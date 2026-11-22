# R-031: E4B selection among independent attempts, re-checked on the R-021 draws (desk check; no GPU run)

Written 2026-11-22, while R-030 runs. Counts only. Lowest rung of the screening ladder.

## Question

R-029 showed that the E4B repairs badly: it sees its own syntax error, and the fix edits fail. If a broken or wrong
attempt cannot be fixed, the other way to use the E4B's spare wall is to pick among attempts. R-019 sized a
file-set selector on the older R-008 draws and found 6.33, below retry. Here the same question is asked on the 24
R-021 draws (8 min cap), using patch agreement and the syntax class from R-029.

## Method

- **Unit.** Per task, every set of 3 of the 12 draws of one arm (220 sets).
- **Attempts compared.** A patch is reduced to the set of its +/- lines.
- **Policies:**
  - `first`: the first draw of the set. It is weighted toward early draws, so it is not the arm mean.
  - `first_ok`: the first draw whose patch is non-empty and parses.
  - `medoid`: among the non-empty, parsing patches, the one with the highest summed Jaccard overlap with the others.
  - `oracle`: any of the three resolved.
- No call or time cap is applied. Each draw is a full independent attempt.

| Draws | Arm mean (real) | first | first_ok | medoid | oracle |
|---|---|---|---|---|---|
| R-021 control (one solve) ×12 | 6.25 | 6.01 | 8.36 | 8.77 | 10.79 |
| R-021 retry ×12 | 7.58 | 8.33 | 9.17 | 9.63 | 13.45 |

## Reading

- **Most of the uncapped gain is "skip empty and unparseable attempts":** 6.25 → 8.36 for control attempts. Agreement
  (medoid) adds only about 0.4 on top.
  - The retry layout (R-021) and the syntax trigger (R-029/R-030) are the sequential, capped forms of the same
    policy. R-021 reached 7.58 against this uncapped 8.36, because its attempts share the 56-call and 8-minute caps
    and the leftover workspace.
- **The caps are binding.**
  - Three independent control attempts cost about 3 × 113 s of agent wall per task. Over 120 hidden tasks that is
    above 11 h, before setup and before any attempt is cut by the 8-minute cap.
  - R-019, with the caps applied, gave 6.33 at 250 s per task.
  - So a best-of-3 with a selector does not fit the Kaggle run. **Not built, not queued.**
- For R-030: the upper bound of a perfect syntax trigger is small. The trigger fires only on attempts that are sure
  misses, at 8.58 per draw, and those tasks resolve in about 5% of other draws.
