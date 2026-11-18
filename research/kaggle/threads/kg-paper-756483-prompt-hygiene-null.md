---
id: kg-paper-756483-prompt-hygiene-null
topic_id: 756483
title: "Pre-registration hash: prompt hygiene rules vs baseline on 233 tasks"
author: yu_kuo14
author_role: participant (paper track); pre-registration posted as a topic
credibility: [M] participant, with a pre-registered rule and three gradings reported in the thread; grading defects disclosed by the author; the eval-kit dataset is promised public at the deadline, not yet readable
topics: [paper, prompt, grading, noise]
first_seen: 2026-11-17
last_checked: 2026-11-17
---

# 756483: prompt hygiene rule H vs baseline v6, pre-registered null

Topic posted 2026-11-06 14:19 UTC. Three comments returned (CLI, read 2026-11-17). Opening body not returned.

## Result as first graded (comment 3551415, 2026-11-07 08:56 UTC)

- Primary outcome (`cap_no_edit`): v6 72/466 (15.5%) vs H 72/466 (15.5%), relative change 0%. Pass required at
  least -30%. The two halves went opposite ways: practice 24 vs 35, validation 48 vs 37 (v6 vs H).
- Guard 1, paired solves H - v6: 127 vs 124, 12 vs 15 discordant pairs, **-3** (threshold >= -5), two-sided sign
  test **p = 0.70**. Holds.
- Guard 2, mean wall seconds per attempt: 307.5 vs 308.0 (+0.2%). Holds.
- Decision under the frozen rule: H dropped; v6 stays the baseline.
- The first validation pass (158 tasks x 2 seeds) was invalid for both arms: rebuilt snapshots lacked `.git`, which
  the official harness needs for its diff baseline (500 "not a git repository" tool errors in one arm-seed). The
  validation half was rerun under the unchanged rule; the Colab runner differs from the pre-registered hash.

## Addendum after grading defects (comment 3552920, 2026-11-10 16:22 UTC)

- Router defect: on Colab, 18 of 34 validation repositories (89 of 158 tasks) ran without the dependency router
  (Debian's `sitecustomize.py` shadowed it). Fixed; rerun.
- Preinstalled-package defect: in 16 repositories a src-layout package also installed in the image was tested
  instead of the workspace, so **12 attempts with an empty patch were recorded as resolved**. Fixed; rerun of 69 tasks.
  An empty-patch control now runs beside the gold control (0/158 in four runtimes).
- After re-run 1: paired solves +5 (26 vs 21, p = 0.56). After re-run 2 (every validation row from the fixed
  runtime): cap_no_edit 70 vs 71 (+1.4%); **paired solves +4 (33 vs 29, p = 0.70)**; mean wall 291.0 vs 285.5 s.
- "The decision under the frozen rule is the same each time: H is dropped, v6 stays our baseline."

## Deviations disclosed

- Second addendum named a Colab A100 80 GB; none was available, so the 69 tasks ran on RTX PRO 6000 96 GB VMs.
  Both arms of a seed shared a VM, so the pairing is unaffected; absolute wall times are not comparable across halves.

## Credibility notes

- Pre-registration with a hash, an explicit primary outcome and guards, and disclosed deviations: stronger than most
  topics in this forum.
- Still [M]: the outcome is a null with n = 466 pairs and p = 0.70; it does not show H is harmful, only that the
  primary endpoint did not move.
- The per-attempt rows and addenda are "in the eval-kit dataset, which becomes public at the deadline". Not
  downloadable here at the time of the read.

## Relevance to our submission

Nothing ships from H. The useful lessons for us are the grading defects (a shadowed router and empty patches
counted as resolved), which our own BASE and gold controls already check (C-022, EXP-036), and the reminder that
prompt-rule variants without a paired arm are not evidence (C-005, C-009).
