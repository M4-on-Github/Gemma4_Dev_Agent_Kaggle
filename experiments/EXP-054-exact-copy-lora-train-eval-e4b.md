# EXP-054 — Exact-copy LoRA on the E4B, stages 1 to 3: build pairs from public files, train a rank-8 q/o adapter on the call tokens only, and read it offline under the harness's own server

**Date:** 2026-11-08
**Type:** zero-task GPU kernel, one kernel, no agent run, no grading, no upload. Expected **0.75-0.90 L4x4-h**; the notebook's hard cap is **3,400 s from its first code cell (0.94 h)**, so the worst case is **at most 0.98 h** with the container start and the last cell (section 2.6). Below 1 GPU-h, so no critic prereg (dispatch 2026-11-08). The day ledger is the lead's: this line's share is about 1.2 h of the 4.0 h day ceiling.
**Cohort:** none (no task runs; the notebook has no `TASK_IDS` and no `RUN_AGENT` parameter)
**Ladder:** D-006 stages 1 to 3, the gate passed in EXP-048 (5f3c654). Not a screen on tasks: whether an adapter copies edit targets exactly is a per-call question that smoke-8 cannot read (8 tasks give about 8 to 30 edit calls, unpaired across arms). The stage-4 smoke on tasks is a later EXP of its own, licensed only by reading R3 here.
**Pre-registered:** this file, the notebook source and the analysis script are committed before the push. Sections 3 to 5 are written blind and are not revised; results are appended below the line.
**Serves:** C-024 (narrow exact-copy adapter), D-006 stages 1 to 3, Q4 (follow-up: an adapter that is applied and trained, not a canary).
**Relates:** EXP-047 (adapter applied on the E4B, A3 / B3; decode 116.63 against 86.96 tok/s), EXP-048 (costing and gate), EXP-038 (the E4B single loop on dev-48, the shipped tree `9de869bd`), S-014 / EXP-050 (the same zip on the board, 3/58).
**Tags:** [V] verified in source or by a check run here, [M] community or mirror, [I] inference.

**Data rule (dispatch 2026-11-08).** Training and evaluation windows come from public files only: the Python standard library inside the kernel's own image. The competition source is attached only because a GPU probe without it gets 2 GPUs, not 4 (EXP-047 §9.1 and §10). **The notebook reads nothing under the competition mount**: no tasks, snapshots, graphs or traces. Whether training on competition data is allowed is not asked here. Adapter weights and training data never enter git. Training sequences stay in the kernel's `/tmp`. The adapter is written to `/kaggle/working/sub1/adapters/copy_lora`. The edit-call arguments, which are standard-library text, are written to `calls.jsonl` in the run dir. Everything downloaded goes to `runs/`, which is gitignored.

## 1. Why this, now

- C-024 says that a LoRA trained only on exact-copy edit calls raises the share of E4B tasks with an applied edit. EXP-048 priced it and set a three-part gate; the gate passed on 2026-11-08 (EXP-048 "Gate check").
  - EXP-047 v2 read A3 / B3: the harness's own `VllmServer` start path applies an `adapters/` LoRA on the E4B [V].
  - At the measured adapter decode rate, EXP-038's per-task wall grows by +17.5 s mean (decode component) or +29.2 s (whole-wall bound), against 225.3 s of spare. No task goes over the 480 s cap, and the projection is 3.56 to 3.96 h.
  - Feasibility: BF16 parents are public [V]; training runs in plain torch, without peft [V for the packages]; memory is on paper only, so it is measured here.
- Nothing yet shows that such an adapter can be trained in one kernel, that it changes the exact-copy rate, or what it does to the agent's other calls. Stages 1 to 3 answer that offline, on held-out windows. No task run is spent and no upload slot.

## 2. Design

### 2.1 Stage 1: edit items and their rendering (CPU, in the kernel)

- **Source.** The kernel's own standard library (`sysconfig.get_paths()['stdlib']`). Each top-level package with an `__init__.py` counts as one "repository". Excluded: test and tool directories (test, tests, idle_test, encodings, pydoc_data, site/dist-packages, lib2to3, turtledemo, ensurepip, venv, idlelib, `__phello__`).
- **Files.** ASCII only, LF line endings, 80 to 4,000 lines. A file is dropped if it holds the chat template's delimiters (`<|`, `|>`) or the strings `tool_call` or `<tool`.
- **Edits.** Made by the `ast` in module-level functions and class methods of 6 to 90 lines. Each function contributes at most one edit per kind:
  - **K1:** the integer constant that occurs once in the function, `n -> n + 1`;
  - **K2:** the single `==` or `!=` in the function, flipped;
  - **K3:** a one-line call statement whose callee name occurs once in the function, deleted.

  The target `old_string` is the smallest block of 2 to 8 whole lines around the edited line that occurs exactly once in the file and starts and ends on a non-blank line. `new_string` is that block with the edit made. Each item is checked: replacing the block yields a file that parses and whose `ast` differs from the original.
- **Split.** Packages are ordered by the sha256 of their name. The first ones form the held-out set, until it holds at least 20% of packages and 400 items. No package is in both sets.
  - Eval: **120 held-out edit windows**, balanced 40/40/40 over K1/K2/K3, one per function and at most 3 per (file, kind).
  - Drift: **48 held-out first-turn prompts**, taken from the eval items.
  - Training: **400 training windows**, plus **64 training first-turn prompts**.
  - Local check (2026-11-08, this machine's Python 3.13 stdlib): 2,434 items from 186 files; 120 eval and 400 training items; 0 of 520 failed the uniqueness, window and `ast` checks. The kernel's stdlib differs; its counts are recorded in `run.json`.
- **Window.** The function plus 3 lines on each side, capped at 150 lines and 10,000 characters (the harness's read limits). It is rendered by the harness's own `swegemma.tools.workspace.make_read_file`. A stub context serves `copy_from` from a local copy of the package, as the sandbox would serve `/workspace`. A window whose content differs from the file's lines, or that comes back truncated, is dropped and counted.
- **Prompt.** The user turn comes from the harness's own `build_agent_prompt`. Its inputs:
  - a task whose repository is `python-stdlib/<pkg>`;
  - a problem statement in our own words, naming the file, the function and the change, with no line numbers;
  - the shipped eval budgets (240 s, 28 calls, 8 min, 80 turns);
  - the six declared tools;
  - the workspace tree from the harness's own `build_workspace_tree_command`, run over the package copy.
- **History.** An edit prompt is the user turn plus one prior model turn. That turn holds a thought in our own words and one `read_file` call for the window, followed by the harness tool's response. A drift prompt is the user turn alone, the task's first turn.
- **Request.** The agent is compiled from the shipped tree by the official `compile_submission`. Each history is sent through the agent's own LiteLlm, with the adk_submission patches, to a local capture endpoint, and the captured HTTP body is what goes to vLLM. Only the model name, the temperature (0 for greedy) and `return_token_ids` change.
  - The ADK identity line is added by hand, in ADK's wording. This is the one place where the request is not produced end to end by ADK's own processors.
  - If the capture fails, hand-built messages are used. The path taken is recorded (`run.json` `paths.request`).
  - The server's `/tokenize` of the same body is compared with the prompt ids that a chat request returns (`render_check`).

### 2.2 Stage 2a: training pairs (on-policy prefixes)

- **Boot 0.** The shipped tree `9de869bd` (S-014, the EXP-038 zip) is served with no adapter. The base model generates once, at the shipped sampling, on each of the 400 training windows and the 64 training first-turn prompts.
- **Pair.** Used when the base's first call on a training window is `edit_file`.
  - Prefix: the prompt ids plus the base's own completion tokens, through its `<|tool_call>` token.
  - Target: the call `call:edit_file{...}` with the correct `old_string` and `new_string`, keeping the base's own key order and its own filepath spelling when that names the right file. Then `<tool_call|>`, and the base's next token if it is an end token.
  - The target is kept only if all three checks pass: its tokens decode back to the text; it carries six string-delimiter tokens; and vLLM's own argument grammar (`_parse_gemma4_args`) recovers the exact strings.
- **Anchor.** Any other first call, on a training window (`anchor_read`) or on a first-turn prompt (`anchor_first`). The target is the base's own call tokens, so its non-edit behaviour is trained to stay put.
- **Mix.** First-turn anchors number at most half the pairs, and all anchors together at most the pairs. Loss is on the target tokens only.

### 2.3 Stage 2b: training (one child process under torchrun, 4 ranks)

- **Weights.** BF16 parent `google/gemma-4/transformers/gemma-4-e4b-it-qat-q4_0-unquantized/2`, loaded with `Gemma4ForConditionalGeneration` in bf16 and sdpa attention. If that load fails, the served w4a16 checkpoint is decompressed with `CompressedTensorsConfig(run_compressed=False)`. The source used is recorded.
- **Placement.** The per-layer embedding table and the vision and audio parts are moved to the CPU. All base weights are frozen.
- **LoRA.** Rank 8, alpha 16, on `q_proj` and `o_proj` of every text layer. A is fp32 (Kaiming), B is zero. The adapter is applied in bf16.
- **Loop.** Gradient checkpointing (non-reentrant); micro-batch 1; gradient accumulation 2; LoRA gradients all-reduced by hand. AdamW at lr 5e-4, 5 warmup steps, then cosine to 10% over whichever ends first, two epochs or the time cap.
- **Memory probe.** The longest sequence is run at the largest length that fits, cut from the left, from the ladder 12,288 / 10,240 / 8,192 / 6,144 / 4,096. Longer sequences are dropped and counted.
- **Time.** Training stops at kernel second 2,050 or after 660 s of optimisation, whichever comes first. If the 4-rank run saves no adapter and time remains, it is retried once with one process.
- **Output.** Rank 0 writes the PEFT layout. Keys are `base_model.model.<module>.lora_{A,B}.weight`, with module names taken from the served checkpoint's safetensors index, as in EXP-047. `train.json` records the source, the steps, the sequences seen, the pair and anchor losses, the B norms and the memory peaks.

### 2.4 Stage 3: offline read under the harness's own server (boot 1)

- **Server.** `sub1` = the shipped tree plus `adapters/copy_lora` and one `adapter: copy_lora` line, served by `VllmServer` with the same arguments as EXP-047. Base and adapter are read on the same server, as `base1` and `copy_lora`.
- **Order.**
  1. Decode probes on the idle server, alternating base1 and adapter, two each (256 tokens, `ignore_eos`).
  2. Logprobs of the two own-words texts from EXP-047, for base1, base1 repeated and the adapter.
  3. The routing check through the compile path.
  4. The request phase, interleaved per prompt (base1, then adapter):
     - greedy on the 120 edit windows and the 48 first-turn prompts;
     - the shipped sampling (T = 1) on the first 60 edit windows.
- **Boot-0 comparison.** Boot 0 also ran base0 greedy on the same 120 + 48 prompts, and base0 logprobs twice. This gives a boot-to-boot floor.
- **Judge.** The first tool call of each edit prompt is judged against the full raw file, with the harness's own `swegemma.edit.apply_replacement`. The class is the first that applies:
  - **x:** no call, or another tool;
  - **f:** missing or empty arguments;
  - **w:** wrong file;
  - **g:** `old_string` matches more than once;
  - **c:** no match;
  - **b:** applied by a fuzzy strategy;
  - **E:** exact and unique.

  Besides the class, two outcomes are recorded per prompt: `correct_strict` (the resulting file equals the gold file) and `correct_ast` (the same `ast`).

### 2.5 What is fixed and what varies

- **One variable:** the adapter. It is base1 against the adapter on one server, on the same prompts, greedy.
- **Fixed:** the shipped tree's prompt, tools, sampling and eval budgets, and the served w4a16 checkpoint. Only the temperature differs between the greedy read and the T = 1 subset.
- **Zip:** `dist/EXP-038-e4b.zip`, sha256 `9de869bd2cd8853b72d653d06b9acef3e03794c8b588c26494435774dda11ac0`. It is embedded, and the notebook checks its sha256.

### 2.6 Cost and the hard cap

Seconds from the notebook's first code cell (`T0`). All are [I] estimates, built from the EXP-047 v2 and EXP-038 boots.

| item | seconds | bound in the notebook |
|---|---|---|
| wheelhouse install and imports | 100 to 150 | none (EXP-047: about 120) |
| stage 1 items, rendering, workspace trees | 60 to 120 | local run 59.5 s; stops as infrastructure if boot 0 would start after 700 s |
| boot 0 (E4B, no adapter) | 290 to 330 | startup timeout 600 s |
| capture, render check, logprob probes | 20 to 60 | request timeout 120 s each |
| boot 0 request phase: 464 training generations, 168 greedy eval and drift prompts | 250 to 560 | deadline `min(now + 560, 1500)`; late results are dropped |
| teardown 0, training sequences, PEFT keys | 30 to 60 | |
| training child (load about 120 to 200, then optimisation) | 400 to 860 | the loop stops by second 2,050 or after 660 s; subprocess timeout to second 2,290 |
| boot 1 (E4B, the adapter) | 300 to 450 | not started after second 2,500; startup timeout 720 s |
| boot 1 probes and request phase (2 x 120 greedy edit, 2 x 48 drift, 2 x 60 at T = 1) | 200 to 600 | deadline `min(now + 600, 3310)` |
| teardown and quick look | 20 to 40 | |
| **total** | **2,700 to 3,250 s = 0.75 to 0.90 h** | |

- **Worst case.** Every wait is bounded so that the last cell ends at about `HARD_CAP_S` = 3,400 s (0.94 h). The container start and the env cell before `T0` add about 1 to 2 minutes, so the worst case is **at most 0.98 L4x4-h**.
- **Ledger.** At dispatch: 0.52 h used today, EXP-053 running with a worst case of about 1.24 h, and this line's share about 1.2 h. 0.52 + 1.24 + 0.98 = 2.74 h, under the 4.0 h day ceiling. Rechecked at the build against `knowledge/plan.md` (93a0c22): EXP-045 0.248 and EXP-053 0.281 are measured, and EXP-055 is running (0.30 expected). Even if EXP-055 ran to about 1.24 h, 0.529 + 1.24 + 0.98 = 2.75 h, still under 4.0. 0.98 h is under the 1.2 h share. With EXP-055 running, this is the second kernel at a time, which the plan allows.
- **One kernel.** This is the second and last kernel of the line under the 2026-11-08 dispatch. There is no re-run of a failed kernel, no dev-48 and no upload.

## 3. Endpoints, fixed in advance

All endpoints come from the run dir (`run.json`, `eval.jsonl`, `probes.jsonl`, `train.json`). They are read by `experiments/EXP-054/analyze_copy_lora.py`, which does not read `calls.jsonl`.

| # | Endpoint | Definition |
|---|---|---|
| E1 | exact rate, base1 and adapter | share of the paired boot-1 greedy edit prompts (both arms HTTP 200) whose first call is class E; Wilson 95% CI |
| E2 | Δ exact, McNemar | adapter − base1 on the same prompts; exact two-sided McNemar on the discordant pairs |
| E3 | base0 on the same ids | the exact rate of base0 (boot 0) and of the adapter on the paired ids that base0 also answered; the boot-to-boot agreement of base0 and base1 |
| E4 | classes | the E/b/g/c/f/w/x counts per arm; edit-call rate; `correct_ast` and `correct_strict`; exact given an edit call; exact by K1/K2/K3; class disagreement (share of paired prompts whose class differs) |
| E5 | drift gate, G1 to G5 | see below |
| E6 | decode drop | 1 − (adapter tok/s ÷ base1 tok/s), from the idle boot-1 decode probes |
| E7 | training | weight source, ranks, the fitted length, sequences and pairs that fit, steps, pair and anchor loss over the first 5 and the last 5 steps, the B norm, peak memory |
| E8 | recorded, not read | the T = 1 subset (n, exact per arm, McNemar), the render check, the request path, the data counts, the first tools per arm |

**Drift gate (E5).** All five must hold.

- **G1.** On the paired drift prompts, the first-tool agreement of the adapter with base1 is ≥ 0.70. It must also be ≥ the base0-base1 agreement minus 0.10.
- **G2.** The no-call share rises by at most 0.10, adapter against base1. It is pooled over the paired edit and drift prompts.
- **G3.** On the drift prompts:
  - the mean completion tokens, adapter ÷ base1, lie within [0.67, 1.5];
  - the mean call tokens, on prompts where both arms made a call, lie within [0.8, 1.25].
- **G4.** The mean per-token |Δ logprob| of the adapter against base1, over the two own-words texts, is ≤ 0.15. The floor (base1 repeat against base1, and base0 repeat against base0) is recorded alongside it.
- **G5.** The `correct_ast` rate of the adapter is ≥ that of base1 minus 0.05.

## 4. Pre-registered readings, written blind

These readings are written before any number exists and are not revised. The first row that matches wins. "X+" means Δ exact ≥ +0.10 with McNemar p < 0.05; "X−" means Δ exact ≤ −0.10 with p < 0.05.

| row | condition | reading | what follows |
|---|---|---|---|
| **R0 infrastructure** | The run status is missing, `started` or `infrastructure`. Or fewer than 32 training pairs were kept (unless the status is `boot1_failed`). Or the run completed with fewer than 60 paired edit prompts. | Nothing about the adapter is read. | The stage reached and the cause are recorded in section 9. There is no re-run under this dispatch; a fix is proposed, not applied. C-024 is unread, not refuted. |
| **R1 not applied** | Boot 1 failed or did not start. Or `copy_lora` is not in `/v1/models`. Or more than half the adapter requests were not HTTP 200. Or the compiled agent's model does not name `copy_lora`. Or the adapter responses name a model other than `copy_lora`. | The trained adapter did not reach the served model. That conflicts with EXP-047 A3 for a canary of the same layout, so the difference is in what training wrote (shapes, keys, dtype) or in the boot. | The failure class is recorded, and a harness-stack note is made if it is a tooling fact. The line stops until the lead decides. |
| **R2 near-zero** | 0 optimiser steps. Or a B norm of 0. Or both of these at once: the logprob drift is ≤ max(2 × the boot-1 floor, 0.005), and the class disagreement is ≤ 0.05. | Training ran, but the adapter barely changes the model. The dose is too small for this read. | Recorded with E7. A larger dose (steps, lr, rank) would be a new pre-registration, which is the lead's call. |
| **R3 positive, clean** | X+, and all of: the drift gate passes; the decode drop is ≤ 0.35; and the adapter's exact rate on the base0 ids is ≥ base0's. | The adapter raises exact copying on held-out windows without moving the agent's other first calls, at a decode cost the EXP-048 gate admits. | This is evidence for C-024, offline and per call. It licenses one stage-4 pre-registration: a smoke-8 on tasks with the adapter shipped. Nothing here licenses an upload. |
| **R4 positive, costly** | X+, but some R3 condition fails. | Copying improves, but with drift, decode cost or a boot effect that the clean reading excludes. Which condition failed is named in section 9. | No stage 4 on this adapter. One revision (more anchors, fewer steps, or q only) could be pre-registered; the lead decides. |
| **R5 no move** | Neither X+ nor X−. | At this dose (rank 8, q/o, ≤ 660 s of training), the adapter does not move exact copying by 0.10. | C-024 gets negative evidence at this scale. The line stops unless the lead picks one change. |
| **R6 harmful** | X−. | The adapter makes copying worse. | The line stops. The class shift (E4) is recorded. |

**Power, noted before the run [I].** With 120 paired prompts and a base exact rate near 0.5, a +0.10 move needs about 12 more adapter-only wins than base-only wins. With about 20 discordant pairs that reaches p < 0.05; with 40 it does not reach it at +0.10 alone. A Δ between +0.05 and +0.10 reads R5 by design.

**Blind prediction (not a reading).** R0 25%, R1 5%, R2 5%, R3 20%, R4 15%, R5 25%, R6 5%. The point guesses are a base1 exact rate of about 0.5 and an adapter rate of about 0.6.

**Synthetic check of the analysis (code paths, not results).** A scratch generator (`out/exp054_synth.py`, not committed) writes seven synthetic run dirs, and the script returned R3, R4, R5, R6, R2, R1 and R0 for the seven scenarios built to hit them.

## 5. Limits, stated before the run

1. **Offline and per call, not per task.** The read is the first call after one synthetic read of the window. A real task has a longer history, its own search path and a later edit. R3 says nothing about the resolve rate; that is stage 4's question.
2. **The history is synthetic.** The prior model turn is one own-words thought and one `read_file` call. The base's own thoughts in a real run differ, so the prefix is on-policy only from the completion onward.
3. **Standard-library code may be memorised.** Both arms see the same windows, so a memorised file helps both. It can still shrink the room for a move, or let the adapter learn to recall rather than to copy.
4. **Trained on the BF16 QAT parent, served on w4a16.** The shapes and module names come from the served index, but no explicit check runs before boot 1. A mismatch shows as a boot-1 failure or a refusal (R1). A numerical gap between parent and served weights would weaken the adapter and could read R2 or R5.
5. **The identity line is added by hand** (section 2.1, Request). The render check compares the server's own rendering with the chat request; it does not compare with a request that ADK built end to end.
6. **The competition source is mounted but not read.** It is attached for the GPU count only. No path in `copy_lora.py` names it.
7. **One kernel, one seed.** A boot-to-boot floor is measured (base0 against base1), but there is no second training run. A positive reading is one adapter, not a recipe.
8. **The gate on drift is coarse.** It looks at first calls and two own-words texts. An adapter that moves later calls, or the content of a thought, can pass it.
9. **Time-capped training.** If the loop stops on time, it has seen fewer than two epochs; `train.json` records how many sequences it saw. A short run that reads R2 or R5 is a dose result, not a refutation of C-024.

## 6. Exact commands

```
python tools/build_notebook.py --src notebooks/exp054_copylora/copy_lora.py --embed dist/EXP-038-e4b.zip --out notebooks/exp054_copylora/copy_lora.ipynb
# kernel-metadata.json is then written by hand (section 8); the push is the bare command, once
kaggle kernels push -p notebooks/exp054_copylora
# after COMPLETE, a separate job:
kaggle kernels output rainm4/gemma4-exp054-copy-lora -p runs/EXP-054-copy-lora/
python -I -X utf8 experiments/EXP-054/analyze_copy_lora.py runs/EXP-054-copy-lora --json runs/EXP-054-copy-lora/analysis.json
```

The bundle usually nests one level, and is flattened with `cp -r`. Everything in it is read as data with `python -I -X utf8`, and nothing from it is run. The adapter weights and `calls.jsonl` stay under `runs/`.

## 7. Results

None yet. Results are appended in section 9 and apply section 4 as written.

## 8. Built

2026-11-08, built (no GPU spent before the push).

- **Files.**
  - Source: `notebooks/exp054_copylora/copy_lora.py` (py:percent).
  - Notebook: built with the section 6 command into `notebooks/exp054_copylora/copy_lora.ipynb` (13 code cells). It embeds `dist/EXP-038-e4b.zip`; the decoded bytes have sha256 `9de869bd...1ac0`, equal to the notebook's `ZIP_SHA256`.
  - Metadata: `notebooks/exp054_copylora/kernel-metadata.json`.
  - Analysis: `experiments/EXP-054/analyze_copy_lora.py`.
- **Kernel id** `rainm4/gemma4-exp054-copy-lora`. Private, GPU on (`NvidiaL4`, the EXP-047 docker image), internet off.
  - Inputs: the wheelhouse `metric/gemma-4-developer-agent-wheelhouse`; the competition `gemma-4-developer-agent`, for the GPU count only; and two models, `google/gemma-4/other/gemma-4-e4b-it-qat-w4a16-ct/2` (served) and `google/gemma-4/transformers/gemma-4-e4b-it-qat-q4_0-unquantized/2` (the BF16 parent, for training).
  - Every other key equals EXP-047 v2.
- **One build fix, before the first commit.** The first build looked for the BF16 parent with a recursive glob over all of `/kaggle/input`. That would have walked the competition mount, so the search is now confined to the model mount: two explicit paths, then a glob under `/kaggle/input/models` only. After the fix, no path in the source names the competition mount.
- **Checks run locally (no GPU).**
  - Every code cell parses.
  - A crude unbound-name check is clean, on the notebook and on the training child's source.
  - The guard's own parameter regex finds no `RUN_AGENT` and no `TASK_IDS` line.
  - Stage 1a ran on this machine's standard library (section 2.1 counts).
  - The analysis ran on seven synthetic run dirs (section 4).

  These check code paths, not results. Training and both boots run only in the kernel.
- **Push guard.** It reads this as a zero-task GPU probe: no `RUN_AGENT` and no `TASK_IDS` parameter, `**Cohort:** none`, and the main competition source alone (rule dd8d3fc). Model sources are not restricted by the rule.
- **Pushed 2026-11-08 (addendum written after the push; nothing above is revised).**
  - Authority: the user's request of 2026-11-08, about 18:19 UTC, relayed by the lead ("prep and push the lora training test exp"). Also the standing approval within the day's 4.0 GPU-h ceiling (`knowledge/user-decisions.md`, 2026-11-08).
  - Ledger at the push, as the lead stated it: 0.83 of 4.0 (EXP-045 0.248, EXP-053 0.281, EXP-055 about 0.30 and running). With this kernel's 0.98 worst case, that is about 1.81. EXP-055 is the only other kernel running.
  - Pre-push checks: this file is tracked once and clean, and the directory holds one `.ipynb`.
  - The push: the bare command from the repo root, once, between 18:20:42Z and 18:20:54Z UTC, from commit 2b89d60. It printed "Kernel version 1 successfully pushed." The guard did not refuse.
  - Kernel `rainm4/gemma4-exp054-copy-lora` **version 1**. One `kaggle kernels status` call right after returned `KernelWorkerStatus.RUNNING`.
  - Expected 0.75 to 0.90 L4x4-h; worst case at most 0.98 h.
  - If the kernel fails, there is no re-run without the user's word.

### v2, an infrastructure fix, 2026-11-08

Written before the v2 push. Nothing above is revised.

- **Authority.** The user approved it at about 19:15 UTC, relayed by the lead ("fix the lora"). The approval covers one push of version 2; any further re-run needs the user's word again.
- **The one change.** This is the two-line fix proposed in section 9.4, applied to the capture cell of `copy_lora.py`, and nothing else:
  - `import http.server` is replaced by `from http.server import BaseHTTPRequestHandler`;
  - the capture handler's base class changes from `http.server.BaseHTTPRequestHandler` to `BaseHTTPRequestHandler`.

  The global helper `http()` is therefore no longer shadowed.
- **Rebuilt with the section 6 command.** The diff of the new `copy_lora.ipynb` against the v1 file is the same two lines.
  - New notebook sha256 (worktree file): `289d4cdd66ff8d59d3d840ab79b1cb0411fdff1933a3ecb9ff2a004a817557b4`. v1's was `db4667666ede62f7521aaee51cc59b9f03fc929ea11f769b4a47d0e7f1495a50`.
  - The embedded zip still decodes to `9de869bd...1ac0`.
  - There are 13 code cells. There is no `RUN_AGENT` or `TASK_IDS` line, and no path names the competition mount.
- **Unchanged.** `kernel-metadata.json` is byte-identical: the same id, inputs and machine. Also unchanged:
  - sections 1 to 7 (design, endpoints and readings);
  - every parameter and cap (`HARD_CAP_S` 3,400 s);
  - the analysis script.
- **Pre-push checks.**
  - The source parses, and so does the training child's source.
  - The crude unbound-name check is clean on both.
  - The new check for a name bound both by a `def` or `class` and by an `import` or `from` finds none in either source (v1 had exactly one, `http`).
- **Risk, as in section 9.4 [I].** Everything after boot 0 runs in a kernel for the first time, so a later defect would read R0 again.
- **Cost.** Expected 0.75 to 0.90 L4x4-h, worst at most 0.98 h. The day ledger at dispatch was 0.971 of 4.0, so it reaches about 1.95 at the v2 worst case. The screener's loop kernel is the other slot.

## Status

~~2026-11-08: **PRE-REGISTERED AND BUILT, not pushed.** Zero GPU spent. Expected 0.75 to 0.90 L4x4-h, worst case at most 0.98 h (`HARD_CAP_S` 3,400 s). Next: the bare push of `notebooks/exp054_copylora`, once, then section 8 records the kernel version.~~

~~2026-11-08: **PUSHED.** Version 1 of `rainm4/gemma4-exp054-copy-lora` was pushed at 18:20 UTC from 2b89d60 and showed RUNNING. Expected 0.75 to 0.90 L4x4-h, worst case at most 0.98 h. Not analyzed yet; download and analysis are a separate job, using the section 6 commands. When the kernel is COMPLETE, the next step is `kaggle kernels output rainm4/gemma4-exp054-copy-lora -p runs/EXP-054-copy-lora/`, then flatten the nested bundle and run `python -I -X utf8 experiments/EXP-054/analyze_copy_lora.py runs/EXP-054-copy-lora --json runs/EXP-054-copy-lora/analysis.json`.~~

2026-11-08: **v1 ERROR, read as R0 (infrastructure)** (section 9).
- It died in our own notebook code at about kernel second 495, right after the boot-0 vLLM server came up and before any request. A global helper name was shadowed by an `import` [V].
- GPU 0.140 h (kernel-log span).
- No pairs were built, no training ran, and no adapter was read. C-024 is unread, not refuted.
- The proposed fix is two lines in the capture cell (section 9.4). It is not applied and not rebuilt.
- A v2 needs the user's word. If approved, the next steps are: apply 9.4, rebuild with the section 6 command, record a section 8 addendum, then push the bare command once.

---

## 9. Results, v1, 2026-11-08. Section 4's readings applied as written.

Kernel `rainm4/gemma4-exp054-copy-lora` version 1 ended with status `KernelWorkerStatus.ERROR` (the lead checked at 19:06 UTC, and `kaggle kernels status` showed the same at the download).

- **Download.** Section 6 command, `kaggle kernels output rainm4/gemma4-exp054-copy-lora -p runs/EXP-054-copy-lora/`. The bundle nested one level, as usual, and was flattened with `cp -r`.
- **What it holds.**
  - `run.json`, `env.json` and `boot0.log`;
  - the two trees `sub0/` and `sub1/` (the shipped tree; `sub1` has no adapter yet);
  - the kernel log.

  There is no `eval.jsonl`, `probes.jsonl`, `calls.jsonl` or `train.json`, and no adapter.
- **How it was read.** Everything was read as data with `python -I -X utf8`; nothing from the bundle was run. `python -I -X utf8 experiments/EXP-054/analyze_copy_lora.py runs/EXP-054-copy-lora --json runs/EXP-054-copy-lora/analysis.json` ran (exit 0) and returned **R0**, with the conditions "run status started" and "training pairs None < 32".

### 9.1 Where and why it stopped [V]

Times are kernel-log seconds. The notebook's own clock runs about 9 s behind: its `rendered` stage at 149.4 s is logged at 158.7 s.

| stage | kernel-log s | notebook s | record |
|---|---|---|---|
| wheelhouse installed (41 of 41 wheels) | 62.8 | | log |
| env, 4 GPUs, BF16 parent found | 104.5 | 95.2 | `run.json` `installed` |
| stage 1 items | 158.1 | 148.8 | 24 packages, 164 files, 2,222 items (404 held-out, 1,818 training); eval 120, drift 48, training 400 + 64 first-turn |
| stage 1 rendering through the harness tools | 158.7 | 149.4 | 0 bad windows; `build_agent_prompt`, `EvalConfig`, `make_read_file` and `swegemma.edit` all from the harness |
| boot 0: vLLM up | before 494.8 | | `boot0.log`: KV pool 298,464 tokens; engine init 137.98 s; "Application startup complete." |
| **failure** | **494.8** | about 485 | papermill `PapermillExecutionError` at "In [8]" (the boot-0 cell) |
| last log entry | 502.3 | | nbconvert writes the results |

- **The exception.** `TypeError: 'module' object is not callable`. It was raised inside our `boot()` helper, at its first call to our HTTP helper `http(...)`, which lists `/v1/models` after the server has started.
- **The cause.** The source shows it. The helper is defined as a function named `http` (`copy_lora.py`, the log/HTTP/boot cell). The next cell, the ADK capture cell, runs `import http.server`. That statement binds the global name `http` to the standard-library package and replaces the function. Every later `http(...)` call therefore raises this TypeError.
- **How sure.** This is [V] on two grounds: the traceback names the line, and a scan of the source for names bound both by a `def` and by an `import` finds exactly one such name, `http` (definition and import in the same two cells). The training child's source has none.
- **Status.** The exception escaped the cell without our `stop()` helper, so `run.json` still says `started`.
- **Not a server failure.** The server came up and shut down cleanly when the kernel ended ("Application shutdown complete." in `boot0.log`).

### 9.2 Readings

- **R0 fires.** The run status is `started`, and 0 training pairs were kept. No other row is read.
- **Stage reached.** Stage 1 finished. In D-006 terms, this kernel stopped at **boot 0, before pair building**. No base generation ran, no pair was built, no training ran, no boot 1 started, and no request was evaluated.
- **C-024.** Unread, not refuted.
- **Blind prediction.** It gave R0 25%. R0 came, but from a defect in our own code, not from the training or memory risks the prediction had in mind.

### 9.3 The two points flagged before the push

1. **BF16 lookup: no fallback [V].** The first explicit path hit: `/kaggle/input/models/google/gemma-4/transformers/gemma-4-e4b-it-qat-q4_0-unquantized/2` (`env.json` `bf16_dir`). Training would have used the BF16 parent. Nothing was walked under the competition mount.
2. **Memory, feasibility 3: not the cause, and still unmeasured [V for "not the cause"].** The failure is a Python name error before any training process started. The kernel reported 4 x 22,563 MiB GPUs and 184.4 GiB of free host RAM. The boot-0 E4B server reserved its usual KV pool. Training memory remains on paper.

### 9.4 The one cause and the fix (proposed, not applied)

The fix touches two lines in the capture cell of `notebooks/exp054_copylora/copy_lora.py`, and nothing else:

- `import http.server` becomes an import of `BaseHTTPRequestHandler` from `http.server` by name, which binds no global `http`;
- the capture handler's base class, `http.server.BaseHTTPRequestHandler`, becomes `BaseHTTPRequestHandler`.

A rename of the helper would work equally well. Either way, no reading, endpoint, cap, parameter or input changes. The notebook would be rebuilt with the section 6 command, its `kernel-metadata.json` kept unchanged, and pushed as version 2.

- **Risk.** It is [I]. The cells after boot 0 have never run in a kernel: the capture, the request phase, pair building, training under torchrun and boot 1. A v2 can still stop at a later defect; R0 would then fire again.
- **Cost of a v2.** As section 2.6: expected 0.75 to 0.90 L4x4-h, worst at most 0.98 h. The 3,400 s cap is unchanged.

### 9.5 GPU spent

**0.140 L4x4-h**: the kernel-log span, 502.3 s from kernel start to the last entry, measured as for EXP-047. This is against the 0.98 h worst case and the about 1.2 h share.

### 9.6 Two deviations from section 2.1, logged after the fact (the readings are untouched)

1. **The eval set was not balanced.** Section 2.1 says it is 40/40/40 over K1/K2/K3; the kernel's held-out pool gave 45/31/44 (K2 short). The 40/40/40 balance held only on this machine's 3.13 stdlib. No reading depends on the balance; by-kind rates are secondary (E4).
2. **The `peft` package is present in the kernel** (0.19.1, `env.json`). EXP-048's feasibility point 2 said "no `peft`" of the wheelhouse, and that stays true there. The hand-written LoRA does not use `peft`, so nothing changes. The harness-stack note is updated.
