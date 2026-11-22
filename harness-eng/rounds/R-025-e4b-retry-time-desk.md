# R-025: does the E4B retry run out of time at 4.5 min? (desk check; no GPU run)

Written 2026-11-22, after R-024's decision. Counts only; no trace content. Lowest rung of the screening ladder.
The question is whether "a retry with a shorter first attempt", the one variant R-024 left open, is worth a GPU round.

## Method

`tools/attempt_times.py` on the 12 R-024 retry draws. Attempts are cut at root `solve` calls using the trace's
`elapsed_s`. An attempt is empty when the change-count skill printed 0. Time left is 270 s minus the end of the first
attempt.

## Counts

| Count (12 draws, 948 task-draws) | Value |
|---|---|
| empty first attempts with a count | 161 |
| end of an empty first attempt, p10 / p50 / p90 | 13 / 82 / 149 s |
| empty first attempts leaving < 120 s | 15 |
| empty first attempts leaving < 60 s | 1 |
| resolved in a single attempt | 71 |
| length of a solving attempt, p10 / p50 / p90 | 32 / 59 / 101 s |
| solving attempts ≤ 60 s / ≤ 120 s | 38 / 67 of 71 |
| rescued; length of the rescuing attempt | 10; 39, 53, 54, 57, 61, 83, 88, 110, 127, 133 s |

## Decision

- **Not run.** After 146 of 161 empty first attempts, more than 120 s remained. 67 of 71 solving attempts fit in
  120 s. So the time a retry gets is rarely what stops it.
- The limit is the success rate of a retry: 10 rescued of 162 retried (6%). The extra time caps in R-024's retry arm
  (7.0 against 3.9 per draw) come from retries of tasks the E4B does not solve. They cost wall, not solves.
- A shorter first attempt would cut the first attempt's own solves and gain little. There is no other open E4B
  orchestration variant with an offline sizing above noise. The E4B ships the EXP-050 single loop.
