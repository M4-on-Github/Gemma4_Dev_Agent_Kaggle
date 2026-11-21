# Skill-script sizing: a 31B locate script and an E4B tolerant edit applier (zero GPU)

Written 2026-11-21. An analysis of existing traces only: no GPU, no new runs. It holds counts, shares and seconds;
no trace content. The user asked whether ADK skill scripts (`run_skill_script`, verified on Kaggle in EXP-056/057)
could take over the steps where the agents fail. This file sizes the two candidates before either is built.

## Method

- **Time per call.** The call's own model time, plus its tool time, plus the model time of any tool-less agent
  steps since the previous call. These add up to the observation clock.
- **Edit attempt.** `edit_file` or `write_file` on a relative source path that is not under /tmp and is not a test
  file. A root-level repro, test or debug write counts as scratch.
- **Not-found edit failures** are classified against the latest successful `read_file` of the same path:
  - WS: matches after normalizing whitespace and line endings.
  - PREFIX: matches after stripping copied line numbers.
  - NEAR: difflib ratio >= 0.9.
  - AMBIG: matches in more than one place.
  - ABSENT: none of these.
  - stale: one of the agent's own edits landed on that path after the read.

## A. 31B: the calls before the first edit attempt

Runs: the 5 base draws (R-008 d1-d2, R-011 d3-d4, R-014 d5), 395 task-draws over 79 tasks. Values are per-draw means.

| Group | n | Calls | Seconds | Search calls / s | Read calls / s |
|---|---|---|---|---|---|
| all | 395 | 13.9 | 198 | 5.6 / 73 | 6.6 / 74 |
| resolved | 145 | 10.0 | 136 | 3.3 / 40 | 4.7 / 49 |
| noisy-fail | 50 | 15.2 | 273 | 6.2 / 99 | 6.9 / 83 |
| noisy-solve | 50 | 13.4 | 213 | 5.0 / 68 | 6.0 / 67 |
| never landed an edit | 97 | 20.6 | 307 | 8.3 / 118 | 9.2 / 105 |

- **The reference file is found early.** It is named by call 3 in 293 of 395 draws, at a median of call 2 (11 s).
  In the 19 noisy-fail draws with no edit attempt, it was named and read in all 19, by call 3 in 17.
- **Most pre-edit calls come after the file is found.** From the first naming of the file that is eventually
  edited to the edit itself takes a median of 9 more calls: 7 in resolved draws, 12 in noisy-fail, 21 in
  never-landed.
- Tool time is about 0.2% of search seconds. The rest is model time.
- **Ceiling of a locate script.** One script call replaces every call up to the first call that names or reads the
  reference file. That saves 1.5 calls and 8 s per noisy-fail draw. 5 of the 19 noisy-fail draws with no edit
  attempt would then reach one.
  - The strict upper bound, which also removes every read of a file never edited, is 9.2 calls and 153 s. Most of
    what it removes comes after the file is found, while the agent decides what to change. No locate script
    replaces that.
- **Earlier locate attempts all failed on effect, not on compliance:**
  - R-005: twosearch, filerank.
  - R-007: locator then editor, pinissue.
  - R-014: the 31B scout.
  - EXP-032: three parallel localizers.

**Verdict: do not build.** The 31B's pre-edit time is spent deciding what to change, not finding where.

## B. E4B: failed `edit_file` calls

| Arm | Draws | Edits | Failed | Not-found | Not-unique | Malformed | No-op |
|---|---|---|---|---|---|---|---|
| R-011 base d1-d8 | 632 | 2055 | 1178 | 808 | 202 | 148 | 20 |
| L-003 full0 d1-d8 (partial, fold B) | 312 | 859 | 464 | 305 | 94 | 55 | 10 |
| R-014 applier d1 | 79 | 376 | 204 | 113 | 72 | 7 | 12 |

| Not-found class | R-011 base | L-003 full0 |
|---|---|---|
| ABSENT | 421 | 132 |
| NEAR (>= 0.9) | 218 | 89 |
| stale | 161 | 74 |
| NEAR but ambiguous | 5 | 5 |
| WS | 1 | 0 |
| PREFIX, AMBIG | 0 | 0 |
| no read to compare | 2 | 4 |

- **WS and PREFIX are empty because the harness already tolerates whitespace.** Checked in the wheel
  (`adk_eval_core/editing/edit.py`): `edit_file` tries an exact match, then rstrip and strip windows, then a regex
  match, then JSON-unescape. No `old_string` carries copied line numbers.
- **NEAR differs by one line, which a fuzzy applier would write into the file.** Of R-011's 218 NEAR failures,
  only 32 are >= 0.9 at line level. 128 differ by one line, and in 99 of those the misquoted line also appears in
  `new_string`, so a fuzzy applier would write the misquote into the file.
- **Per draw.** In R-011, 63 draws failed an edit and never landed one.
  - Character-level NEAR or a read-window anchor for not-unique would land an edit in 35 of them.
  - The landed draws on those tasks resolve 7.8% of the time, so the gain is about 2.7 resolves over 8 draws,
    about 0.3 per draw. That is under the MDE, and only if the fuzzy edit were right.
- **R-014's applier landed edits and still resolved 2 of 79.** It left only 3 draws without a landed edit.
  Landing an edit is not what limits the E4B. Correct edits are, and that points to LoRA (L-003), not to a script.

**Verdict: do not build.** A whitespace-tolerant applier rescues no draws. The fuzzy and anchor variants are worth
about 0.3 resolves per draw, below the MDE, and would write wrong lines.

## Limits

- Model time per turn is taken as fixed.
- A rescued draw is assumed to edit on its next turn.
- Reads are paged windows, so "the latest read" is a window, not the whole file.
- NEAR compares only windows with the same number of lines.
- The L-003 full0 numbers are partial and on a different cohort.
- Neither ceiling says whether an edit would be correct.

The per-draw counts are kept outside git (session scratch). The scripts are in `tools/sizing/` (added with R-015,
2026-11-21); `tools/r015_gates.py` reuses `locate_31b.py`'s call parsing.
