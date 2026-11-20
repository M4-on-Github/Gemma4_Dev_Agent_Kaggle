# R-013: LoRA serving canary, 31B and E4B (stage 1 of the LoRA track)

Written 2026-11-20, before any R-013 job. On 2026-11-20 the user ruled LoRA allowed. They asked for both models in
parallel and approved this canary ("Yes, run it"). It needs no install and no download. pleiades-1-10 is lent for
the E4B jobs, provided nobody else has jobs on it at submit time.

## Why

R-012's review left the LoRA track at stage 0 with no stage 1 data. No 31B adapter has ever been served on this
cluster. For the E4B, adapters loaded on the Kaggle L4x4 path (EXP-047/054/058), but never here on Turing.
Before any data or training work, each model needs four answers:
- Does the harness's own server mount an adapter of the training shape?
- Is the adapter applied?
- Does every agent call go through it?
- What does it cost in decode speed?

The time budget decides the 31B. Its Kaggle projection is 10.04 h against the 11.0 h gate, so decode may lose at
most 1 - 10.04/11.0 = 8.7%. That assumes wall time scales with decode; it is an upper bound on the allowed loss.
Earlier adapters cost 17-29% (EXP-047, EXP-054, kg-755677). The E4B projects to 2.98 h, so it can lose up to 73%.

## Facts checked for this round

- **Allowed base models.** The scorer allows exactly four: the 31B, 12B, E4B and E2B `-it-qat-w4a16-ct`, one per
  submission (`data/raw/HARNESS_README.md` §3.1-3.2, [V]). The bf16 names are registered for local CLI use only.
  An adapter is a PEFT LoRA directory under `adapters/<name>/`, rank at most 128, inside the 3 GiB size limit.
  The competition rules allow public, free external models (competition-brief), so a bf16 parent could be used for
  training only; the shipped tree still declares the w4a16 model.
- **Server flags.** `adk_submission/server.py` (in the image, around lines 759-795) passes `--enable-lora` only
  when adapters are mounted. It also sets `--max-loras` to the number mounted and `--max-lora-rank` to the
  largest rank rounded up to vLLM's bucket (4 -> 8, 16 -> 16). The 8 and 128 in `cluster_eval.py`'s `VllmConfig` are
  overridden.
- **Module layout (served headers).**

  | Model | Layers | Projections | Missing |
  |---|---|---|---|
  | 31B | 60 | q/k/o/gate/up/down 60 each | `v_proj` only on 50 layers |
  | E4B | 42 | q/o/gate/up/down 42 each | `k_proj`/`v_proj` only on 24 layers (KV sharing) |

  The E4B also has `per_layer_input_gate` and `per_layer_projection`; they are not LoRA targets here.

## Adapters and trees (gitignored: `adapters/`, `*.safetensors`)

`tools/make_lora_canary.py <served dir> <out>` builds both adapters from the served header with seed 0. For each
model:
- **`full_zero`.** Rank 16 on every q/k/v/o/gate/up/down projection the checkpoint has, with lora_B = 0, so it is
  the training shape. 31B: 410 modules, 122.4M parameters, 233.5 MiB. E4B: 258 modules, 34.9M parameters,
  66.5 MiB.
- **`loud_l0`.** The organisers' sample layout: rank 4, q_proj and o_proj of layer 0, with lora_B ~ N(0, 0.02).

Each sits alone in its own root (`adapters/canary-<model>-{full,loud}/adapters/<name>`), so each boot mounts one
adapter, as a shipped tree would.

Agent-path trees: `adapters/trees/{31b,e4b}-full0`. Each is the base tree (`trees/31b-base`, `trees/e4b-base`) plus
`adapters/full_zero` and one added line, `adapter: full_zero`, after `model:` in `agent.yaml`. The validator gives
both the base profile (the cluster trees' packing-gate error and `timeout_seconds` warning) plus the expected
"shipping an adapter" warning.

## Jobs

Each job asks for 1 GPU, 4 CPUs and 64G. Run `squeue -w pleiades-1-10` before the E4B submits.

| Job | Command (from `harness-eng/`) |
|---|---|
| 31B probe (Ada) | `sbatch -J heng_31b slurm/lora_canary.sbatch R-013-31b-probe gemma-4-31b-it-qat-w4a16-ct adapters/canary-31b-full adapters/canary-31b-loud` |
| 31B agent path (Ada) | `sbatch -J heng_31b slurm/eval.sbatch R-013-31b-full0-c4 adapters/trees/31b-full0 cohorts/cdev2-79.txt --limit 4 --concurrency 4 --py313 env/py313-scorer/bin/python3.13 --task-envs env/taskenvs` |
| E4B probe (Turing) | `sbatch -J heng_e4b --constraint=QUADRORTX6000 -w pleiades-1-10 slurm/lora_canary.sbatch R-013-e4b-probe gemma-4-e4b-it-qat-w4a16-ct adapters/canary-e4b-full adapters/canary-e4b-loud` |
| E4B agent path (Turing) | `sbatch -J heng_e4b --constraint=QUADRORTX6000 -w pleiades-1-10 slurm/eval.sbatch R-013-e4b-full0-tu5-c4 adapters/trees/e4b-full0 cohorts/cdev2-79.txt --limit 4 --concurrency 4 --py313 env/py313-scorer/bin/python3.13 --task-envs env/taskenvs --time-scale 5.0` |

- **The probe.** `tools/lora_canary.py` runs inside `slurm/lora_canary.sbatch`, which uses `eval.sbatch`'s
  container setup, including the Turing firmware bind and the attention patch. It boots once per root and runs
  no task. The prompts are two sentences in our own words, plus a ~12k-token repeat of them for prefill.
- **The agent path.** The first 4 cdev2-79 tasks, one wave at concurrency 4. The resolve count is reported, not
  gated.
- **Cost.** About 0.3 GPU-h per probe job (two boots) and about 0.25 GPU-h per agent-path job. That is about
  0.55 Ada GPU-h and 0.55 Turing GPU-h.

## Readings (written before any job)

1. **Flags.** The probe's command line has `--enable-lora --max-loras 1`, with `--max-lora-rank 16` for
   `full_zero` and 8 for `loud_l0`. `/v1/models` lists the adapter name. Pass/fail.
2. **Applied.**
   - Floor: the base name's repeat, `mean_abs_delta` against the first base pass.
   - `full_zero` passes if its `mean_abs_delta` is at most max(1e-3, 2 x floor).
   - `loud_l0` passes if its `mean_abs_delta` exceeds both 0.01 and 10 x floor.

   Both must pass. If `loud_l0` does not move, the adapter is not applied.
3. **Routing.** In the agent-path job, every LLM request in the 4 traces names `full_zero` as its model, where
   the trace records a model name. There are 0 HTTP or adapter errors in the job log and 0 task exceptions.
   Pass/fail.
4. **Decode cost.** `full_zero` tok/s at 4 streams, over the mean of its two passes, divided by the base's mean from
   the same boot. Reported at 1 stream too, with the 12k prefill ratio.
   - 31B passes at a ratio of 0.913 or more. The Kaggle projection is then at most 11.0 h, assuming all wall time
     is decode.
   - E4B passes at 0.27 or more (2.98 h / 0.27 = 11.0 h).

   This lane runs TP1 on one GPU; Kaggle serves TP4 on 4 x L4. So a pass here is necessary, not sufficient, and
   the Kaggle number needs its own probe (stage S6).

## Decisions (fixed before results)

- **Readings 1-3 pass for a model.** Its adapter path works on the cluster, and that model's LoRA track moves to
  data (S2) and training (S3).
- **Reading 1, 2 or 3 fails.** Stop that model's track and diagnose; no training compute is spent on it.
- **31B reading 4 fails.**
  - First, one more probe boot with an attention-only adapter (q/k/v/o, rank 16), at about 0.15 GPU-h, to see
    whether fewer modules recover the speed.
  - If it still fails, 31B LoRA needs a decision from the user: a recorded budget override (projection between
    11 and 12 h) or a lower time cap. It is not trained before that.
- **E4B reading 4 fails.** The E4B's tool-call cap binds before its time does (R-012 follow-up). The E4B still
  goes ahead, and the cost is reported against its 240 s per task of headroom.

Nothing here ships; the projected Kaggle time for an adapter tree is worked out in S6. No competition text goes
into the probes, and this file holds counts only.
