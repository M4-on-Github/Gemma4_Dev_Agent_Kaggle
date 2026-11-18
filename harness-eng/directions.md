# Directions

Ranked backlog per model. A direction is a family of tweaks; a round takes the top open one (or the
next after a pivot). Sources: `../research/lit/2026-11-17-run-synthesis-model-faults.md`,
`../research/lit/2026-11-17-next-ideas-web-scout.md`, and the traces under `runs/`.
Status: open / active / kept / dropped / pivoted-away. Update after every round.

## 31B (`trees/31b-base`, 28 calls, 8 min, thinking 4096, T=1.0)

| # | Direction | Why (evidence) | First tweak | Status |
|---|---|---|---|---|
| A1 | More tool calls | 6 small-gold tasks lost at the 28-call cap in both Kaggle baseline arms; one Ada decodes ~35 tok/s alone, so time is not the binding limit at 28 | `max_tool_calls` 28 -> 40, prompt budget line to match | open |
| A2 | Sibling-site sweep (bug-fix mechanics) | most 31B losses are partial fixes on multi-region gold patches | prompt rule: after the first edit, grep the changed identifier and patch every sibling site before testing | open |
| A3 | Cheaper thinking | thinking tokens are most of the decode time; fewer thinking tokens buy calls inside 8 min | `thinking_budget` 4096 -> 1024 | open |
| A4 | Bounded observations | compaction fires at 14,336 prompt tokens and drops what the model read | prompt rule: every command output piped through `head`, reads <= 80 lines | open |
| A5 | Sampling temperature | T=1.0 gives wide draw-to-draw spread | T 1.0 -> 0.6 | open |
| A6 | Process order (invariant) | the "edit by call 12" rule may force early wrong edits | reproduce-first variant: one failing check before the edit | open |

## E4B (`trees/e4b-base`, same tree, model line differs)

| # | Direction | Why (evidence) | First tweak | Status |
|---|---|---|---|---|
| B0 | Edit failures (found 2026-11-18, R-000) | 17% and 28% of edit calls fail with FileEditError in the two reference draws; 10 and 8 of 56 tasks end with an empty patch | prompt: short `old_string` copied from the last read; re-read after a failure; scripted replace after two | active (R-002) |
| B1 | Localization (wrong file 10.0, wrong region 8.2 tasks lost per draw) | R-005 proposer: the reference file appears in a search output in only 5 of 43 wrong-file task-draws; 'edits the first grep hit' held on 7 of 27 | prompt rule: two greps (symbol and error string), list candidate files, read the definition before editing | closed 2026-11-18 (R-005: the hit-count search was taken up and named the reference file more often, but wrong-file did not fall; two-search was not followed) |
| B2 | Sibling-site sweep | partial fix 9.5 tasks lost per draw | same rule as A2 | open |
| B3 | Sampling | small model at T=1.0 | T 1.0 -> 0.3 | open |
| B4 | Use the unused budget | E4B tasks end in ~30-50 s of 480 s and under 10 calls | prompt: required second look (re-read the diff against the contract list, fix, then submit) | open |
| B5 | Thinking budget | 4096 may be more than the E4B uses well, or too little | 1024 and 8192 | open |
| B6 | Shorter prompt | 3.1 kB of rules may exceed what the E4B follows | cut to the contract, locate, edit, submit skeleton | open |

## Later (not in the first 24 h)

- LoRA adapters (public data only unless the user says otherwise); canary on the 31B serving path first.
- ~~Per-task dependency install in the sandbox~~ done 2026-11-18 with the user's permission:
  `--py313 ... --task-envs env/taskenvs` makes 119/129 tasks gradeable (was 101); see
  `rounds/C-002-C-003-test-envs.md`. Agent runs that should use it must pass the same flags.
