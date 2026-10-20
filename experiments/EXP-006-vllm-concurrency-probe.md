id: EXP-006-vllm-concurrency-probe        date: 2026-10-20        owner: M4
hypothesis: a single-agent submission (`submission/agent.yaml`, one `LlmAgent`) issues at most one LLM
        generation request at a time, both across the Stage-1 grading loop (confirmed sequential,
        `notebooks/kaggle_eval_l4x4.py:380-383` has no `asyncio.gather`/concurrency) and within a single
        task. vLLM is booted with `gpu_memory_utilization=0.90` regardless of model size, so the real
        INT4-quantized model (~16-18 GB for the 31B) leaves most of the ~86 GB/model vLLM claims on
        L4x4 as unused KV-cache headroom under this single-request pattern. H1: for all 4 allowed model
        sizes, vLLM's own boot-time "Maximum concurrency for N tokens per request" figure at
        `max_model_len=32768` is > 1, i.e. real idle KV-cache capacity exists and is measurable without
        running any task. H2: that capacity scales roughly inversely with model size (31B lowest, 2B
        highest). H3: a synthetic concurrent-request burst against the already-booted server
        (N=1/4/16) shows aggregate throughput scaling with N up to roughly the measured max-concurrency
        ceiling, i.e. the idle capacity is not just a theoretical KV-cache number but is schedulable by
        vLLM under concurrent load.
single variable changed: n/a -- no agent run, no eval_config, no submission change. This is a read-only
        measurement of vLLM server boot logs and an optional synthetic HTTP burst against the server,
        using the same `VllmConfig`/`VllmServer` recipe the real harness uses (see config below), for
        each of the 4 allowed model sizes in turn. Zero interaction with `evaluate_task`, `Evaluator`,
        task cohorts, or the submission bundle.
cohort: n/a -- no tasks involved. "Cohort" here is the 4 allowed model variants:
        gemma-4-31b-it-qat-w4a16-ct, gemma-4-12b-it-qat-w4a16-ct, gemma-4-e4b-it-qat-w4a16-ct,
        gemma-4-e2b-it-qat-w4a16-ct (all `.../other/<name>/2` Kaggle Model inputs).
        GPU-h used: ~0.5 L4x4 kernel-hours expected (hard-capped at 55 min wall time via
        `GLOBAL_HARD_CAP_S` in the notebook itself; see follow-up 4 for the actual figure once run).
config: `notebooks/exp011_vllm_concurrency_probe/vllm_concurrency_probe.py` (source) ->
        `vllm_concurrency_probe.ipynb` (built via `tools/build_notebook.py`, not hand-edited).
        kernel: `rainm4/gemma4-exp011-vllm-concurrency-probe`
        (`notebooks/exp011_vllm_concurrency_probe/kernel-metadata.json`), pinned docker image
        `gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461`
        (required -- an unpinned kernel previously landed on Python 3.13 and crashed vLLM with
        `ImportError ... undefined symbol _ZN3c1013MessageLoggerC1EPKciib`), `machine_shape: NvidiaL4`,
        `enable_internet: false`, wheelhouse dataset + competition source attached, all 4 models attached
        as `model_sources`. Per model: boots a real `VllmServer(VllmConfig(...))` with the same fields
        the harness's own recipe uses -- `tensor_parallel_size=4`, `max_model_len=32768`,
        `gpu_memory_utilization=0.90`, `tool_call_parser="gemma4"`, `reasoning_parser="gemma4"`,
        `scheduler_reserve_full_isl=False` -- with two corrections made against the real
        `adk_submission` source rather than assumed: **`enable_lora=False`** (the real submission ships
        no adapters, so `VllmServer.build_cmd()` never emits LoRA flags in practice --
        `submission/adapters/` has only a README -- and the probe records each boot's real argv to
        `cmd/*.json` as evidence rather than assuming this), and the **12B model gets
        `--hf-overrides '{"architectures": ["Gemma4ForCausalLM"], "model_type": "gemma4"}'`** via
        `extra_args` (our own mirror notebook omits this because it never serves 12B; the real harness's
        `MODEL_VLLM_EXTRA_ARGS` requires it). Server stdout/stderr is continuously tee'd to a separate
        run-dir log file while the server runs, because `VllmServer.stop()` unconditionally deletes its
        own `log_path` in a `finally` block (`data/src/adk_submission/adk_submission/server.py:393-395`)
        -- without the tee, every capacity figure in the log would be lost even on a clean boot.
        Teardown sweeps any orphaned `nvidia-smi --query-compute-apps` processes (TP worker/EngineCore
        children can outlive the parent under `multiprocessing` `spawn`) and polls per-GPU memory back
        to baseline before moving to the next model; the whole run aborts early if a GPU is left dirty.
        One retry/diagnostic attempt is allowed per failing model (lower `gpu_memory_utilization` for
        OOM, `max_model_len=16384` for a too-small-KV-cache failure, a second faithful attempt for a
        timeout), budget-gated against a 45 min soft / 55 min hard wall-clock cap for the whole run.
        An optional ~1 min synthetic burst arm (N=1/4/16 concurrent chat-completion calls via
        `ThreadPoolExecutor`) runs once per model after a successful faithful boot, to test H3.
        Outputs land under `/kaggle/working/runs/EXP-006-vllm-concurrency-probe/`:
        `capacity.jsonl`/`capacity.csv` (one row per attempt), `summary.json` (per-model
        `max_concurrency_32k`, `idle_kv_fraction_1agent_32k = 1 - 1/max_concurrency_32k`, `speedup_n4`,
        and a `decision_hint` per the rule below), `env.json`, `model_configs.json`, per-attempt
        `cmd/*.json` argv dumps, raw server logs, and (if the burst arm runs) `burst/*.jsonl`.
        Designed by an Opus/high-effort subagent (full design brief + corrections in this session's
        transcript); implemented by Sonnet against this doc plus direct reads of
        `data/src/adk_submission/adk_submission/server.py` to verify every `VllmConfig`/`VllmServer`
        field name, `extra_args` shape, and the log-deletion/`.pid` behavior cited above.
results: **RUN COMPLETE 2026-10-20**, kernel `rainm4/gemma4-exp011-vllm-concurrency-probe` v1, COMPLETE,
        `total_wall_s = 1358.0` (22.6 min, well inside the 55 min hard cap and the 45 min soft budget).
        All 4 models booted on the first attempt (`attempt=1`, no retries needed), `teardown_clean=True`
        and `model_path_resolved_by=exact` for all 4, confirming the harness-faithful config (incl. the
        12B `--hf-overrides` and `enable_lora=False`) booted cleanly end to end. Confirmed empirically,
        not assumed: `lora_flags_in_cmd=False` for every model (no `--lora-modules`/`--enable-lora` in
        the real argv -- matches the design's correction that the real submission never emits LoRA
        flags since it ships no adapters). `extra_args` for the 12B row shows the expected
        `--hf-overrides '{"architectures": ["Gemma4ForCausalLM"], "model_type": "gemma4"}'` and is empty
        for the other 3, as designed.

        | model | max_concurrency_32k | idle_kv_fraction_1agent_32k | boot_s | speedup_n4 | speedup_n16 |
        |---|---|---|---|---|---|
        | 31B | **8.74** | 0.886 | 376.5 | 3.60x | 9.85x |
        | 12B | 19.97 | 0.950 | 217.3 | 3.54x | 9.44x |
        | e4B | 45.63 | 0.978 | 289.4 | 3.47x | 9.45x |
        | e2B | 67.18 | 0.985 | 245.3 | 3.21x | 9.05x |

        H1 (max_concurrency_32k > 1 for all 4 models): **CONFIRMED** -- lowest is 31B at 8.74, i.e. an
        already-booted 31B server could in principle serve ~8-9 full-length (32k-token) concurrent
        requests before running out of KV-cache blocks, under a single-agent submission that never
        issues more than 1 at a time. 88.6% of the 31B server's usable KV-cache capacity sits idle under
        the current one-request-at-a-time pattern.
        H2 (capacity scales inversely with model size): **CONFIRMED**, monotonic and large: 31B (8.74) <
        12B (19.97) < e4B (45.63) < e2B (67.18), roughly tracking each model's much smaller weights
        footprint (`weights_gib_total`: 5.96 / 2.29 / 3.31 / 2.66 GiB) leaving more of the fixed ~90%
        GPU-memory budget free for KV-cache blocks.
        H3 (synthetic burst throughput scales with N up to roughly the measured ceiling): **CONFIRMED**
        for N=4 (3.2x-3.6x aggregate speedup vs N=1 across all 4 models, i.e. real schedulable
        throughput gain, not just a theoretical KV-cache number) and still scaling at N=16 (9.0x-9.9x,
        sub-linear as expected since N=16 approaches or exceeds `max_concurrency_32k` for 31B/12B).
per-repo: n/a -- no task repos involved in this experiment.
decision: **ADOPT the decision rule's "proceed" branch.** `max_concurrency_32k(31B) = 8.74 >= 4` AND
        `speedup_n4 = 3.60 >= 2.0`, so per the pre-registered rule this experiment's own
        `summary.json.decision_hint` reads: **"proceed to EXP-007 ParallelAgent concurrency probe
        (N=2..4 branches)."** The idle KV-cache capacity on L4x4 is real, large (88.6% idle even on the
        biggest allowed model), and demonstrably schedulable under concurrent HTTP load -- this clears
        the bar the design set for moving on to the next, harder question (whether ADK's `ParallelAgent`
        /parallel `AgentTool` dispatch can actually exploit it for real agent work, not just raw HTTP
        concurrency). This does **not** by itself validate any resolve-rate or LB benefit -- see
        follow-up 2, unchanged from the original design.
follow-ups:
  1. Done 2026-10-20: kernel pushed, completed, `summary.json`/`capacity.csv` retrieved into
     `runs/EXP-006-vllm-concurrency-probe/` (gitignored); results/decision above and
     `experiments/README.md` §2/§3 filled in with the real per-model max-concurrency figures.
  2. This experiment establishes only: (a) boot-time KV-cache headroom per model, and (b) a synthetic
     HTTP-burst throughput scaling figure against an idle vLLM server. It does **not** establish that
     ADK's `ParallelAgent` or parallel `AgentTool` dispatch actually issues concurrent LLM calls in
     practice, nor anything about the real (sequential) Stage-1 task loop, nor any resolve-rate/LB
     implication. A separate, smaller follow-up (`EXP-007` candidate, ~15 min, 4 falsification arms:
     sequential control, `ParallelAgent`, parallel `AgentTool` calls, a sync-tool-call loop-blocking
     check) is the right next step if this experiment's decision rule says to proceed -- not yet built.
  3. A known blocker flagged for that follow-up regardless of this experiment's outcome: every
     swegemma tool (`run_command`, etc.) is a synchronous function invoked directly on the asyncio event
     loop by `FunctionTool._invoke_callable`, so one long sync tool call (e.g. pytest) would stall
     sibling branches of a `ParallelAgent` even while vLLM itself has spare capacity -- this needs to be
     checked empirically, not assumed, by EXP-007.
  4. Done 2026-10-20: actual wall time was 1358.0s (22.6 min total for all 4 models), well inside the
     45 min soft / 55 min hard cap -- the self-imposed budget held with large margin.
