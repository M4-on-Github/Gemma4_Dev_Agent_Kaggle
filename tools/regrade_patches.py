#!/usr/bin/env python3
"""EXP-004: re-grade already-collected agent patches with the two missing test-only shims present.

Takes the final patch each agent already submitted for a run (from <run_dir>/patches/*.patch,
not the gold/reference patch) and re-runs grading on it, this time with inline_snapshot and
dirty_equals (tools/compat_shims/*) dropped into /workspace before pytest, gated per-task on
whether the extracted test files actually import them. This isolates how much of a run's
resolved-rate gap is a real fix-quality difference vs. a grading-sandbox artifact: a patch whose
logic was correct but that never reached (or had its vendored shim stripped before) submission.

Runs with sandbox='subprocess' (the same mode the project's actual Kaggle notebooks use, not the
real-docker mode tools/gold_control.py uses) since that is what a Kaggle CPU kernel can access.
Under subprocess sandbox, swegemma's install_editable_package/install_test_dependencies are
no-ops (see container_setup.py), so the ONLY way to make a test-only package importable is to
put it on /workspace, which is already on PYTHONPATH for the pytest subprocess (sandbox/subprocess.py
sets PYTHONPATH=<workspace>). That is exactly the mechanism the agent's own self-vendoring trick
(submission/prompts/swe_coder.md, "Known sandbox gaps") already relies on; this script performs
the same drop at grade time rather than depending on the agent reaching it within its own budget.

No model, no GPU, no agent loop: _run_agent_sandbox is overridden to hand back the stored patch
text directly, so `docker` here is always the subprocess sandbox manager querying a real
(but agent-free) pytest run.

Usage:
    python tools/regrade_patches.py --tasks tasks.jsonl --snapshots snapshots/ --wheels wheels/ \
        --patches-dir runs/E0-dev48-baseline/runs/E0-dev48-baseline/patches --out runs/EXP-004/E0 \
        --label E0
"""
from __future__ import annotations

import argparse
import asyncio
import json
import time
from pathlib import Path

SHIM_ROOT = Path(__file__).resolve().parent / "compat_shims"


def _load_patches(patches_dir: Path) -> dict[str, str]:
    return {f.stem: f.read_text(encoding="utf-8") for f in patches_dir.glob("*.patch")}


_CURRENT_INSTANCE_ID: str | None = None


def _patch_adds_file(patch_text: str, rel_path: str) -> bool:
    """True if patch_text's own diff already creates rel_path (new top-level file), e.g. an
    agent-vendored shim of the same name -- pre-seeding that path too would make extract_snapshot
    drop a file git apply then refuses to recreate ("already exists in working directory"),
    silently turning a correct, already-self-vendoring patch into a hard apply failure."""
    needle_a = f"+++ b/{rel_path}"
    needle_b = f"diff --git a/{rel_path} b/{rel_path}"
    return needle_a in patch_text or needle_b in patch_text


def _install_shim_hook(patches: dict[str, str]) -> None:
    """Monkeypatches verification.extract_snapshot to additionally vendor the two shim
    packages into /workspace right after the snapshot is extracted, one per task and only
    when that task's own extracted test files import the corresponding package -- so a task
    that never needed the shim is graded identically to an unpatched run (no confound from
    an undeclared package being importable everywhere, the exact failure mode already
    documented in experiments/README.md SS1j for an ungated inline_snapshot wheel).

    Skips pre-seeding a given package for a task whose OWN stored patch already adds that same
    file (the agent self-vendored it at run time): that file must come from the patch via
    git apply, not from this script, or the apply collides with a file already sitting in the
    working directory and fails outright (see _patch_adds_file)."""
    from swegemma.harness import verification as _v

    _orig_extract = _v.extract_snapshot

    def _patched_extract(docker, container_id, snapshot_path, *, patch_path=None, base_snapshot_path=None):
        _orig_extract(
            docker, container_id, snapshot_path,
            patch_path=patch_path, base_snapshot_path=base_snapshot_path,
        )
        patch_text = patches.get(_CURRENT_INSTANCE_ID or "", "")
        for pkg in ("inline_snapshot", "dirty_equals"):
            if _patch_adds_file(patch_text, f"{pkg}/__init__.py"):
                continue
            probe = docker.exec(
                container_id,
                f"grep -rlE '(^|[^a-zA-Z0-9_])(import {pkg}\\b|from {pkg}\\b)' /workspace "
                f"--include=*.py 2>/dev/null | head -1",
            )
            if probe.exit_code == 0 and probe.stdout.strip():
                docker.copy_to(container_id, SHIM_ROOT / pkg, "/workspace/")

    _v.extract_snapshot = _patched_extract


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tasks", type=Path, required=True)
    ap.add_argument("--snapshots", type=Path, required=True)
    ap.add_argument("--wheels", type=Path, required=True)
    ap.add_argument("--patches-dir", type=Path, required=True,
                    help="a run's patches/ dir: one <instance_id>.patch file per task")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--label", required=True, help="e.g. E0 or EXP-003, used only in printed output")
    ap.add_argument("--limit", type=int, default=0, help="grade only the first N tasks (0 = all)")
    ap.add_argument("--task-ids", default="", help="comma-separated instance_ids to grade")
    ap.add_argument("--timeout", type=int, default=300, help="per-command timeout seconds")
    ap.add_argument("--resume", action="store_true",
                    help="keep an existing regrade.jsonl and skip tasks already in it")
    args = ap.parse_args()

    from adk_eval_core.tracing import SessionTrace
    from adk_submission import ModelRegistry
    from swegemma.config import EvalConfig
    from swegemma.evaluate import Evaluator
    from swegemma.models import load_tasks

    patches = _load_patches(args.patches_dir)
    if not patches:
        raise SystemExit(f"no *.patch files found under {args.patches_dir}")

    _install_shim_hook(patches)

    tasks = load_tasks(args.tasks)
    if args.task_ids:
        want = {s.strip() for s in args.task_ids.split(",") if s.strip()}
        tasks = [t for t in tasks if t.instance_id in want]
    tasks = [t for t in tasks if t.instance_id in patches]
    missing = set(patches) - {t.instance_id for t in tasks}
    if missing:
        print(f"skipping {len(missing)} patch(es) with no matching task: {sorted(missing)[:5]}")
    tasks = tasks[: args.limit] if args.limit else tasks
    if not tasks:
        raise SystemExit("no tasks to grade: check --tasks, --patches-dir, --limit, --task-ids")

    args.out.mkdir(parents=True, exist_ok=True)
    config = EvalConfig(
        tasks_path=args.tasks,
        snapshots_dir=args.snapshots,
        results_dir=args.out,
        submission_dir=args.out,          # unused: no agent runs
        models=ModelRegistry(),
        sandbox="subprocess",
        wheels_dir=args.wheels,
        timeout_seconds=args.timeout,
        verification_timeout_seconds=args.timeout,
        max_time_minutes=60.0,
        display_mode="quiet",
    )

    class PatchReplayEvaluator(Evaluator):
        """Phase 1 hands back the run's already-submitted patch; no model is called."""

        async def _run_agent_sandbox(self, task, *a, **kw):  # [V] evaluate.py:194 contract
            return patches.get(task.instance_id, ""), None, SessionTrace()

    ev = PatchReplayEvaluator(config)
    out_jsonl = args.out / "regrade.jsonl"
    if not args.resume:
        out_jsonl.unlink(missing_ok=True)

    rows = []
    if args.resume and out_jsonl.exists():
        for line in out_jsonl.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
        done = {r["instance_id"] for r in rows}
        before = len(tasks)
        tasks = [t for t in tasks if t.instance_id not in done]
        print(f"resuming: {len(rows)} already graded, {len(tasks)} of {before} left")

    global _CURRENT_INSTANCE_ID
    for i, t in enumerate(tasks, 1):
        t0 = time.time()
        _CURRENT_INSTANCE_ID = t.instance_id
        r = asyncio.run(ev.evaluate_task(task=t, task_index=i, total_tasks=len(tasks)))
        row = {
            "instance_id": t.instance_id, "repo": t.repo, "resolved": bool(r.resolved),
            "status": getattr(r, "status", None), "exit": r.test_exit_code,
            "seconds": round(time.time() - t0, 1),
            "patch_chars": len(patches.get(t.instance_id, "")),
            "error": (getattr(r, "error", "") or "")[:400],
            "tail": (r.test_output or "")[-6000:],
        }
        rows.append(row)
        with out_jsonl.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row) + "\n")
        print(f"[{args.label} {i}/{len(tasks)}] {t.instance_id:<18} resolved={row['resolved']!s:<5} "
              f"exit={row['exit']} {row['seconds']}s")

    resolved_n = sum(1 for r in rows if r["resolved"])
    print(f"\n{args.label} regrade: {resolved_n}/{len(rows)} resolved "
          f"({resolved_n / len(rows):.1%})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
