"""Teacher sessions (teacher/DESIGN.md, stage 1): act on one task workspace through the harness's own tools.

    tools/tt init   <run> <task_id> [--tree trees/31b-base] [--tools all|a,b,c] [--timeout-seconds N]
    tools/tt call   <run> <task_id> <tool_name> --args '<json object>' --why '<one line>'
    tools/tt finish <run> <task_id>

Everything that touches the workspace is the `swegemma` package's own code, running inside env/harness.sif:
the subprocess sandbox (SubprocessManager), the sandbox preparation steps of harness/agent_runner.py, the
prompt builder (build_agent_prompt), the tool functions (SwegemmaContext.create_tools) called through ADK's
FunctionTool as in an agent run, and the patch extraction of submit_patch. This file only keeps the sandbox
alive between invocations (the harness keeps it in memory for one session) and writes the log.

Layout, under teacher/runs/<run>/<task_id>/:
    swegemma_sandbox_<id>/{workspace,tmp,wheels,venv}   the sandbox root, as SubprocessManager.start() makes it
    workspace -> swegemma_sandbox_<id>/workspace        symlink
    prompt.txt        the initial task message (no reference patch, test patch or hints)
    state.json        sandbox id, tool list, command timeout, counters
    calls.jsonl       one line per call: index, utc, tool, args, why, result, seconds
    submitted.diff    the patch of the last submit_patch call, if any
    patch.diff, finish.json   written by `finish`
and teacher/runs/<run>/cohort.txt: the ids that have a patch.diff (the cohort file for grading).

No call cap and no session time cap: the budget's time_minutes and tool_calls are None, which the harness
treats as unconstrained. The per-command timeout and the output caps are the harness's.

Runs under the image's Python 3.12 through tools/tt; never under the host python3.
"""
import argparse
import asyncio
import fcntl
import hashlib
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "raw"
RUNS = ROOT / "teacher" / "runs"
HARNESS_TOOLS = ("run_command", "read_file", "write_file", "edit_file", "submit_patch", "get_status",
                 "get_code_neighbors", "search_similar_code", "get_code_subgraph")
SANDBOX_KEYS = ("workspace", "tmp", "wheels", "venv")


def utc():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def die(msg):
    print(f"teacher_tool: {msg}", file=sys.stderr)
    sys.exit(2)


def task_dir(run, task_id):
    for part in (run, task_id):
        if not part or "/" in part or part.startswith("."):
            die(f"bad run or task id: {part!r}")
    return RUNS / run / task_id


def load_task(task_id, redact_tests):
    """The task as the tools may hold it: never the reference patch or the hints.

    test_patch is kept in memory (never written or printed) unless redact_tests, because the harness's
    patch extraction strips the files the test patch touches (task.test_files).
    """
    from swegemma.models import Task, load_tasks
    for t in load_tasks(DATA / "tasks.jsonl"):
        if t.instance_id == task_id:
            safe = Task(instance_id=t.instance_id, repo=t.repo, base_commit=t.base_commit,
                        problem_statement=t.problem_statement, patch="",
                        test_patch="" if redact_tests else t.test_patch, hints_text="",
                        created_at=t.created_at)
            return safe, t
    die(f"task id {task_id!r} not in {DATA / 'tasks.jsonl'}")


def read_state(tdir):
    path = tdir / "state.json"
    if not path.exists():
        die(f"{tdir} is not initialised; run: tools/tt init {tdir.parent.name} {tdir.name}")
    return json.loads(path.read_text(encoding="utf-8"))


def write_state(tdir, state):
    tmp = tdir / "state.json.tmp"
    tmp.write_text(json.dumps(state, indent=1), encoding="utf-8")
    tmp.replace(tdir / "state.json")


def attach(tdir, state):
    """A SubprocessManager that points at the sandbox `init` made. It must never be stopped or cleaned up."""
    from swegemma.sandbox import SubprocessManager
    mgr = SubprocessManager(timeout_seconds=state["timeout_seconds"])
    root = tdir / f"swegemma_sandbox_{state['sandbox_id']}"
    paths = {"root": root, **{k: root / k for k in SANDBOX_KEYS}}
    missing = [str(p) for p in paths.values() if not p.exists()]
    if missing:
        die(f"sandbox incomplete, missing {missing}")
    mgr._sandboxes[state["sandbox_id"]] = paths
    mgr._default_sandbox_id = state["sandbox_id"]
    return mgr


def make_context(tdir, state, task):
    """The context the harness builds in run_agent_sandbox, with an unconstrained session budget."""
    from swegemma.budget import EvaluationBudget, HarnessLimits
    from swegemma.context import SwegemmaContext
    ctx = SwegemmaContext(
        docker_manager=attach(tdir, state), container_id=state["sandbox_id"],
        problem_statement=task.problem_statement, hints_text="", task=task, repo=task.repo,
        graph_dir=str(DATA / "graphs"), embeddings_dir=str(DATA / "embeddings"),
        budget=EvaluationBudget(time_minutes=None, tool_calls=None),
        harness=HarnessLimits(command_timeout_seconds=state["timeout_seconds"]))
    ctx.tool_calls_used = int(state.get("tool_calls_used", 0))
    submitted = tdir / "submitted.diff"
    if submitted.exists():
        ctx.submitted_patch = submitted.read_text(encoding="utf-8")
        ctx.patch_submitted = True
    return ctx


def tree_settings(tree, tools_arg, timeout_arg):
    """Tool list and command timeout: from the agent tree the teacher mirrors, unless given."""
    import yaml
    tree = (ROOT / tree).resolve() if not Path(tree).is_absolute() else Path(tree)
    if tools_arg == "all":
        tools = list(HARNESS_TOOLS)
    elif tools_arg:
        tools = [t.strip() for t in tools_arg.split(",") if t.strip()]
    else:
        class Loader(yaml.SafeLoader):
            pass
        Loader.add_constructor("!include", lambda loader, node: None)
        agent = yaml.load((tree / "agent.yaml").read_text(encoding="utf-8"), Loader=Loader) or {}
        tools = [t for t in (agent.get("tools") or []) if isinstance(t, str)]
    unknown = [t for t in tools if t not in HARNESS_TOOLS]
    if unknown or not tools:
        die(f"tools {unknown or tools} are not harness tools; choose from {', '.join(HARNESS_TOOLS)}")
    if timeout_arg is not None:
        timeout = timeout_arg
    else:
        ev = (yaml.safe_load((tree / "eval_config.yaml").read_text(encoding="utf-8")) or {}).get("evaluation", {})
        timeout = int(ev.get("timeout_seconds", 300))
    return tree, tools, int(timeout)


def cmd_init(a):
    tdir = task_dir(a.run, a.task_id)
    if (tdir / "state.json").exists():
        die(f"{tdir} already initialised; a session is never overwritten (use a new run name)")
    tree, tools, timeout = tree_settings(a.tree, a.tools, a.timeout_seconds)
    task, full = load_task(a.task_id, redact_tests=True)

    from adk_submission import ModelRegistry
    from swegemma.budget import EvaluationBudget
    from swegemma.config import EvalConfig
    from swegemma.deduplication import resolve_task_snapshot_paths
    from swegemma.harness import agent_runner as ar
    from swegemma.sandbox import SubprocessManager

    tdir.mkdir(parents=True, exist_ok=True)
    config = EvalConfig(
        tasks_path=DATA / "tasks.jsonl", snapshots_dir=DATA / "snapshots", results_dir=tdir / "official",
        submission_dir=tree, models=ModelRegistry(), sandbox="subprocess", timeout_seconds=timeout,
        budget=EvaluationBudget(time_minutes=None, tool_calls=None),
        graph_dir=str(DATA / "graphs"), embeddings_dir=str(DATA / "embeddings"), wheels_dir=DATA / "wheels")
    snapshot, base_snapshot, patch_path = resolve_task_snapshot_paths(config.snapshots_dir, task.instance_id, task.repo)
    if not snapshot.exists():
        die(f"snapshot not found: {snapshot}")

    # The sandbox preparation of run_agent_sandbox, step for step, on a sandbox that outlives this process.
    t0 = time.time()
    mgr = SubprocessManager(timeout_seconds=timeout, base_dir=tdir)
    sid = mgr.start()
    ar.setup_container_wheels(mgr, sid, config)
    ar.extract_snapshot(mgr, sid, snapshot, patch_path=patch_path, base_snapshot_path=base_snapshot)
    ar.setup_git_exclude(mgr, sid)
    ar.install_editable_package(mgr, sid)
    ar.install_test_dependencies(mgr, sid, task.repo, config=config)
    ar.setup_workspace_test_config(mgr, sid, repo=task.repo)
    ar.setup_baseline_commit(mgr, sid, "baseline")
    tree_res = mgr.exec(sid, ar.build_workspace_tree_command())
    workspace_tree = tree_res.stdout.strip() if tree_res.exit_code == 0 else ""
    baseline = mgr.exec(sid, "cd /workspace && git rev-parse _swegemma_baseline").stdout.strip()
    head = mgr.exec(sid, "cd /workspace && git rev-parse HEAD").stdout.strip()

    prompt = ar.build_agent_prompt(task=task, config=config, workspace_tree=workspace_tree,
                                   enable_sandbox_testing=True, declared_tools=tools)
    for name, secret in (("patch", full.patch), ("test_patch", full.test_patch), ("hints_text", full.hints_text)):
        if secret and secret.strip() and secret.strip() in prompt:
            die(f"the prompt contains the task's {name}; nothing written")
    (tdir / "prompt.txt").write_text(prompt, encoding="utf-8")
    link = tdir / "workspace"
    if not link.is_symlink():
        link.symlink_to(f"swegemma_sandbox_{sid}/workspace")
    state = {"run": a.run, "task_id": a.task_id, "repo": task.repo, "base_commit": task.base_commit,
             "sandbox_id": sid, "tree": str(tree), "tools": tools, "timeout_seconds": timeout,
             "baseline_tag": baseline, "head": head, "created_utc": utc(), "calls": 0, "tool_calls_used": 0}
    write_state(tdir, state)
    print(json.dumps({"status": "ok", "task_dir": str(tdir), "prompt": str(tdir / "prompt.txt"),
                      "prompt_chars": len(prompt), "tools": tools, "timeout_seconds": timeout,
                      "baseline_tag": baseline or None, "setup_seconds": round(time.time() - t0, 1)}, indent=1))
    if not baseline:
        print("teacher_tool: WARNING no _swegemma_baseline tag; the patch will be a diff against HEAD",
              file=sys.stderr)
    return 0


def run_tool(ctx, state, name, args):
    """One tool call as the ADK flow makes it: lookup, FunctionTool argument handling, ToolErrorPlugin on errors."""
    from google.adk.flows.llm_flows.functions import _get_tool
    from google.adk.tools.function_tool import FunctionTool
    from google.genai import types
    registry = ctx.create_tools()
    tools = {n: FunctionTool(registry[n]) for n in state["tools"]}  # the tree's order, as the agent has it
    try:
        tool = _get_tool(types.FunctionCall(name=name, args=args), tools)
        return asyncio.run(tool.run_async(args=dict(args), tool_context=None))
    except Exception as exc:  # noqa: BLE001  (ToolErrorPlugin.on_tool_error_callback)
        return {"status": "error", "error_type": type(exc).__name__, "error": str(exc)}


def cmd_call(a):
    tdir = task_dir(a.run, a.task_id)
    state = read_state(tdir)
    if (tdir / "patch.diff").exists():
        die(f"{tdir} is finished; no further calls")
    raw = a.args
    if a.args_file:
        raw = sys.stdin.read() if a.args_file == "-" else Path(a.args_file).read_text(encoding="utf-8")
    try:
        args = json.loads(raw)
    except ValueError as exc:
        die(f"--args is not JSON: {exc}")
    if not isinstance(args, dict):
        die("--args must be a JSON object, e.g. '{\"command\": \"ls\"}'")
    why = " ".join((a.why or "").split())
    if not why:
        die("--why is required: one line saying why this call is made")

    task, _ = load_task(a.task_id, redact_tests=False)
    with open(tdir / "calls.lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = read_state(tdir)
        ctx = make_context(tdir, state, task)
        started, t0 = utc(), time.time()
        result = run_tool(ctx, state, a.tool_name, args)
        seconds = round(time.time() - t0, 3)
        out = json.dumps(result, ensure_ascii=False)
        state["calls"] = int(state.get("calls", 0)) + 1
        state["tool_calls_used"] = ctx.tool_calls_used
        row = {"index": state["calls"], "utc": started, "tool": a.tool_name, "args": args, "why": why,
               "result": result, "seconds": seconds}
        with open(tdir / "calls.jsonl", "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        if a.tool_name == "submit_patch" and ctx.patch_submitted:
            (tdir / "submitted.diff").write_text(ctx.submitted_patch or "", encoding="utf-8")
        write_state(tdir, state)
    print(out)
    return 0


def cmd_finish(a):
    tdir = task_dir(a.run, a.task_id)
    state = read_state(tdir)
    task, _ = load_task(a.task_id, redact_tests=False)
    from swegemma.tools.execution import submit_patch
    ctx = make_context(tdir, state, task)
    earlier = ctx.submitted_patch if ctx.patch_submitted else None
    # The harness's own extraction: `git add -N .`, `git diff --binary _swegemma_baseline` (HEAD if the tag
    # is missing), then strip_protected_files_from_patch with the test patch's files. Not logged as a call.
    res = json.loads(submit_patch(ctx))
    if res.get("status") != "ok":
        die(f"patch extraction failed: {res}")
    patch = ctx.submitted_patch or ""
    (tdir / "patch.diff").write_text(patch, encoding="utf-8")
    by_tool = {}
    calls = tdir / "calls.jsonl"
    for line in (calls.read_text(encoding="utf-8").splitlines() if calls.exists() else []):
        tool = json.loads(line)["tool"]
        by_tool[tool] = by_tool.get(tool, 0) + 1
    info = {"status": "ok", "run": a.run, "task_id": a.task_id, "patch": str(tdir / "patch.diff"),
            "patch_chars": len(patch), "patch_sha256": hashlib.sha256(patch.encode("utf-8")).hexdigest(),
            "files_changed": patch.count("diff --git"), "calls": sum(by_tool.values()), "calls_by_tool": by_tool,
            "tool_calls_counted_by_harness": state.get("tool_calls_used", 0),
            "submit_patch_called": earlier is not None,
            # The harness grades the last submitted patch; edits made after it would be lost there.
            "last_submitted_patch_equals_final": (earlier == patch) if earlier is not None else None,
            "finished_utc": utc()}
    (tdir / "finish.json").write_text(json.dumps(info, indent=1), encoding="utf-8")
    ids = sorted(p.parent.name for p in tdir.parent.glob("*/patch.diff"))
    tmp = tdir.parent / f"cohort.txt.{os.getpid()}"
    tmp.write_text("\n".join(ids) + "\n", encoding="utf-8")
    tmp.replace(tdir.parent / "cohort.txt")
    print(json.dumps(info, indent=1))
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("init", help="extract the snapshot, prepare the sandbox, write prompt.txt")
    s.add_argument("run")
    s.add_argument("task_id")
    s.add_argument("--tree", default="trees/31b-base",
                   help="agent tree whose tool list and command timeout the session mirrors")
    s.add_argument("--tools", default=None, help="'all' (the nine harness tools) or a comma list; default: the tree's")
    s.add_argument("--timeout-seconds", type=int, default=None, help="per-command timeout; default: the tree's")
    s.set_defaults(fn=cmd_init)
    s = sub.add_parser("call", help="run one harness tool on the workspace and log it")
    s.add_argument("run")
    s.add_argument("task_id")
    s.add_argument("tool_name")
    s.add_argument("--args", default="{}", help="the tool's arguments, a JSON object")
    s.add_argument("--args-file", default=None, help="read the JSON arguments from this file ('-' = stdin)")
    s.add_argument("--why", required=True, help="one line: why this call")
    s.set_defaults(fn=cmd_call)
    s = sub.add_parser("finish", help="write patch.diff, extracted as the harness extracts the agent's patch")
    s.add_argument("run")
    s.add_argument("task_id")
    s.set_defaults(fn=cmd_finish)
    a = p.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
