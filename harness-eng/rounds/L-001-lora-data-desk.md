# L-001: LoRA stage 2 desk check (data and training feasibility), zero GPU

Written 2026-11-20, while R-013 (serving canary) and the R-014 smokes ran. Counts only: no trace, task, repo or code
text. The user's rulings that apply here (2026-11-20):
- LoRA is allowed for both models;
- training data may be public, synthetic or ours, as long as every source is recorded;
- making the data public is deferred ("we can worry later"), so trajectories stay out of git and any release
  meanwhile (plan.md:52);
- large files go under `/data/mmyatmau/gemma4-lora/`, and a parent-weight download is allowed only if needed.

## 1. What our own trajectories can give

Every task result under `runs/`, split by the eval cohort `cdev2-79`:

| Model | Draws on cdev2-79 | Resolved, traced | Distinct tasks resolved | Draws outside cdev2-79 |
|---|---|---|---|---|
| 31B | 1145 | 448 | 40 | 3 |
| E4B | 5134 | 541 | 29 | 3 |

- Nearly all of it is on the eval cohort. Training on it and then measuring on cdev2-79 would measure memory,
  not skill.
- The 129 tasks split as cdev2-79 (79) plus 50 others. 41 of the 50 are gradeable (C-003: reference passes, empty
  fails). 22 of those 41 are in the held-out cohorts `cheld-16`/`cheld2-22`, which leaves **19 clean gradeable
  tasks** for new trajectories. That is too few for an adapter on its own.
- All 129 tasks come from 4 public repos. The hidden set is private repos, so trajectory data teaches process,
  not repo content, and the eval must be on tasks the adapter never saw.
- Traces (schema 9) keep the system prompt, the task prompt, and per model turn the thought text, tool calls with
  arguments, and observations. A conversation can be rebuilt turn by turn. Over the 316 31B base traces
  (R-008/R-011), each step carries exactly one tool call. The step kinds are 7090 thinking-plus-call, 211 final, 138
  without an event type, 27 text, and 21 continuation nudges.
- **Compaction is on.** An earlier draft of this file said it was off; that was wrong. `tools/cluster_eval.py:37`
  sets ADK events compaction to interval 15, threshold 14336 tokens, retention 5 and overlap 2, as the official
  harness does. The recorded `prompt_tokens` falls from about 14.5k to 2.7-5k at that point, and the compaction
  summary is not in the trace. Turns after a compaction therefore cannot be rebuilt exactly.
- **Fidelity check (6 traces of R-011-31b-base-te-d3, 31B tokenizer, the served template, the dumped tool
  schema).**
  - Re-rendering each call's prefix with the earlier `reasoning_content` gives the recorded `prompt_tokens` to within
    16 tokens. The gap is 16 at call 1 and shrinks by 2 per call.
  - Without the thoughts it falls 100-3000 tokens short.
  - So ADK sends the thoughts back (`lite_llm.py` sets `reasoning_content`), and the served template keeps them for
    the current model turn. It drops them for turns before the last user message (a nudge).
  - Two of the 6 traces have a single larger gap (one call +1392, one drift to -5).
- **Observation encoding.** ADK sends tool results as `json.dumps(..., ensure_ascii=False)`. The trace stores the
  default ASCII-escaped dump, which differs in 41 of 1815 observations in R-008 d1. Re-serializing them closes
  part of the gap.
- **`tools/lora/trace_to_sft.py` (D2 converter).** It writes chat-format samples under
  `/data/mmyatmau/gemma4-lora/data/` only and prints counts only.
  - It keeps a resolved trace's faithful prefix: from the start up to the `submit_patch` response (`complete`), or
    cut before the first nudge or the first LLM call whose re-rendered prefix is more than 64 tokens from the
    recorded count. A recorded drop of more than 3000 tokens is labelled `compaction`, anything else `mismatch`.
  - Smoke over R-008 d1 + R-011 d3 (31B base, all of cdev2-79, no fold yet):

    | Outcome | Draws |
    |---|---|
    | Resolved | 58 |
    | Kept, complete | 36 |
    | Kept, cut at compaction | 17 |
    | Kept, cut at mismatch | 2 |
    | Kept, no submit | 1 |
    | Too short (fewer than 3 calls) | 2 |

  - That is 802 LLM calls over 32 tasks. The median worst prefix gap among kept samples is 16 tokens.
  - Before the re-serialization fix, 30 samples were complete.
- **Open for the trainer.** The samples carry the 31B's system prompt. The E4B adapter must be trained under the
  frozen E4B config's system prompt and tool list, so the trainer swaps the system message and renders with the
  E4B tokenizer. That is a distribution shift to note in the round that trains on it.

## 2. Format and weights (checked in `env/harness.sif`)

- The served `chat_template.jinja` renders the system prompt, tool declarations, `<|channel>thought`, `<|tool_call>`
  and `<|tool_response>` in Gemma 4's native format through `apply_chat_template(..., tools=..., enable_thinking=True)`
  in transformers 5.13.1. Training samples can therefore be rendered with the same template vLLM serves.
- Both served checkpoints are compressed-tensors `pack-quantized`, int4 symmetric, group size 32, with 250 (E4B) and
  192 (31B) modules left unquantized. On disk they are 11 GB (E4B) and 22 GB (31B).
- The image also has compressed_tensors 0.15.0.1 and accelerate 1.14.0, so transformers can load the packed
  checkpoint and dequantize it to bf16 (`run_compressed=False`) without any install. Weights are int32-packed with
  one bf16 scale per 32 inputs (E4B layer 0: q_proj packed [2048, 320], scale [2048, 80]). bitsandbytes 0.46.1 is
  present but built without GPU support. datasets and trl are absent and not needed.
- torch 2.10.0+cu128 and transformers 5.13.1 are in the image; peft is not (no install was asked for). A
  plain-torch LoRA (A/B matrices on the target linears, PEFT-format save) is enough. R-013's
  `make_lora_canary.py` already writes the PEFT layout the harness loads.
- `/data/mmyatmau/gemma4-lora` is visible inside apptainer with no extra bind (1.6 TB free).
- `tools/lora/tool_schema.py` dumps the six tool declarations exactly as served to
  `/data/mmyatmau/gemma4-lora/schema/tools.json`. It builds them through `swegemma.tools.create_tools`, then ADK
  `FunctionTool`, then the LiteLlm converter.
- Tool responses reach the template as JSON strings and render as `response:<name>{value:<|"|>...<|"|>}`.

## 3. Feasibility per model (inference, to be measured)

- **E4B.** Training on the served int4 weights dequantized to bf16 should fit one 48 GB Ada with gradient
  checkpointing at 16-32k tokens. A 24 GB Turing is tight. Training on exactly the served weights means no parent
  download.
- **31B.** About 62 GB dequantized does not fit one 48 GB Ada. It needs either on-the-fly dequantization per layer
  (QLoRA style, custom code) or two GPUs with layer sharding. The R-013 decode-ratio reading decides first whether
  a 31B adapter fits the 11 h budget at all.

## 4. Data options, ranked

| # | Source | Size | Contamination | Targets | Needs |
|---|---|---|---|---|---|
| D1 | Synthetic tool-format data from public code: a `read_file` output, then an `edit_file` whose `old_string` is copied exactly. Includes multi-line, indentation and non-contiguous cases. | unlimited | none | E4B copy fidelity (46.5% of task-draws have a failed edit; the R-014 applier attacks the same failure without training) | a generator; public code already in the image (stdlib, site-packages), license recorded per file |
| D2 | 31B → E4B distillation from our resolved 31B trajectories, with the cdev2-79 tasks split into two folds; train on fold A, evaluate on fold B | 448 draws over 40 tasks (about 220 per fold) | none across folds; the LB set is unaffected | E4B process (locate, edit, submit), with the teacher in the same tool format | conversion script; 2 adapters for a full cross-fold reading |
| D3 | Public SWE agent-trajectory datasets | thousands | none on our repos | process | a download (the user's yes per dataset); conversion to our 6-tool schema |
| D4 | New trajectories on the 19 clean tasks | about 19 × draws | none | small top-up for D2 | GPU-h |

### D2 folds and fold-A inventory (2026-11-20)

- `tools/lora/make_folds.py` split cdev2-79 into `cohorts/lfold-a.txt` (39 ids, train) and `cohorts/lfold-b.txt`
  (40 ids, evaluate).
  - The split is per repo, in snake order over (E4B base resolves over R-011 d1-d8, 31B base resolves over R-008
    d1/d2 and R-011 d3/d4, sha1 of the id).
  - It was fixed before any training sample was looked at.

  | Fold | Tasks | fastapi / rich | E4B base resolves | E4B tasks ever solved | 31B base resolves | 31B tasks ever solved |
  |---|---|---|---|---|---|---|
  | A | 39 | 22 / 17 | 24 | 8 | 53 | 18 |
  | B | 40 | 22 / 18 | 32 | 10 | 60 | 18 |

  - The E4B base solves only 4.0 fold-B tasks per draw, so an adapter reading on fold B needs many draws. The
    round that trains on fold A sets its draw count from this.
- `trace_to_sft.py` now also drops multi-agent traces (more than one agent author).
- **Fold-A inventory.** I ran it over all 31 completed 31B run dirs, excluding gold/empty controls and the
  R-013/R-014 dirs.

  | Outcome | Draws |
  |---|---|
  | Kept, complete | 140 |
  | Kept, cut at compaction | 94 |
  | Kept, cut at a nudge | 16 |
  | Kept, no submit | 2 |
  | Kept, cut at mismatch | 2 |
  | Unresolved | 397 |
  | Multi-agent (dropped) | 1 |

  - **Totals:** 254 samples, 3669 LLM calls, 21 tasks, from 16 arms.
  - **Calls by tool:**

    | Tool | Calls |
    |---|---|
    | `run_command` | 1780 |
    | `read_file` | 1061 |
    | `edit_file` | 558 |
    | `write_file` | 138 |
    | `submit_patch` | 140 |
    | `get_status` | 1 |

  - **Samples per task are skewed:** min 3, median 13, max 29. The trainer caps samples per task.
  - The 6 samples from `R-003-31b-nothoughts` were made without thinking and are filtered out at training.
- Output: `/data/mmyatmau/gemma4-lora/data/d2/31b-all-lfold-a.jsonl`, outside git.

Proposed first adapter: E4B, D1 plus D2 fold A, evaluated on fold-B tasks against the base on the same tasks. It
needs no download, keeps the held-out cohorts unspent and, if R-014's applier is kept, is trained on the frozen
config. The 31B waits for R-013 reading 4.
