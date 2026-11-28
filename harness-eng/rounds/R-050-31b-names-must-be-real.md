# R-050: 31B, check names before use and keep the issue's names (pre-registration)

Written 2026-11-28, before any job of this round is submitted. Counts only.
User question (2026-11-28): the models lack knowledge of libraries; supply it in context without bloating it.

## Why

- **Size of the target, from the graded test output of failing patches (no GPU).** kfctl x8, 295 failing patches: 21%
  end in an import, attribute, name or type error (ImportError 10%, AttributeError 7%, ModuleNotFoundError 5%,
  TypeError 3%); 42% in an assertion only; 5% in a syntax error. E4B rcheck x8, 536 failing patches: 26%, 43%, 14%.
- A pre-written library pack cannot cover private repositories. The sandbox holds the real code, so the knowledge
  can be fetched on demand in one short command, which costs one call and a few lines of context.
- Skills tested so far were procedures (outline, locate, line-edit, change-count and its variants). None supplied
  knowledge of what exists. A skill script is avoided here: skill scripts are reported not to see the repository on
  the official scorer (R-041).

## Arm

`trees/31b-kf-names` = `trees/31b-kf-ctl` plus one prompt section of two bullets: check an unseen name with one
introspection command before using it; create anything the issue names under exactly that name and path.
Validator: the two known errors only.

## Readings (written before any job runs)

1. Served check per draw: 79 rows, all served.
2. Draw-1 kill gate: 25 or more empty patches or mean task wall above 452 s.
3. Decision, `R-050-31b-names-d1..d4` against kfctl x8 (`tools/paired_boot.py`): extend to 8 draws at +1.0 or more;
   promote at 8 draws with +1.5 or more, CI lower bound above -0.5 and wall ratio 1.06 or less; harm at -1.5.
4. Mechanism: share of failing patches whose test output ends in an import, attribute, name or type error (kfctl
   21%); introspection commands per task; tool calls per task; call-cap and time-cap tasks.

**Blind guess.** The error share falls by 5 points or more: 35%. Extension: 15%. Promote: 7%.

## Result, four draws (read 2026-11-28 09:20 UTC)

- Solved 32, 30, 32, 33: mean 31.75 against kfctl 30.38. **Paired +1.38 solves per draw, 90% CI -0.75..+3.50.**
  Empty patches 12, 9, 9, 15 (kfctl 6-15). Mean wall 368, 374, 382, 393 s (kfctl 385.6 s).
- **Reading 3: the extension bar (+1.0) is met. Draws 5-8 are queued.** Promotion needs +1.5 at 8 draws with the CI
  lower bound above -0.5.
- **Mechanism did not move.** Failing patches ending in an import, attribute, name or type error: 22.2% (144
  failing patches) against 21.0%. Commands using introspection: 0.38 per task, in 14% of tasks (kfctl 0.27, 10%).
  Tool calls per task 24.6 against 24.6. So if the gain is real it does not come from the lookup command; the
  second bullet (create what the issue names under exactly that name) is the other candidate.

## Eight-draw reading (2026-11-28 12:20 UTC)

Draws 5-8: 32, 28, 29, 30. All eight: 32, 30, 32, 33, 32, 28, 29, 30 = 30.75 against 30.38 for the control.
Paired difference +0.38 solves per draw, 90% interval -1.50 to +2.25. Mean task wall 364-400 s (control 385.6 s).
The promotion bar (+1.5 with the lower bound above -0.5) is not met: **not kept**. The +1.38 at four draws shrank
to +0.38 at eight, which is what draw noise of this size does; the section costs nothing in time and is neutral.
