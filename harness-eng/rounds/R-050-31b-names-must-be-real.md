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
