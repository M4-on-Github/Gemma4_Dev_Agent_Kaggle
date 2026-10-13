id: EXP-001-baseline        date:            owner:
hypothesis: the v1 phased prompt with 4.5 min / 45 calls finishes every task inside the cap, with empty-patch
            and overflow rates well below community baselines, at a dev-48 resolve rate of 10–25%.
single variable changed: baseline (reference point for E1–E11)
cohort: smoke-8 first (sanity), then dev-48        seed: 20261013        GPU-h used:
config: git tag v1; zip sha256 (from tools/pack_submission.py): ________________
        eval_config: 4.5 min / 45 calls / 70 turns / 300 s ; sampling: T 0.2, top_p 0.95, top_k 64,
        max_output_tokens 4096, thinking on, thinking_budget 256
results: resolve ___/48 (Wilson CI __–__), empty __%, overflow __%, malformed __%, spin __%,
         median wall __ min, p90 __ min, projected 12 h total __ h, worst case __ h
per-repo: fastapi __/22, rich __/16, requests __/9, httpx __/1
decision: submit v1 to the LB regardless (plan §4.6) if projected worst case ≤ 11 h and no crash
follow-ups: run a second seed/session to measure variance (plan §5.5); start E1/E2.
