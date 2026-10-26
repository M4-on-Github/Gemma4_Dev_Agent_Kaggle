#!/usr/bin/env python3
"""Recompute every number quoted in experiments/EXP-024-direction-review-2.md.

The two dev-48 runs live under runs/, which is .gitignored, so this script takes the
repo root (the MAIN checkout, not a worktree) as its only argument:

    python -I -X utf8 tools/exp024_stats.py C:/Users/moemy/Documents/Kaggle/Gemma4_Dev_Agent_Kaggle

Sections 1-4 are MEASURED: they read task_results.jsonl, summary.jsonl and traces/*.json
and report counts. Sections 5-6 are MODELLED: Monte Carlo over an explicit heterogeneous-difficulty
beta-binomial model, seeded, with the measured base rates as inputs. The two are never mixed.

Stdlib only, no numpy/scipy, so it runs anywhere the repo tooling does.
"""
from __future__ import annotations

import json
import math
import random
import re
import statistics
import sys
from functools import lru_cache
from pathlib import Path
from statistics import NormalDist

E0 = "runs/E0-dev48-baseline/runs/E0-dev48-baseline"
E3 = "runs/exp003_public_budget_dev48/runs/EXP-003-public-budget-dev48"

# The exact harness error that means an argument never reached the tool.
LOST_ARG_RE = re.compile(r"mandatory input parameters are not present", re.I)

SEED = 20261026
ND = NormalDist()


# ----------------------------------------------------------------- loading


def load_jsonl(p: Path) -> list[dict]:
    out = []
    with open(p, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def load_run(root: Path, rel: str) -> dict:
    d = root / rel
    traces = {}
    for f in sorted((d / "traces").glob("*.json")):
        with open(f, encoding="utf-8") as fh:
            # trace files are named trace_<task_id>.json; strip the prefix so trace keys
            # join against the task_id keys in task_results.jsonl / summary.jsonl.
            traces[f.stem.removeprefix("trace_")] = json.load(fh)
    return {
        "dir": d,
        "tasks": load_jsonl(d / "task_results.jsonl"),
        "summary": load_jsonl(d / "summary.jsonl"),
        "traces": traces,
    }


def key(rec: dict) -> str:
    for k in ("task_id", "instance_id", "id", "task"):
        if k in rec:
            return str(rec[k])
    raise KeyError(sorted(rec))


def resolved(rec: dict) -> bool:
    for k in ("resolved", "is_resolved", "passed", "success"):
        if k in rec:
            return bool(rec[k])
    raise KeyError(sorted(rec))


def steps_of(trace):
    if isinstance(trace, dict):
        for k in ("steps", "trace", "events"):
            if isinstance(trace.get(k), list):
                return trace[k]
        return []
    return trace if isinstance(trace, list) else []


def tool_calls_of(step):
    for tc in (step.get("tool_calls") or []):
        fn = tc.get("function_name") or tc.get("name")
        args = tc.get("arguments") or {}
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except Exception:
                args = {}
        if not isinstance(args, dict):
            args = {}
        obs = (step.get("observation") or {}).get("content") or ""
        if not isinstance(obs, str):
            obs = json.dumps(obs)
        yield fn, args, obs


# ------------------------------------------------------------ stats helpers


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


@lru_cache(maxsize=None)
def _hyper_pmf(r1: int, n: int, c1: int, x: int) -> float:
    lo, hi = max(0, c1 - (n - r1)), min(r1, c1)
    if not lo <= x <= hi:
        return 0.0
    return math.comb(r1, x) * math.comb(n - r1, c1 - x) / math.comb(n, c1)


def fisher_exact(a: int, b: int, c: int, d: int) -> float:
    """Two-sided Fisher exact p-value for [[a,b],[c,d]] (sum of tables no more likely)."""
    n, r1, c1 = a + b + c + d, a + b, a + c
    obs = _hyper_pmf(r1, n, c1, a)
    lo, hi = max(0, c1 - (n - r1)), min(r1, c1)
    return min(1.0, sum(p for x in range(lo, hi + 1)
                        if (p := _hyper_pmf(r1, n, c1, x)) <= obs * (1 + 1e-9)))


def mcnemar_exact(b: int, c: int) -> float:
    """Two-sided exact McNemar from the discordant counts."""
    n = b + c
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def mann_whitney(x: list[float], y: list[float]) -> tuple[float, float, float]:
    """Tie-corrected normal-approx U. Returns (z, two-sided p, P(x>y)+0.5P(x=y))."""
    comb = sorted([(v, 0) for v in x] + [(v, 1) for v in y])
    ranks: dict[int, float] = {}
    tie = 0.0
    i = 0
    while i < len(comb):
        j = i
        while j + 1 < len(comb) and comb[j + 1][0] == comb[i][0]:
            j += 1
        t = j - i + 1
        tie += t ** 3 - t
        for k in range(i, j + 1):
            ranks[k] = (i + j) / 2 + 1
        i = j + 1
    n1, n2, n = len(x), len(y), len(x) + len(y)
    r1 = sum(ranks[k] for k, (_, g) in enumerate(comb) if g == 0)
    u1 = r1 - n1 * (n1 + 1) / 2
    var = n1 * n2 / 12 * ((n + 1) - tie / (n * (n - 1)))
    z = (u1 - n1 * n2 / 2) / math.sqrt(var)
    return z, math.erfc(abs(z) / math.sqrt(2)), u1 / (n1 * n2)


def _chi2_cdf(x: float, k: int) -> float:
    """Regularized lower incomplete gamma P(k/2, x/2): series below the mean, CF above."""
    a, xx = k / 2, x / 2
    if xx <= 0:
        return 0.0
    if xx < a + 1:
        term = s = 1.0 / a
        for n in range(1, 10_000):
            term *= xx / (a + n)
            s += term
            if abs(term) < abs(s) * 1e-15:
                break
        return s * math.exp(-xx + a * math.log(xx) - math.lgamma(a))
    tiny = 1e-300
    b, c, d = xx + 1 - a, 1 / tiny, 1 / (xx + 1 - a)
    h = d
    for i in range(1, 10_000):
        an = -i * (i - a)
        b += 2
        d = an * d + b
        d = tiny if abs(d) < tiny else d
        c = b + an / c
        c = tiny if abs(c) < tiny else c
        d = 1 / d
        de = d * c
        h *= de
        if abs(de - 1) < 1e-15:
            break
    return 1 - math.exp(-xx + a * math.log(xx) - math.lgamma(a)) * h


def chi2_quantile(q: float, df: int) -> float:
    lo, hi = 1e-9, 1e4
    for _ in range(200):
        mid = (lo + hi) / 2
        if _chi2_cdf(mid, df) < q:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def var_ci(s2: float, n: int) -> tuple[float, float]:
    """Exact-normal-theory 95% CI for a variance from n draws."""
    df = n - 1
    return df * s2 / chi2_quantile(0.975, df), df * s2 / chi2_quantile(0.025, df)


# --------------------------------------------------------- trace extraction


KNOWN_ARGS = frozenset({"filepath", "new_string", "old_string", "allow_multiple",
                        "content", "command", "start_line", "end_line"})


def edit_calls(run: dict) -> list[dict]:
    """Every edit_file / write_file call, with whether its arguments survived transport.

    On a lost call the old_string VALUE is gone, but in 64 of the 117 cases fragments of the
    anchor the model was trying to send survive as spurious argument KEYS: the gemma4
    tool-call text was split on the commas inside the anchor, so each comma-separated piece
    became a key. Rejoining those keys with a comma reconstructs (a lower bound on) the
    anchor that was attempted. `anchor_len` is therefore a reconstruction for lost calls and
    the real value for successful ones -- never compare them without saying so.
    """
    rows = []
    for tid, trace in run["traces"].items():
        for st in steps_of(trace):
            for fn, args, obs in tool_calls_of(st):
                if fn not in ("edit_file", "write_file"):
                    continue
                lost = bool(LOST_ARG_RE.search(obs))
                old = args.get("old_string")
                leaked = ",".join(k for k in args if k not in KNOWN_ARGS)
                anchor = leaked if lost else (old if isinstance(old, str) else "")
                rows.append({
                    "task": tid,
                    "fn": fn,
                    "lost": lost,
                    "has_old": "old_string" in args,
                    "has_new": "new_string" in args,
                    "anchor": anchor,
                    "anchor_len": len(anchor),
                    "lines": anchor.count("\n") + anchor.count("\\n") + 1 if anchor else 0,
                })
    return rows


def edit_outcome(run: dict) -> tuple[dict, dict]:
    """(attempted an edit at all, landed at least one edit) per task."""
    att, ok = {}, {}
    for tid, trace in run["traces"].items():
        a = g = False
        for st in steps_of(trace):
            for fn, _args, obs in tool_calls_of(st):
                if fn not in ("edit_file", "write_file"):
                    continue
                a = True
                low = obs.lower()
                if not LOST_ARG_RE.search(obs) and "failed" not in low and "error" not in low:
                    g = True
        att[tid], ok[tid] = a, g
    return att, ok


# ------------------------------------------------------------------- model


def difficulties(theta: float, rho: float, rng: random.Random) -> list[float]:
    """58 per-task success probabilities, FIXED across every draw of one config.

    This is the only model consistent with the direction of our data. The 7 scored
    submissions are LESS dispersed (sd 1.380) than an independent binomial at the same
    mean (2.437), and heterogeneous fixed task difficulty is what shrinks the variance:
    with p_i fixed, Var(K) = sum p_i(1-p_i) = n*pbar*(1-pbar) - n*Var(p). Writing
    rho = Var(p) / (pbar*(1-pbar)) gives Var(K) = (1-rho) * binomial variance, i.e. exactly
    the beta-binomial intraclass correlation with rho = 1/(a+b+1). Because p_i is drawn once
    and reused, successive draws are positively correlated -- which is what makes repeated
    sampling of the leaderboard a weak way to buy tasks, since the hard ones stay hard.
    A shared-latent-factor model that re-randomises per draw moves the variance the WRONG
    way (it inflates it) and was rejected.
    """
    mu = theta / 58.0
    if rho <= 1e-9:
        return [mu] * 58
    s = 1.0 / rho - 1.0
    a, b = mu * s, (1.0 - mu) * s
    return [rng.betavariate(a, b) for _ in range(58)]


def max_stats(theta: float, rho: float, reps: int, rng: random.Random,
              n_list: tuple[int, ...] = (17,), thresholds: tuple[tuple[int, int], ...] = ()):
    """E[max of n] for each n in n_list, plus P(max of n >= k) for each (n, k) threshold.

    One replicate draws the task difficulties once and then max(n_list) independent runs,
    so the nested maxima are read off the same sample (valid: they are prefixes).
    """
    nmax = max(list(n_list) + [n for n, _ in thresholds])
    tot = {n: 0 for n in n_list}
    hits = {t: 0 for t in thresholds}
    for _ in range(reps):
        ps = difficulties(theta, rho, rng)
        running, best = [], 0
        for _ in range(nmax):
            k = sum(1 for p in ps if rng.random() < p)
            best = max(best, k)
            running.append(best)
        for n in n_list:
            tot[n] += running[n - 1]
        for (n, k) in thresholds:
            if running[n - 1] >= k:
                hits[(n, k)] += 1
    return ({n: tot[n] / reps for n in n_list},
            {t: hits[t] / reps for t in thresholds})


# -------------------------------------------------------------------- main


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    root = Path(sys.argv[1])
    runs = {"E0": load_run(root, E0), "E3": load_run(root, E3)}
    rng = random.Random(SEED)
    random.seed(SEED)

    print("=" * 76)
    print("SECTION 1  run descriptives                                  [MEASURED]")
    print("=" * 76)
    for name, run in runs.items():
        res = {key(r): resolved(r) for r in run["tasks"]}
        sm = {key(r): r for r in run["summary"]}
        n, k = len(res), sum(res.values())
        empty = [t for t, s in sm.items() if s.get("patch_empty")]
        tcap = sum(1 for s in sm.values() if s.get("time_cap_hit"))
        ccap = sum(1 for s in sm.values() if s.get("calls_cap_hit"))
        wall = [s.get("wall_s", 0.0) for s in sm.values()]
        calls = [s.get("n_calls", 0) for s in sm.values()]
        print(f"{name}: n={n} resolved={k} empty={len(empty)} "
              f"time_cap={tcap} ({tcap / n:.1%}) calls_cap={ccap} ({ccap / n:.1%})")
        free = 0
        for s in sm.values():
            h = s.get("tool_histogram") or {}
            free += int(h.get("get_status", 0)) + int(h.get("submit_patch", 0))
        billable = sum(calls) - free
        print(f"    mean wall {statistics.mean(wall):6.1f}s  total calls {sum(calls)} "
              f"(of which free {free})")
        print(f"    pooled {sum(wall) / max(1, sum(calls)):.2f} s/call over ALL calls, "
              f"{sum(wall) / max(1, billable):.2f} s/call over BILLABLE calls only")
        for lab, sel in (("EMPTY  ", lambda t: sm[t].get("patch_empty")),
                         ("RESOLVE", lambda t: res[t])):
            ts = [t for t in res if sel(t)]
            if not ts:
                continue
            cap = sum(1 for t in ts if sm[t].get("time_cap_hit"))
            print(f"    {lab} n={len(ts):2d} wall {statistics.mean([sm[t]['wall_s'] for t in ts]):6.1f}s "
                  f"calls {statistics.mean([sm[t]['n_calls'] for t in ts]):5.1f} "
                  f"turns {statistics.mean([sm[t]['n_turns'] for t in ts]):5.1f} "
                  f"time_capped {cap}/{len(ts)}")
        prod = [t for t in res if not sm[t].get("patch_empty")]
        pk = sum(1 for t in prod if res[t])
        print(f"    producers {len(prod)}  resolve-among-producers {pk}/{len(prod)} = {pk / len(prod):.3f}")
        print(f"    resolved among the {len(empty)} empty patches: {sum(res[t] for t in empty)}")

    print()
    print("=" * 76)
    print("SECTION 2  the edit_file argument-loss defect                 [MEASURED]")
    print("=" * 76)
    rows = {n: edit_calls(r) for n, r in runs.items()}
    pooled = {"edit_file": [0, 0], "write_file": [0, 0]}
    for name in runs:
        for fn in ("edit_file", "write_file"):
            sub = [r for r in rows[name] if r["fn"] == fn]
            bad = [r for r in sub if r["lost"]]
            pooled[fn][0] += len(bad)
            pooled[fn][1] += len(sub)
            lo, hi = wilson(len(bad), len(sub))
            rate = len(bad) / len(sub) if sub else 0.0
            print(f"{name} {fn:11s} {len(bad):3d}/{len(sub):3d} = {rate:6.1%}  "
                  f"Wilson95 [{lo:.1%}, {hi:.1%}]")
    for fn in ("edit_file", "write_file"):
        b, n = pooled[fn]
        lo, hi = wilson(b, n)
        print(f"POOLED {fn:11s} {b:3d}/{n:3d} = {b / n:6.1%}  Wilson95 [{lo:.1%}, {hi:.1%}]")
    ea, en = pooled["edit_file"]
    wa, wn = pooled["write_file"]
    print(f"  Fisher, edit_file vs write_file loss: p = {fisher_exact(ea, en - ea, wa, wn - wa):.4f}")

    allrows = rows["E0"] + rows["E3"]
    bad = [r for r in allrows if r["fn"] == "edit_file" and r["lost"]]
    print(f"  POSITIONAL MECHANISM, pooled over the {len(bad)} lost edit_file calls:")
    print(f"    new_string (LAST arg)   present in {sum(r['has_new'] for r in bad)}/{len(bad)}")
    print(f"    old_string (MIDDLE arg) present in {sum(r['has_old'] for r in bad)}/{len(bad)}")

    r0 = [r for r in rows["E0"] if r["fn"] == "edit_file"]
    r3 = [r for r in rows["E3"] if r["fn"] == "edit_file"]
    a, c = sum(r["lost"] for r in r0), sum(r["lost"] for r in r3)
    print(f"  E0 (thinking_budget 256) vs E3 (4096), call level: "
          f"Fisher p = {fisher_exact(a, len(r0) - a, c, len(r3) - c):.4g}")
    t0 = len({r['task'] for r in r0 if r['lost']})
    t3 = len({r['task'] for r in r3 if r['lost']})
    print(f"  task level {t0}/48 vs {t3}/48 tasks hit by the defect: "
          f"Fisher p = {fisher_exact(t0, 48 - t0, t3, 48 - t3):.4g}")

    es = [r for r in allrows if r["fn"] == "edit_file"]
    succ_r = [r for r in es if not r["lost"] and r["anchor_len"]]
    fail_r = [r for r in es if r["lost"] and r["anchor_len"]]
    succ = [r["anchor_len"] for r in succ_r]
    fail = [r["anchor_len"] for r in fail_r]
    z, p, auc = mann_whitney(succ, fail)
    print(f"  anchor length: SUCCESS median {statistics.median(succ):.0f} chars (n={len(succ)}, "
          f"{sum(1 for r in succ_r if r['lines'] <= 1) / len(succ_r):.0%} single-line) vs "
          f"LOST median {statistics.median(fail):.0f} (n={len(fail)}, "
          f"{sum(1 for r in fail_r if r['lines'] <= 1) / len(fail_r):.0%} single-line)")
    print(f"    Mann-Whitney z={z:.2f}  p={p:.3g}  P(success longer)={auc:.2f}")
    censored = sum(1 for r in es if r["lost"] and not r["anchor_len"])
    print(f"    CENSORING: {censored} of the {sum(r['lost'] for r in es)} lost calls leaked no "
          "fragment at all, so the")
    print("    'LOST' median is conditioned on the subset where a fragment survived, and the")
    print("    reconstruction is a LOWER bound on what was attempted. Treat as suggestive.")

    # cost of the defect in the worse arm
    sm0 = {key(r): r for r in runs["E0"]["summary"]}
    spc0 = sum(s["wall_s"] for s in sm0.values()) / sum(s["n_calls"] for s in sm0.values())
    print(f"  cost in E0: {a} wasted calls = {a / sum(s['n_calls'] for s in sm0.values()):.1%} of all calls "
          f"= {a * spc0:.0f}s total = {a * spc0 / 48:.1f}s/task at {spc0:.2f}s/call")

    print()
    print("=" * 76)
    print("SECTION 3  Q1: empty patch <=> no edit ever landed             [MEASURED]")
    print("=" * 76)
    tot_never, tot_allfail = 0, 0
    for name, run in runs.items():
        sm = {key(r): r for r in run["summary"]}
        att, ok = edit_outcome(run)
        empty = [t for t, s in sm.items() if s.get("patch_empty")]
        never = sum(1 for t in empty if not att.get(t))
        allfail = sum(1 for t in empty if att.get(t) and not ok.get(t))
        tot_never += never
        tot_allfail += allfail
        print(f"{name}: EMPTY n={len(empty)}; landed an edit anyway: "
              f"{sum(ok.get(t, False) for t in empty)}")
        print(f"    never attempted an edit:            {never:2d}  (needs a forcing function)")
        print(f"    attempted, every attempt failed:    {allfail:2d}  (needs edit recovery)")
    print(f"POOLED over 35 empty patches: {tot_never} never attempted, {tot_allfail} all-attempts-failed")

    print()
    print("=" * 76)
    print("SECTION 4  Q2: is the E0 -> E3 see-saw real? PAIRED            [MEASURED]")
    print("=" * 76)
    s0 = {key(r): r for r in runs["E0"]["summary"]}
    s3 = {key(r): r for r in runs["E3"]["summary"]}
    res0 = {key(r): resolved(r) for r in runs["E0"]["tasks"]}
    res3 = {key(r): resolved(r) for r in runs["E3"]["tasks"]}
    att0, ok0 = edit_outcome(runs["E0"])
    att3, ok3 = edit_outcome(runs["E3"])
    common = sorted(set(res0) & set(res3))
    print(f"  the two runs share {len(common)} task ids, so EVERY contrast below is paired")

    def paired(label, f0, f3):
        b = sum(1 for t in common if f0(t) and not f3(t))
        c = sum(1 for t in common if not f0(t) and f3(t))
        print(f"  {label:32s} E0-only {b:2d}  E3-only {c:2d}  "
              f"exact McNemar p = {mcnemar_exact(b, c):.4f}")

    paired("resolved", lambda t: res0[t], lambda t: res3[t])
    paired("empty patch", lambda t: s0[t].get("patch_empty"), lambda t: s3[t].get("patch_empty"))
    paired("produced a patch", lambda t: not s0[t].get("patch_empty"),
           lambda t: not s3[t].get("patch_empty"))
    paired("never attempted an edit", lambda t: not att0.get(t), lambda t: not att3.get(t))
    paired("attempted, all edits failed", lambda t: att0.get(t) and not ok0.get(t),
           lambda t: att3.get(t) and not ok3.get(t))
    p0 = [t for t in common if not s0[t].get("patch_empty")]
    p3 = [t for t in common if not s3[t].get("patch_empty")]
    k0, k3 = sum(res0[t] for t in p0), sum(res3[t] for t in p3)
    print(f"  resolve-among-producers {k0}/{len(p0)} vs {k3}/{len(p3)} UNPAIRED: "
          f"Fisher p = {fisher_exact(k0, len(p0) - k0, k3, len(p3) - k3):.4f}")
    flips = sum(1 for t in common
                if bool(s0[t].get("patch_empty")) != bool(s3[t].get("patch_empty")))
    disc = sum(1 for t in common if res0[t] != res3[t])
    print(f"  churn: {flips}/{len(common)} tasks flip empty-patch status, "
          f"{disc}/{len(common)} flip resolved status")

    print()
    print("=" * 76)
    print("SECTION 5  Q5: selection arithmetic   [draws MEASURED, rest MODELLED]")
    print("=" * 76)
    draws = [4, 7, 6, 8, 8, 7, 7]      # scored submissions; #2 was the BLANK timeout
    m, v = statistics.mean(draws), statistics.variance(draws)
    p = m / 58
    binvar = 58 * p * (1 - p)
    print(f"  7 scored draws {draws}: mean {m:.3f}  var {v:.3f}  sd {math.sqrt(v):.3f}")
    print(f"  sd under INDEPENDENT binomial(58, {p:.4f}) = {math.sqrt(binvar):.3f}")
    lo, hi = var_ci(v, len(draws))
    print(f"  95% CI for the single-draw sd from n=7: [{math.sqrt(lo):.3f}, {math.sqrt(hi):.3f}]")
    print(f"  => implied rho in [{max(0.0, 1 - hi / binvar):.3f}, {max(0.0, 1 - lo / binvar):.3f}] "
          "-- the CI spans the whole range, so rho is NOT identified by 7 draws")
    print("  CAVEAT: the 7 draws are 7 DIFFERENT configs, so 1.380 bounds pure draw noise")
    print("          FROM ABOVE (it also contains real between-config differences).")
    rho_hat = max(0.0, 1 - v / binvar)
    print(f"  point estimate rho_hat = 1 - var/binvar = {rho_hat:.3f}")
    print("  MODELLED E[max of N draws] at theta = 6.714 (reps=3000, seed fixed):")
    for rho in (0.0, 0.50, rho_hat):
        e, h = max_stats(6.714, rho, 3000, rng, n_list=(17, 44),
                         thresholds=((38, 14), (38, 11)))
        print(f"    rho={rho:.2f}: E[max17]={e[17]:5.2f}  E[max44]={e[44]:5.2f}  "
              f"P(max38>=14)={h[(38, 14)]:.3f}  P(max38>=11)={h[(38, 11)]:.3f}")
    print("  MODELLED theta solving E[max of 17] = 14 (our best board score so far):")
    for rho in (0.0, 0.50, rho_hat):
        lo_t, hi_t = 4.0, 22.0
        for _ in range(11):
            mid = (lo_t + hi_t) / 2
            e, _ = max_stats(mid, rho, 1200, rng, n_list=(17,))
            if e[17] < 14:
                lo_t = mid
            else:
                hi_t = mid
        th = (lo_t + hi_t) / 2
        print(f"    rho={rho:.2f}: theta ~ {th:.1f} tasks of 58 (= {th / 58:.3f} score)")

    print()
    print("=" * 76)
    print("SECTION 6  Q3/Q4: power    [base rates MEASURED, power MODELLED]")
    print("=" * 76)
    n_edit = len(r3)
    base_k = c
    base3 = base_k / n_edit
    print("  PRIMARY endpoint: edit_file argument-loss rate.")
    print(f"  The comparator ALREADY EXISTS and is not re-run: E3's measured {base_k}/{n_edit}")
    print(f"  = {base3:.1%} on the very config we ship. So a new arm is tested against a FIXED")
    print("  2x2 column, which is why even a small new arm has usable power.")
    for n_new, label in ((n_edit, f"dev-48 (~{n_edit} calls)"),
                         (max(1, round(n_edit * 8 / 48)), f"smoke-8 (~{round(n_edit * 8 / 48)} calls)")):
        for target in (0.00, 0.02, 0.05, 0.09, 0.12):
            hit = 0
            for _ in range(3000):
                k = random.binomialvariate(n_new, target)
                if fisher_exact(k, n_new - k, base_k, n_edit - base_k) < 0.05:
                    hit += 1
            print(f"    {label:22s} true post-fix rate {target:5.0%}: power {hit / 3000:.3f}")
    print(f"  SECONDARY endpoint: paired resolve count. Measured discordance {disc}/48.")
    for delta in (2, 4, 6, 8, 10):
        hit = 0
        for _ in range(3000):
            b = c2 = 0
            q = min(1.0, 0.5 + delta / (2 * disc))
            for _ in range(disc):
                if random.random() < q:
                    c2 += 1
                else:
                    b += 1
            if mcnemar_exact(b, c2) < 0.05:
                hit += 1
        print(f"    true effect +{delta:2d} tasks/48: power {hit / 3000:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
