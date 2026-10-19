id: EXP-004-regrade-shim (zero-GPU re-grade follow-up to EXP-003-public-budget)        date: 2026-10-19        owner: M4
hypothesis: EXP-003's measured dev-48 resolve-rate loss vs E0 (18.75% vs 22.9%) is at least partly a
        grading-sandbox artifact, not a real fix-quality difference: EXP-003's tighter 28-call budget
        gives the agent less room to reach the `ModuleNotFoundError: inline_snapshot`/`dirty_equals`
        error and self-vendor the known-gap stub (`submission/prompts/swe_coder.md` "Known sandbox
        gaps") before its budget runs out, so some EXP-003 "losses" may really be fixes the sandbox
        never let the agent finish proving. Zero GPU cost: re-grade (not re-run) the two runs' own
        already-captured final patches with the two stub packages (`tools/compat_shims/*`) present,
        gated per task on whether that task's own extracted test files import them.
single variable changed: n/a -- this is a re-grade of already-collected patches, not a new agent run. The
        only change between a task's original scored result and its regrade result is whether
        `inline_snapshot`/`dirty_equals` were importable from `/workspace` during that task's pytest run.
cohort: the same dev-48 cohort as E0 (EXP-001-baseline) and EXP-003-public-budget, both runs' full 48
        tasks, replaying each run's own `patches/*.patch` (the agent's actual final submission, not gold).
        GPU-h used: 0 (CPU-only kernel, `enable_gpu: false`, no model/vLLM/litellm import).
config: `tools/regrade_patches.py` -- subclasses `swegemma.evaluate.Evaluator`, overrides
        `_run_agent_sandbox` to hand back the run's stored patch text instead of calling a model (same
        technique as `tools/gold_control.py`'s `GoldEvaluator`, with the agent's own patch in place of
        gold), and monkeypatches `swegemma.harness.verification.extract_snapshot` to additionally copy
        `tools/compat_shims/{inline_snapshot,dirty_equals}` into `/workspace` right after snapshot
        extraction, per task, only when that task's own extracted test files actually import the
        package (grep probe) -- so a task that never needed the shim grades identically to an
        unpatched run. Runs with `sandbox='subprocess'` (what Kaggle CPU kernels actually use; the
        docker-only `install_test_dependencies` codepath that `gold_control.py` depends on is a no-op
        under subprocess, confirmed in `container_setup.py`), matching the sandbox mode both E0's and
        EXP-003's original scored runs used.
        kernel: rainm4/gemma4-exp004-regrade-shim (notebooks/regrade_shim_dev48/), v1 pushed 2026-10-19.
bug found and fixed (v1 -> v2, before trusting any number): v1's shim hook pre-seeded the two stub files
        into `/workspace` *before* the agent's own patch was applied (`extract_snapshot` runs ahead of
        `apply_patch_in_container` in `verification.verify_task`). For any patch that had itself
        self-vendored the same file (exactly the class of patch this experiment most needed to read),
        `git apply` then failed outright -- `error: inline_snapshot/__init__.py: already exists in
        working directory` -- so that patch was never applied or graded at all, producing a false
        `resolved=False, exit=1` regardless of the patch's actual correctness. This deflated v1's raw
        counts (E0 8/48, EXP-003 10/48, both clearly wrong and lower than the runs' own original scored
        numbers) and fully or partially corrupted 3 of the 5 originally-contested tasks. Fix: track the
        currently-graded task's own patch text in a module global set right before each
        `evaluate_task` call, and skip pre-seeding a given shim package for that task if the patch's own
        diff already adds `<pkg>/__init__.py` (`_patch_adds_file`, checked via the diff's own
        `+++ b/<path>` / `diff --git a/<path> b/<path>` header lines) -- the file then comes from
        `git apply` itself, never colliding with a pre-seeded copy. v2 pushed and rerun, same kernel id
        (rainm4/gemma4-exp004-regrade-shim), version 2, CPU-only, COMPLETE 2026-10-19.
results (v2, clean -- zero `git apply` "already exists" errors in either run's 96 regrade rows,
        confirmed by grepping every row's `error` field):
        **E0 regrade: 11/48 = 22.9% (Wilson 95% CI 13.3-36.5%) -- exactly matches E0's own original
        scored result, zero flips.** No E0 task's resolved/not-resolved status changed at all: none of
        E0's patches needed the shim that it didn't already have (E0 ran under the old 45-call budget
        and evidently always had enough slack to self-vendor when it hit the gap). This is also the
        methodology's own sanity check: the regrade tooling does not inflate or distort results when
        there is nothing to recover.
        **EXP-003 regrade: 12/48 = 25.0% (Wilson 95% CI 14.9-38.8%) -- up from EXP-003's original scored
        9/48 = 18.75%, via exactly 3 tasks flipping False -> True: fastapi_14459, fastapi_14360,
        fastapi_14297.** All 3 were corrected from false losses once the shim gap stopped eating the
        agent's remaining budget before it could resubmit.
        **The 5 originally-contested tasks (E0 resolved, EXP-003 did not, per EXP-003-public-budget.md),
        re-read clean:**
        | task | E0 (regrade) | EXP-003 (regrade) | reading |
        |---|---|---|---|
        | fastapi_13207 | True | False | genuine loss, holds up |
        | fastapi_14873 | True | False | genuine loss, holds up |
        | fastapi_14297 | True | **True** | **confirms the hypothesis: this was the grading-sandbox artifact** |
        | fastapi_13537 | True | False | genuine loss, holds up |
        | rich_3676 | True | False | genuine loss, holds up -- EXP-003-public-budget.md already identified this one as stopping at exactly the new 28-call cap (vs. 30 calls to resolve under E0's old 45-call budget); this regrade confirms it is not also a shim artifact |
        fastapi_14297 is also the task EXP-003-public-budget.md flagged as unexplained ("only
        fastapi_14297 stopped earlier, at 26 [calls], for a different reason not yet investigated") --
        now explained: it hit the `ModuleNotFoundError` gap with only ~2 calls of budget left and ran
        out before it could finish re-vendoring and resubmitting.
        fastapi_14459 and fastapi_14360 were not in the original 5-task "lost" list (both E0 and EXP-003
        originally failed them outright, for unrelated reasons) -- they surface only in this regrade,
        as two additional cases where EXP-003's own patch logic was already correct but the sandbox gap
        alone cost the resolve; E0's patches for these two tasks do not flip, confirming they are not
        shim-related for E0.
decision: **the original EXP-003-public-budget.md "flat-to-slightly-worse, not a win" verdict rested in
        part on a grading-sandbox artifact, not purely on the 45->28 call-count cut.** Once the
        inline_snapshot/dirty_equals gap is equalized between the two runs, EXP-003's config
        (12/48 = 25.0%) is a hair *above* E0 (11/48 = 22.9%) rather than below it -- though at n=48 this
        is a 1-task difference, well inside both Wilson CIs, and not a basis for adopting EXP-003's
        bundle outright. The one real, mechanistic, non-shim loss this regrade confirms is rich_3676
        (28-call cap, already documented) -- the call-count cut's cost is real but was previously
        overstated because 1 of the 5 "losses" attributed to it (fastapi_14297) was actually the shim
        artifact. Net effect on EXP-003-public-budget.md's own decision: the specific claim "the
        call-count cut (45->28) is actively costing resolves" still holds for rich_3676, but the
        implied broader damage (5 lost tasks) should be read as closer to 4 genuine losses offset by 3
        shim-recovered gains once corrected for this artifact -- materially closer to parity with E0
        than the original write-up suggested. Do not read this as "EXP-003 wins": it is "the EXP-003
        vs. E0 comparison in EXP-003-public-budget.md was measured on an uneven footing, and the actual
        gap is smaller (or possibly reversed) once that unevenness is removed."
        This also strengthens the project's existing prompt-side mitigation (`swe_coder.md` "Known
        sandbox gaps" section): the gap is real, the self-vendoring instruction works when the agent has
        budget left to reach it, and tighter call budgets measurably interact with it. Any future
        budget-shape experiment (e.g. the pre-registered EXP-003c isolating the call-count variable)
        should re-grade its own patches with this same shim-equalization step before comparing resolve
        rates to E0, or risk re-introducing this exact confound.
follow-ups:
  1. Not done here, still open: EXP-003c (isolate the call-count variable alone, call cap raised back
     toward E0's 45) remains the right next step to cleanly separate the call-count cost from the other
     bundled budget-shape changes -- this regrade does not substitute for that, it only removes a
     confound from the comparison that already exists.
  2. The two newly-identified fastapi_14459/fastapi_14360 shim-recovered gains were not previously
     flagged anywhere (they are not in EXP-003-public-budget.md's 5-lost/3-gained per-task diff since
     both runs originally failed them) -- worth a quick trace read if anyone later wants to confirm the
     mechanism (self-vendor-then-ModuleNotFoundError-again pattern) rather than assuming it from the
     aggregate flip alone; not done in this pass.
  3. `tools/regrade_patches.py`'s shim-pre-seeding ordering bug (fixed here via `_patch_adds_file`) is a
     reusable lesson for any future "replay an already-captured patch under a modified sandbox"
     tooling: always check whether the stored patch's own diff already creates the path you're about to
     inject, before injecting it, or `git apply` will reject the patch outright instead of merely
     grading it differently.
