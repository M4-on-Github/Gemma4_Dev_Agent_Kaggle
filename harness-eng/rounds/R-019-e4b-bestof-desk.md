# R-019: E4B best-of-3 with a file-set selector (desk check; no GPU run)

Written 2026-11-21. Counts only; no trace content. Tweak id **T-e4b-019**. This is the lowest rung of the screening
ladder: a desk check plus trace mining over existing base draws. Its outcome decides whether a GPU round is
pre-registered. It was not run on a GPU.

## What was built

- Tree `trees/e4b-r019-bestof`: R-017's tree plus `run_command` on the root, the skill `skills/best-of`
  (`scripts/pick.py`), a new `prompts/root.md`, and `max_tool_calls` 28 → 64.
  - The root runs `solve`. A fixed `run_command` string saves the attempt to `.git/cand_N.diff` and resets the
    workspace to `_swegemma_baseline`.
  - `run_skill_script` then calls `pick.py`, which prints NEXT or APPLY.
  - On APPLY the root runs `git apply` on `.git/chosen.diff`, then calls `submit_patch`.
- `pick.py` policy:
  - It compares the source-file sets of the attempts, leaving test files and test configs out.
  - Two attempts with the same set: keep the smaller.
  - Otherwise run a third attempt and keep the file set most attempts share. Ties go to the smallest, then the
    earliest.
  - It uses pure file reads and writes only under `.git/`.
- Checked by hand on a synthetic git repo:
  - save, reset, pick and apply work end to end;
  - test files are left out of the file sets;
  - CRLF content survives the round trip byte for byte.
- The ADK skill wrapper:
  - It writes `.adk_exec_*.py` into the work dir and deletes it after the run.
  - The script uses no git, so the wrapper file never enters a saved attempt.
  - `sys.path[0]` names the workspace, which `pick.py` uses to find the root.
- The tree was not run through the validator.

## Desk check (zero GPU)

`tools/bestof_sim.py` resamples ordered triples of base draws. It applies `pick.py`'s own `choose()` and the shared
tool counter, turn counter and task clock. Each attempt adds 2 root tool calls, 3 root model calls and 6 s, and the
end adds 2 calls and 3 model calls. An attempt that would cross a cap is not run, and the task then keeps the last
non-empty attempt.

| Base draws | Cap | Policy | Resolved per draw | Attempts per task | Wall per task |
|---|---|---|---|---|---|
| Ada R-008-te2 d1-d3 (base 6.67, 106 s) | 480 s | best-of (pick.py) | **6.33** | 2.39 | 250 s |
| | 480 s | retry-on-empty (R-018) | **7.67** | 1.17 | 127 s |
| | 480 s | oracle over the same attempts | 11.33 | 2.39 | 250 s |
| Turing R-011-tu5 d1-d8, time ÷ 5 (base 7.00, 121 s) | 480 s | best-of (pick.py) | **8.12** | 2.29 | 268 s |
| | 480 s | retry-on-empty (R-018) | **8.20** | 1.15 | 141 s |
| | 480 s | oracle | 10.97 | 2.29 | 268 s |
| | none | best-of / retry-on-empty / oracle | 8.36 / 8.34 / 11.28 | 2.52 / 1.18 / 2.52 | 323 / 150 / 323 s |

- Under the shared clock the file-set selector is no better than retry-on-empty. It is worse on Ada and level on
  Turing, at about twice the wall.
- The earlier figure of +1.9 at 2.5 attempts (`tools/select_sim.py`) ignored the caps.
- The oracle shows about +4 solves per draw of headroom, so the selection signal is the limit, not the number of
  attempts.
- **The test signal, mined from the same traces.**
  - Each non-empty attempt was classed by the last `run_command` output in the attempt that held a pytest
    summary.
  - Last run failed: 1 resolved of 48. Passed: 4 of 20. No test run: 71 of 678.
  - A failing last run is a strong negative signal, but it is present in only 6% of attempts. A selector built on
    it moves less than one solve per draw.

## Decision

- **Not run on a GPU.** The best-of-3 file-set selector is dropped at the desk check. The Ada GPU-hours stay with
  R-018.
- The E4B framework candidate is R-018's retry-on-empty layout, pending its readings.
- The tree and `tools/bestof_sim.py` are kept. A future selector with a better signal can reuse the save, reset
  and apply plumbing.
