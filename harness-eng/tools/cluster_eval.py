"""Run one draw of one agent tree on a list of tasks, on one GPU of the cluster.

A port of the agent path of notebooks/kaggle_eval_l4x4.py (the organizers' Getting-Started recipe:
VllmServer, swegemma Evaluator, subprocess sandbox). It writes the same run layout a Kaggle kernel
does, so tools/analyze_traces.py and tools/run_forensics.py read it unchanged:

    <out>/task_results.jsonl   one row per task
    <out>/traces/trace_<id>.json
    <out>/patches/<id>.patch
    <out>/summary.json         run settings, decode probe, hardware, hashes

Differences from the kernel, all recorded in summary.json:
  - one GPU, tensor_parallel_size 1 (the scorer and the kernels use 4 x L4, TP 4);
  - --concurrency N runs N tasks at once (the scorer and the kernels run one at a time);
  - the wheelhouse is already installed in the image;
  - paths come from arguments; no gold control and no phase-0 checks.

Runs inside env/harness.sif. Started by slurm/eval.sbatch.
"""
import argparse
import asyncio
import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

ALLOWED_MODELS = ("gemma-4-31b-it-qat-w4a16-ct", "gemma-4-e4b-it-qat-w4a16-ct", "gemma-4-e2b-it-qat-w4a16-ct")
PREFIXES = ("openai/", "google/", "hosted_vllm/", "custom/")
# HARNESS_README section 7.2, as in the kernel.
COMPACTION_INTERVAL, COMPACTION_TOKEN_THRESHOLD = 15, 14336


def parse_args():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--tree", required=True, type=Path, help="agent config: a directory or a packed zip")
    p.add_argument("--cohort", required=True, type=Path, help="text file of task ids, one per line, # comments")
    p.add_argument("--out", required=True, type=Path, help="run directory; must not already hold results")
    p.add_argument("--data", required=True, type=Path, help="competition data dir (tasks.jsonl, snapshots/, ...)")
    p.add_argument("--models", required=True, type=Path, help="dir holding one folder per served checkpoint")
    p.add_argument("--time-scale", type=float, default=1.0,
                   help="multiply the tree's max_time_minutes by this (the model sees the scaled budget)")
    p.add_argument("--limit", type=int, default=0, help="run only the first N ids of the cohort (0 = all)")
    p.add_argument("--concurrency", type=int, default=1,
                   help="tasks run at once against the one server (the kernels and the scorer run 1)")
    p.add_argument("--control", choices=("gold", "empty", "patchdir"), default=None,
                   help="no model and no GPU: grade each task's reference patch (gold), an empty patch, "
                        "or <patch-dir>/<task id>/patch.diff (patchdir)")
    p.add_argument("--patch-dir", type=Path, default=None, help="with --control patchdir: one folder per task id")
    p.add_argument("--port", type=int, default=0, help="vLLM port (0 = pick a free one)")
    p.add_argument("--py313", type=Path, default=None,
                   help="sandbox venvs from this interpreter (env/py313-scorer/bin/python3.13, a copy of the "
                        "public scorer's Python) instead of the image's; see tools/scorer_env.py")
    p.add_argument("--extras", type=Path, default=None,
                   help="with --py313: a directory of packages the public scorer lacks, added to every venv")
    p.add_argument("--task-envs", type=Path, default=None,
                   help="with --py313: env/taskenvs; each task's venv gets <dir>/<id> (the repo's declared test "
                        "deps, tools/build_task_envs.py) ahead of site-packages. Not scorer-faithful")
    return p.parse_args()


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def tree_hash(root):
    """sha256 over the relative paths and bytes of every file in an unpacked tree."""
    h = hashlib.sha256()
    for f in sorted(p for p in root.rglob("*") if p.is_file()):
        h.update(f.relative_to(root).as_posix().encode() + b"\0" + f.read_bytes() + b"\0")
    return h.hexdigest()


def read_cohort(path, limit):
    ids = [ln.split("#")[0].strip() for ln in path.read_text().splitlines()]
    ids = [i for i in ids if i]
    assert len(ids) == len(set(ids)), f"duplicate ids in {path}"
    return ids[:limit] if limit else ids


def gpu_info():
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
                             capture_output=True, text=True, timeout=30).stdout.strip().splitlines()
    except Exception as exc:  # noqa: BLE001
        out = [f"nvidia-smi failed: {exc}"]
    return out


def decode_probe(base_url, model_id, streams=1):
    """Decode speed per stream with `streams` requests in flight, the load a run at that concurrency puts on the server."""
    body = json.dumps({"model": model_id, "max_tokens": 400, "temperature": 0.0,
                       "messages": [{"role": "user", "content": "Count from 1 to 400 separated by spaces."}],
                       "chat_template_kwargs": {"enable_thinking": False}}).encode()

    def one(_):
        req = urllib.request.Request(base_url.rstrip("/") + "/chat/completions", data=body,
                                     headers={"Content-Type": "application/json"}, method="POST")
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=600) as resp:
            out = json.loads(resp.read())
        dt = time.time() - t0
        return out.get("usage", {}).get("completion_tokens", 0), dt

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(streams) as ex:
        res = list(ex.map(one, range(streams)))
    per = [round(n / dt, 1) for n, dt in res if dt]
    return {"streams": streams, "completion_tokens": res[0][0], "seconds": round(max(dt for _, dt in res), 2),
            "tok_s": round(sum(per) / len(per), 1) if per else None, "tok_s_per_stream": per}


def main():
    a = parse_args()
    out = a.out.resolve()
    assert not (out / "task_results.jsonl").exists(), f"{out} already holds a run; a draw is never overwritten"
    for sub in ("traces", "patches", "logs"):
        (out / sub).mkdir(parents=True, exist_ok=True)

    # ---- the agent tree
    agent_dir = out / "agent"
    shutil.rmtree(agent_dir, ignore_errors=True)
    if a.tree.is_dir():
        shutil.copytree(a.tree, agent_dir)
        source = {"tree": str(a.tree), "zip_sha256": None}
    else:
        agent_dir.mkdir(parents=True)
        zipfile.ZipFile(a.tree).extractall(agent_dir)
        source = {"tree": str(a.tree), "zip_sha256": sha256_file(a.tree)}
    source["tree_sha256"] = tree_hash(agent_dir)

    import yaml
    eval_path = agent_dir / "eval_config.yaml"
    EVAL = (yaml.safe_load(eval_path.read_text()) or {}).get("evaluation", {}) if eval_path.exists() else {}
    shipped_minutes = float(EVAL.get("max_time_minutes", 60.0))
    run_minutes = round(shipped_minutes * a.time_scale, 3)

    # ---- harness imports (after the cheap checks, so a bad argument fails in seconds)
    import litellm
    import torch
    from adk_submission import (ModelRegistry, VllmConfig, VllmServer, discover_adapters,
                                discover_declared_models)
    from google.adk.agents.context_cache_config import ContextCacheConfig
    from google.adk.apps._configs import EventsCompactionConfig
    from google.adk.models.lite_llm import LiteLlm
    from swegemma.config import ALLOWED_ADAPTER_EXTENSIONS, EvalConfig, build_submission_limits
    from swegemma.evaluate import Evaluator
    from swegemma.models import load_tasks
    test_env = {"py313": None}
    if a.py313:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import scorer_env
        test_env = scorer_env.install(a.py313, a.extras, a.task_envs)
        print("sandbox test env:", test_env, flush=True)
    else:
        assert not (a.extras or a.task_envs), "--extras and --task-envs need --py313"

    tasks_path = a.data / "tasks.jsonl"
    by_id = {t.instance_id: t for t in load_tasks(tasks_path)}
    ids = read_cohort(a.cohort, a.limit)
    unknown = [i for i in ids if i not in by_id]
    assert not unknown, f"cohort ids not in tasks.jsonl: {unknown[:5]}"
    tasks = [by_id[i] for i in ids]

    declared = discover_declared_models(str(agent_dir))
    assert len(declared) == 1, f"the tree must declare exactly one model, got {sorted(declared)}"
    alias = next(iter(declared))
    target = alias.strip()
    for pre in PREFIXES:
        if target.startswith(pre):
            target = target[len(pre):]
            break
    assert target in ALLOWED_MODELS, f"declared model {target!r} not in {ALLOWED_MODELS}"
    model_dir = a.models / target
    assert (model_dir / "config.json").exists(), f"{model_dir}/config.json missing"
    adapters = discover_adapters(str(agent_dir), adapter_extensions=ALLOWED_ADAPTER_EXTENSIONS)

    server, server_start_s = None, None
    if a.control:
        EVAL = {**EVAL, "timeout_seconds": 300, "max_time_minutes": 60.0, "max_tool_calls": 100}
        run_minutes = 60.0
    # ---- vLLM, the kernel's settings except the GPU count
    if not a.control:
      try:
        from adk_submission.resolvers.generation import install_litellm_reasoning_patch
        install_litellm_reasoning_patch()
      except Exception as exc:  # noqa: BLE001
        print("reasoning patch not installed:", exc)
      litellm.drop_params = True
      n_gpu = torch.cuda.device_count() if torch.cuda.is_available() else 0
      assert n_gpu == 1, f"expected exactly one visible GPU, saw {n_gpu}"
      port = a.port or free_port()
      t0 = time.time()
      server = VllmServer(VllmConfig(
        model=str(model_dir), port=port, host="127.0.0.1", tool_call_parser="gemma4", reasoning_parser="gemma4",
        default_chat_template_kwargs={"enable_thinking": True}, max_model_len=32768,
        dtype="bfloat16" if torch.cuda.is_bf16_supported() else "auto", gpu_memory_utilization=0.90,
        enable_auto_tool_choice=True, enable_lora=True, max_loras=8, max_lora_rank=128,
        tensor_parallel_size=1, startup_timeout=60 * 20), adapter_manifest=adapters)
      server.start()
      server_start_s = round(time.time() - t0, 1)
      print(f"vLLM up in {server_start_s}s (tp=1) at {server.base_url}", flush=True)

    summary = {"run": out.name, "source": source, "model": target, "cohort": str(a.cohort), "n_tasks": len(tasks),
               "eval_config_shipped": EVAL, "time_scale": a.time_scale, "concurrency": a.concurrency, "max_time_minutes_run": run_minutes,
               "compaction": {"interval": COMPACTION_INTERVAL, "token_threshold": COMPACTION_TOKEN_THRESHOLD},
               "hardware": {"host": socket.gethostname(), "gpus": [] if a.control else gpu_info(), "tensor_parallel_size": 1},
               "slurm_job": os.environ.get("SLURM_JOB_ID"), "server_start_s": server_start_s,
               "sandbox_test_env": test_env,
               "task_env_used": (sys.modules["scorer_env"].TASK_ENV_USE if a.py313 and a.task_envs else None),
               "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "tasks": [], "resolved": 0}
    try:
        models = ModelRegistry()
        summary["control"] = a.control
        if a.control == "patchdir":
            assert a.patch_dir and a.patch_dir.is_dir(), "--control patchdir needs --patch-dir <dir>"
            summary["patch_dir"] = str(a.patch_dir.resolve())
        if a.control:
            from adk_eval_core.tracing import SessionTrace

            class ControlEvaluator(Evaluator):
                """No model call: the 'agent patch' is the task's reference patch, or nothing."""
                async def _run_agent_sandbox(self, task, *args, **kwargs):
                    if a.control == "patchdir":  # a missing patch.diff raises: recorded as a task exception
                        return (a.patch_dir / task.instance_id / "patch.diff").read_text(encoding="utf-8"), None, SessionTrace()
                    return (task.patch if a.control == "gold" else ""), None, SessionTrace()
            evaluator_cls = ControlEvaluator
        else:
            evaluator_cls = Evaluator
            target_id = getattr(server, "effective_model_path", str(model_dir))
            for name in {alias, target}:
                models.register(name, LiteLlm(model=f"openai/{target_id}", api_base=server.base_url, api_key="EMPTY"))
            summary["decode_probe"] = decode_probe(server.base_url, target_id)
            if a.concurrency > 1:
                summary["decode_probe_loaded"] = decode_probe(server.base_url, target_id, a.concurrency)
                print("decode probe at run concurrency:", summary["decode_probe_loaded"], flush=True)
            print("decode probe:", summary["decode_probe"], flush=True)

        limits, gen = build_submission_limits()
        ev = evaluator_cls(EvalConfig(
            tasks_path=tasks_path, snapshots_dir=a.data / "snapshots", results_dir=out / "official",
            submission_dir=agent_dir, models=models, sandbox="subprocess",
            timeout_seconds=int(EVAL.get("timeout_seconds", 300)), max_time_minutes=run_minutes,
            max_tool_calls=int(EVAL.get("max_tool_calls", 100)),
            max_turns=int(EVAL["max_turns"]) if EVAL.get("max_turns") is not None else None,
            limits=limits, generation_constraints=gen, adapter_manifest=adapters,
            context_cache_config=ContextCacheConfig(min_tokens=2048, ttl_seconds=1800, cache_intervals=10),
            events_compaction_config=EventsCompactionConfig(
                compaction_interval=COMPACTION_INTERVAL, overlap_size=2,
                token_threshold=COMPACTION_TOKEN_THRESHOLD, event_retention_size=5),
            graph_dir=str(a.data / "graphs"), embeddings_dir=str(a.data / "embeddings"),
            wheels_dir=a.data / "wheels", verbose=False))

        async def one(i, t, sem):
            async with sem:
                t_start = time.time()
                r = await ev.evaluate_task(task=t, task_index=i, total_tasks=len(tasks))
                wall = time.time() - t_start
            patch = r.agent_patch or ""
            dur = float(r.duration_seconds or 0)
            row = {"instance_id": t.instance_id, "repo": t.repo, "resolved": bool(r.resolved),
                   "status": getattr(r, "status", None), "test_exit_code": r.test_exit_code,
                   "duration_s": round(dur, 1), "task_wall_s": round(wall, 1), "setup_s": round(max(0.0, wall - dur), 1),
                   "tool_calls": getattr(r, "tool_calls", None), "llm_calls": getattr(r, "total_llm_calls", None),
                   "total_tokens": getattr(r, "total_tokens", None),
                   "error": getattr(r, "error", None) or getattr(r, "error_message", None),
                   "patch_chars": len(patch), "patch": patch,
                   "trace": str(getattr(r, "trace_path", "") or getattr(r, "trace_json_path", "") or ""),
                   "test_tail": (r.test_output or "")[-1500:], "max_time_minutes": run_minutes,
                   "max_tool_calls": EVAL.get("max_tool_calls"), "concurrency": a.concurrency}
            # No await between here and the end of the function, so rows never interleave.
            with (out / "task_results.jsonl").open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(row) + "\n")
            (out / "patches" / f"{t.instance_id}.patch").write_text(patch)
            for cand in (Path(row["trace"]) if row["trace"] else None,
                         out / "official" / "traces" / f"trace_{t.instance_id}.json"):
                if cand and cand.exists():
                    shutil.copy(cand, out / "traces" / f"trace_{t.instance_id}.json")
                    break
            summary["tasks"].append(t.instance_id)
            summary["resolved"] += int(row["resolved"])
            print(f"[{len(summary['tasks'])}/{len(tasks)}] {t.instance_id} resolved={row['resolved']} "
                  f"calls={row['tool_calls']} agent={row['duration_s']}s setup={row['setup_s']}s "
                  f"err={(row['error'] or '')[:100]}", flush=True)

        async def run_all():
            sem = asyncio.Semaphore(a.concurrency)
            results = await asyncio.gather(*(one(i, t, sem) for i, t in enumerate(tasks, 1)), return_exceptions=True)
            return [f"{t.instance_id}: {r!r}" for t, r in zip(tasks, results) if isinstance(r, BaseException)]

        t_run = time.time()
        summary["task_exceptions"] = asyncio.run(run_all())
        summary["tasks_wall_s"] = round(time.time() - t_run, 1)
        for line in summary["task_exceptions"]:
            print("TASK EXCEPTION", line[:300], flush=True)
        print(f"RESOLVED {summary['resolved']}/{len(summary['tasks'])}")
    finally:
        summary["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        (out / "summary.json").write_text(json.dumps(summary, indent=1))
        logs = out / "official" / "logs"
        if logs.exists():
            shutil.copytree(logs, out / "logs", dirs_exist_ok=True)
        try:
            server.stop()
        except Exception:  # noqa: BLE001
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
