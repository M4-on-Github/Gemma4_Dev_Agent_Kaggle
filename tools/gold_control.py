#!/usr/bin/env python3
"""EXP-000 gold control (Q5): grade each task with its own reference patch, no model involved.

Any task that fails here is unsolvable by construction and must be excluded from every cohort,
or it silently caps our ceiling and adds noise to every A/B comparison.

Runs inside the orchestrator container (see tools/docker/Dockerfile.orchestrator) and uses the
REAL `docker` sandbox. This cannot run on Kaggle: swegemma's `subprocess` sandbox returns early
from install_editable_package/install_test_dependencies, so per-task dependencies are never
installed and every task fails identically on a version mismatch rather than on its own merits.

Usage (from the repo root, via tools/run_gold_control.sh):
    python tools/gold_control.py --tasks /data/tasks.jsonl --snapshots /data/snapshots \
        --wheels /data/wheels --out /work/runs/EXP-000 [--limit 8] [--task-ids a,b]
"""
from __future__ import annotations

import argparse
import asyncio
import json
import shutil
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from curate_wheels import curate



def _clear_sitepackages_tar_cache() -> None:
    """Drops the harness's unpacked-wheels tar cache, which is keyed by a constant.

    container_setup._build_unpacked_wheels_tar caches to
    `{tempdir}/swegemma_sp_cache_v8/{cache_name}.tar` and returns early whenever that file exists,
    but the base set is always built under the literal cache_name 'sp_base'. The tar is therefore
    built once from whichever pool the *first* task used and then reused for every later task,
    regardless of that task's own wheels_dir -- and it outlives the process, so a second run
    inherits it too.

    Official grading never notices, because there every task shares one pool and the cached tar is
    the correct one. It matters here only because we vary the pool per task (tools/curate_wheels.py),
    where it silently gave each task its predecessor's dependencies: fastapi_13920 passes alone but
    failed with `ModuleNotFoundError: typing_inspection` when a requests task ran before it.
    """
    cache = Path(tempfile.gettempdir()) / "swegemma_sp_cache_v8"
    shutil.rmtree(cache, ignore_errors=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tasks", type=Path, required=True)
    ap.add_argument("--snapshots", type=Path, required=True)
    ap.add_argument("--wheels", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--image", default="swebench-sandbox:latest")
    ap.add_argument("--limit", type=int, default=0, help="grade only the first N tasks (0 = all)")
    ap.add_argument("--task-ids", default="", help="comma-separated instance_ids to grade")
    ap.add_argument("--timeout", type=int, default=600, help="per-command timeout seconds")
    ap.add_argument("--resume", action="store_true",
                    help="keep an existing gold_control.jsonl and skip the tasks already in it. "
                         "A full 129-task sweep runs ~1h; without this a crash at task 120 "
                         "discards everything, since the log is truncated at startup.")
    ap.add_argument("--negative-control", action="store_true",
                    help="hand back an EMPTY patch instead of the reference one. Validity check: if "
                         "tasks still 'resolve', grading is a no-op and a gold pass means nothing")
    ap.add_argument("--supplemental-wheels", type=Path, default=None,
                    help="dir of wheels fetched from PyPI to fill gaps in the official pool. These "
                         "are gated on being declared by the task, since an undeclared pytest "
                         "plugin auto-loads and can break an unrelated repo")
    ap.add_argument("--pin", action="append", default=[], metavar="NAME==VERSION",
                    help="override a declared range with an empirically known-good one, e.g. "
                         "--pin pygments==2.20.0 (repeatable). Needed for tasks whose own pins "
                         "are too loose to reproduce their snapshots.")
    ap.add_argument("--curate-wheels", action="store_true",
                    help="per task, hide the wheel versions the repo's pins forbid, so the harness's "
                         "highest-version-wins injection lands on a compatible env "
                         "(see tools/curate_wheels.py)")
    args = ap.parse_args()

    from adk_eval_core.tracing import SessionTrace
    from adk_submission import ModelRegistry
    from swegemma.config import EvalConfig
    from swegemma.evaluate import Evaluator
    from swegemma.models import load_tasks

    tasks = load_tasks(args.tasks)
    if args.task_ids:
        want = {s.strip() for s in args.task_ids.split(",") if s.strip()}
        tasks = [t for t in tasks if t.instance_id in want]
    # Only grade tasks whose snapshot is actually present. A missing snapshot returns
    # resolved=False with 'Snapshot file not found', which is indistinguishable from a
    # genuinely broken task and would corrupt the Q5 answer.
    present, absent = [], []
    for t in tasks:
        if any((args.snapshots / f"{t.instance_id}{ext}").exists() for ext in (".tgz", ".tar.gz")):
            present.append(t)
        else:
            absent.append(t.instance_id)
    if absent:
        print(f"skipping {len(absent)} task(s) with no local snapshot: {absent[:5]}"
              f"{'...' if len(absent) > 5 else ''}")
    tasks = present[: args.limit] if args.limit else present
    if not tasks:
        raise SystemExit("no tasks to grade: check --snapshots, --limit and --task-ids")

    args.out.mkdir(parents=True, exist_ok=True)
    config = EvalConfig(
        tasks_path=args.tasks,
        snapshots_dir=args.snapshots,
        results_dir=args.out,
        submission_dir=args.out,          # unused: no agent runs
        models=ModelRegistry(),
        image=args.image,
        sandbox="docker",
        wheels_dir=args.wheels,
        timeout_seconds=args.timeout,
        verification_timeout_seconds=args.timeout,
        max_time_minutes=60.0,
        display_mode="quiet",
    )

    class GoldEvaluator(Evaluator):
        """Phase 1 hands back the reference patch; no model is called, nothing is shown to an agent."""

        async def _run_agent_sandbox(self, task, *a, **kw):  # [V] evaluate.py:194 contract
            return ("" if args.negative_control else task.patch), None, SessionTrace()


    ev = GoldEvaluator(config)
    out_jsonl = args.out / "gold_control.jsonl"
    if not args.resume:
        out_jsonl.unlink(missing_ok=True)
    supplemental: set[str] = set()
    if args.supplemental_wheels and args.supplemental_wheels.is_dir():
        supplemental = {
            f.name.split("-", 1)[0]
            for f in args.supplemental_wheels.iterdir() if f.name.endswith(".whl")
        }
        print(f"supplemental (gated on declaration): {len(supplemental)} pkgs")

    overrides: dict[str, str] = {}
    for raw in args.pin:
        name, sep, spec = raw.partition("==")
        if not sep:
            ap.error(f"--pin expects NAME==VERSION, got {raw!r}")
        overrides[name.strip()] = f"=={spec.strip()}"
    if overrides:
        print(f"pins: {', '.join(f'{k}{v}' for k, v in sorted(overrides.items()))}")

    rows = []
    if args.resume and out_jsonl.exists():
        for line in out_jsonl.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
        done = {r["instance_id"] for r in rows}
        before = len(tasks)
        tasks = [t for t in tasks if t.instance_id not in done]
        print(f"resuming: {len(rows)} already graded, {len(tasks)} of {before} left")

    for i, t in enumerate(tasks, 1):
        t0 = time.time()
        curation = None
        if args.curate_wheels:
            _clear_sitepackages_tar_cache()
            # Point the harness at a per-task pool before it builds the container. Selection is
            # "highest version per name" (container_setup._deduplicate_wheels), so narrowing the
            # pool is what actually decides the test environment.
            snap = next(
                (args.snapshots / f"{t.instance_id}{ext}"
                 for ext in (".tgz", ".tar.gz")
                 if (args.snapshots / f"{t.instance_id}{ext}").exists()),
                None,
            )
            if snap is not None:
                pool = args.out / "wheelpools" / t.instance_id
                curation = curate(args.wheels, snap, pool,
                                  repo=t.repo, instance_id=t.instance_id,
                                  supplemental=supplemental,
                                  extra_pool=args.supplemental_wheels,
                                  overrides=overrides)
                config.wheels_dir = pool
                ev.config.wheels_dir = pool
                print(f"    curated {curation['kept']} pkgs "
                      f"(-{len(curation['dropped_undeclared'])} undeclared, "
                      f"-{curation['under_test']} under test), "
                      f"narrowed {len(curation['narrowed'])}: "
                      f"{'; '.join(curation['narrowed'][:3]) or 'none'}")
        r = asyncio.run(ev.evaluate_task(task=t, task_index=i, total_tasks=len(tasks)))
        row = {
            "instance_id": t.instance_id, "repo": t.repo, "resolved": bool(r.resolved),
            "status": getattr(r, "status", None), "exit": r.test_exit_code,
            "seconds": round(time.time() - t0, 1),
            "gold_patch_chars": len(t.patch or ""), "test_patch_chars": len(t.test_patch or ""),
            "error": (getattr(r, "error", "") or "")[:400],
            "curation": curation,
            "tail": (r.test_output or "")[-6000:],
            "head": (r.test_output or "")[:6000],
        }
        rows.append(row)
        with out_jsonl.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row) + "\n")
        print(f"[{i}/{len(tasks)}] {t.instance_id:<18} resolved={row['resolved']!s:<5} "
              f"exit={row['exit']} {row['seconds']}s")

    failures = [r["instance_id"] for r in rows if not r["resolved"]]
    (args.out / "gold_failures.txt").write_text(
        "# gold-control failures (exclude from cohorts)\n" + "\n".join(failures) + "\n",
        encoding="utf-8")
    print(f"\ngold control: {len(rows) - len(failures)}/{len(rows)} sound")
    if failures:
        print("failures:", failures)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
