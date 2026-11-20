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
  arguments, and observations. A conversation can be rebuilt turn by turn. Compacted turns need care, because the
  model saw a shortened prompt there.

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

Proposed first adapter: E4B, D1 plus D2 fold A, evaluated on fold-B tasks against the base on the same tasks. It
needs no download, keeps the held-out cohorts unspent and, if R-014's applier is kept, is trained on the frozen
config. The 31B waits for R-013 reading 4.
