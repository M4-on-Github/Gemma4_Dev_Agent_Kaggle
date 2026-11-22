# Directions

Ranked backlog per model. A direction is a family of tweaks; a round takes the top open one (or the
next after a pivot). Sources: `../research/lit/2026-11-17-run-synthesis-model-faults.md`,
`../research/lit/2026-11-17-next-ideas-web-scout.md`, and the traces under `runs/`.
Status: open / active / kept / dropped / pivoted-away. Update after every round. (Statuses through R-010 were
filled in 2026-11-19 with R-011; before that several rows still said open after their round.)

## 31B (`trees/31b-base`, 28 calls, 8 min, thinking 4096, T=1.0)

| # | Direction | Why (evidence) | First tweak | Status |
|---|---|---|---|---|
| A1 | More tool calls | 6 small-gold tasks lost at the 28-call cap in both Kaggle baseline arms; one Ada decodes ~35 tok/s alone, so time is not the binding limit at 28 | `max_tool_calls` 28 -> 40, prompt budget line to match | dropped (R-001 T-31b-001: the same tasks moved onto the time cap) |
| A2 | Sibling-site sweep (bug-fix mechanics) | most 31B losses are partial fixes on multi-region gold patches | prompt rule: after the first edit, grep the changed identifier and patch every sibling site before testing | dropped (R-001 T-31b-002: +1, inside the margin) |
| A3 | Cheaper thinking | thinking tokens are most of the decode time; fewer thinking tokens buy calls inside 8 min | `thinking_budget` 4096 -> 1024 | dropped (R-002 T-31b-003: no wall time saved; R-004 output cap 2048 also dropped) |
| A4 | Bounded observations | compaction fires at 14,336 prompt tokens and drops what the model read | prompt rule: every command output piped through `head`, reads <= 80 lines | dropped (R-011 T-31b-011: 8.5 vs 8.5; only 20% of commands bounded, so the idea is untested in prompt form) |
| A5 | Sampling temperature | T=1.0 gives wide draw-to-draw spread | T 1.0 -> 0.6 | dropped (R-011 T-31b-010: 8.5 vs 8.5, time cap + empty 22 vs 17) |
| A6 | Process order (invariant) | the "edit by call 12" rule may force early wrong edits | reproduce-first variant: one failing check before the edit | dropped 2026-11-19 (R-010: failing 31B draws commit late, and this would delay the edit further) |
| A7 | Commit-forcing orchestration (2026-11-20, R-012 pool) | unresolved noisy-task draws land no source edit 3.5 per draw (ceiling 1.92, the largest group); first edit ~4 calls later than in resolved draws of the same task; the prompt rule A6/T-31b-007 was not followed | SequentialAgent scout (no edit tools, 3-line TARGET) -> editor (edit within 2 calls) | dropped (R-014 T-31b-012: killed at draw 1, scout median 12 calls per task against a bar of 10; the scout made tasks longer) |
| A8 | Worked example (2026-11-21) | the 31B names the edited file early, then takes a median 9 calls to edit it (7 in resolved draws, 12 in unresolved); `rounds/skill-script-sizing.md` part A | one made-up solve as section 5 of the system prompt | dropped (R-015 T-31b-013: killed at draw 1, resolved 25 at the bar of 25 against base d6 27; file-to-edit median 10, not met; no-edit draws 15 against 8) |
| A9 | Edit-argument loss (2026-11-22, R-034/R-035) | about half of `edit_file` calls lose `old_string`: the 31B closes `new_string` with a backtick, so the Gemma 4 parser runs on (87% of lost calls in 38 draws); lost after lost 0.89-0.95 | line-only edit skill (R-034); prompt bullet or backtick-free prompt (R-035 draft) | closed (R-034 31B arm −6.00 on harness errors; R-035 desk: heavy-loss task-draws resolve 25 vs 22.9 paired, cost +58 s each, ceiling about 2-3% wall and 0 solves, not run) |

## E4B (`trees/e4b-base`, same tree, model line differs)

| # | Direction | Why (evidence) | First tweak | Status |
|---|---|---|---|---|
| B0 | Edit failures (found 2026-11-18, R-000) | 17% and 28% of edit calls fail with FileEditError in the two reference draws; 10 and 8 of 56 tasks end with an empty patch | prompt: short `old_string` copied from the last read; re-read after a failure; scripted replace after two | not kept (R-002 T-e4b-003) |
| B1 | Localization (wrong file 10.0, wrong region 8.2 tasks lost per draw) | R-005 proposer: the reference file appears in a search output in only 5 of 43 wrong-file task-draws; 'edits the first grep hit' held on 7 of 27 | prompt rule: two greps (symbol and error string), list candidate files, read the definition before editing | closed 2026-11-18 (R-005: the hit-count search was taken up and named the reference file more often, but wrong-file did not fall; two-search was not followed) |
| B2 | Sibling-site sweep | partial fix 9.5 tasks lost per draw | same rule as A2 | dropped (R-001 T-e4b-002, reclassified as noise in R-006) |
| B3 | Sampling | small model at T=1.0 | T 1.0 -> 0.3 | dropped (R-003 T-e4b-004) |
| B4 | Use the unused budget | E4B tasks end in ~30-50 s of 480 s and under 10 calls | prompt: required second look (re-read the diff against the contract list, fix, then submit) | not kept (R-011 T-e4b-015: editor then reviewer 7.5 vs 7.0 over 8 draws each, CI includes 0; the reviewer edits only 21% of diffs) |
| B5 | Thinking budget | 4096 may be more than the E4B uses well, or too little | 1024 and 8192 | 2048 dropped (R-007 T-e4b-011); 8192 closed at L0 2026-11-20 (R-012 review: 67 of 7,378 E4B turns reach 4,096 thinking tokens; 8192 equals `max_output_tokens`, so tool calls would be cut) |
| B6 | Shorter prompt | 3.1 kB of rules may exceed what the E4B follows | cut to the contract, locate, edit, submit skeleton | dropped (R-003 T-e4b-005: same score at 1.2 kB) |
| B7 | Edit applier in a fresh context (2026-11-20, R-012 recount) | 46.5% of Turing base task-draws have a failed edit, 35.0% a not-found; 265 of 808 not-found anchors quote lines never read | `edit_file` -> agent_tool `apply_edit` that re-reads LINES and copies `old_string` | active (R-014 T-e4b-016) |

## Later (not in the first 24 h)

- LoRA adapters (public data only unless the user says otherwise); canary on the 31B serving path first.
  2026-11-20 R-012 review, stage 0 desk check: the budget gate fails for the 31B (10.04 h Kaggle projection x 1.17
  decode slowdown = 11.7 h); the pool gate fails (no target worth +3 per draw); feasibility is partial (no peft, no BF16
  parent on disk). Stage 1, the 31B canary with the organisers' sample adapter, waits for the user's decisions.
- ~~Per-task dependency install in the sandbox~~ done 2026-11-18 with the user's permission:
  `--py313 ... --task-envs env/taskenvs` makes 119/129 tasks gradeable (was 101); see
  `rounds/C-002-C-003-test-envs.md`. Agent runs that should use it must pass the same flags.
  2026-11-19: C-004 pins werkzeug for requests_6592 (120/129 gradeable); R-008 moves agent runs onto it
  and re-baselines both models (`rounds/R-008-taskenv-base.md`).
