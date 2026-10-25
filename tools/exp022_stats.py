#!/usr/bin/env python3
"""EXP-022 statistics: every number in experiments/EXP-022-direction-review.md that is not copied from an
earlier document is produced here. Standard library only (plus tools/run_forensics.py for the exact tests).

    python -I -X utf8 tools/exp022_stats.py --e0 RUN_DIR --exp3 RUN_DIR [--lb-csv FILE] [--seed 22]

RUN_DIR is a directory holding task_results.jsonl and traces/ (runs/ is gitignored; in the maintainer's main
checkout these are runs/E0-dev48-baseline/runs/E0-dev48-baseline and
runs/exp003_public_budget_dev48/runs/EXP-003-public-budget-dev48). --lb-csv is a Kaggle public-leaderboard CSV
(read as data only).

Sections
  A  task-level overlap of the two existing dev-48 resolved sets (the mandatory deterministic-core test)
  B  what that table can and cannot distinguish (core vs continuous heterogeneity), profile likelihood
  C  the six-submission dispersion test redone against a heterogeneity-aware null
  D  LB power / error rates for the pre-registered EXT-19 reading, and the winner's-curse table
  E  dev-48 paired (McNemar) power
  F  wall-clock: projection of 120-task hours and the price of a 4.5-minute cap
  G  leaderboard tier table (optional)
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import random
import statistics as st
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_forensics import fisher_exact_2x2, mcnemar_exact  # noqa: E402

N_LB = 58
LB_SCORES = [4, 7, 6, 8, 8, 7]          # submissions #1,#3,#4,#5,#6,#7 (floor(k/58*100)/100 = .06 .12 .10 .13 .13 .12)


# ----------------------------------------------------------------------------------------------- helpers
def load_results(run: Path) -> dict[str, dict]:
    out = {}
    for line in (run / "task_results.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            out[r["instance_id"]] = r
    return out


def comb(n: int, k: int) -> int:
    return math.comb(n, k) if 0 <= k <= n else 0


def hyper_ge(x: int, N: int, K: int, n: int) -> float:
    """P(X >= x), X ~ Hypergeometric(population N, K successes, n draws)."""
    return sum(comb(K, i) * comb(N - K, n - i) for i in range(x, min(K, n) + 1)) / comb(N, n)


def chi2_cdf(x: float, df: int) -> float:
    """Regularised lower incomplete gamma P(df/2, x/2) by series (adequate for the small df used here)."""
    if x <= 0:
        return 0.0
    a, z = df / 2.0, x / 2.0
    term = total = 1.0 / a
    for n in range(1, 400):
        term *= z / (a + n)
        total += term
        if term < 1e-14 * total:
            break
    return total * math.exp(-z + a * math.log(z) - math.lgamma(a))


def pb_pmf(ps: list[float]) -> list[float]:
    """Exact Poisson-binomial pmf by dynamic programming."""
    pmf = [1.0]
    for p in ps:
        nxt = [0.0] * (len(pmf) + 1)
        for k, v in enumerate(pmf):
            nxt[k] += v * (1 - p)
            nxt[k + 1] += v * p
        pmf = nxt
    return pmf


def shift_to_sum(base: list[float], target: float) -> list[float]:
    """Logit-shift a vector of probabilities so that it sums to `target` (keeps every p inside (0,1))."""
    eps = 1e-9
    lg = [math.log(max(eps, min(1 - eps, p)) / (1 - max(eps, min(1 - eps, p)))) for p in base]
    lo, hi = -40.0, 40.0
    for _ in range(80):
        mid = (lo + hi) / 2
        s = sum(1 / (1 + math.exp(-(g + mid))) for g in lg)
        lo, hi = (mid, hi) if s < target else (lo, mid)
    mid = (lo + hi) / 2
    return [1 / (1 + math.exp(-(g + mid))) for g in lg]


def beta_vectors(rng: random.Random, n: int, mu: float, rho: float, m: int) -> list[list[float]]:
    """m draws of an n-vector of task solve-probabilities, p_i ~ Beta with mean mu and across-run ICC rho."""
    if rho <= 1e-9:
        return [[mu] * n for _ in range(m)]
    s = 1.0 / rho - 1.0
    a, b = max(1e-3, mu * s), max(1e-3, (1 - mu) * s)
    return [[rng.betavariate(a, b) for _ in range(n)] for _ in range(m)]


def mixed_pmf(rng: random.Random, n: int, theta: float, rho: float, m: int = 150) -> list[float]:
    """pmf of one run's count when the SUM of the task probabilities is theta and tasks are heterogeneous."""
    acc = [0.0] * (n + 1)
    for v in beta_vectors(rng, n, theta / n, rho, m):
        pm = pb_pmf(shift_to_sum(v, theta))
        for k, x in enumerate(pm):
            acc[k] += x / m
    return acc


def moments(pmf: list[float]) -> tuple[float, float]:
    mu = sum(k * p for k, p in enumerate(pmf))
    return mu, math.sqrt(sum((k - mu) ** 2 * p for k, p in enumerate(pmf)))


def tail(pmf: list[float], k: int) -> float:
    return sum(pmf[k:])


def h(title: str) -> None:
    print("\n" + "=" * 100 + f"\n{title}\n" + "=" * 100)


# ----------------------------------------------------------------------------------------------- A
def section_a(a: dict, b: dict, rng: random.Random) -> tuple[float, int]:
    h("A. TASK-LEVEL OVERLAP of the two existing dev-48 runs (E0 vs EXP-003), field `resolved` in task_results.jsonl")
    ids = sorted(set(a) & set(b))
    ra = {i for i in ids if a[i]["resolved"]}
    rb = {i for i in ids if b[i]["resolved"]}
    both, only_a, only_b = sorted(ra & rb), sorted(ra - rb), sorted(rb - ra)
    neither = sorted(set(ids) - ra - rb)
    n = len(ids)
    print(f"tasks in both runs: {n}   E0 resolved {len(ra)}   EXP-003 resolved {len(rb)}   union {len(ra | rb)}")
    print(f"\n                    EXP-003 resolved   EXP-003 not")
    print(f"  E0 resolved       {len(both):>8d}           {len(only_a):>5d}")
    print(f"  E0 not            {len(only_b):>8d}           {len(neither):>5d}")
    print(f"\nboth resolved ({len(both)}):   {both}")
    print(f"E0 only ({len(only_a)}):        {only_a}")
    print(f"EXP-003 only ({len(only_b)}):    {only_b}")
    print(f"neither ({len(neither)}):        {neither}")
    t = (len(both), len(only_a), len(only_b), len(neither))
    exp_both = len(ra) * len(rb) / n
    print(f"\nexpected 'both' if the runs were independent (hypergeometric mean): {exp_both:.3f}   observed {t[0]}")
    p_one = hyper_ge(t[0], n, len(ra), len(rb))
    print(f"P(overlap >= {t[0]}) one-sided hypergeometric : {p_one:.6f}")
    print(f"Fisher exact two-sided (tools/run_forensics)  : {fisher_exact_2x2(*t):.6f}")
    print(f"exact McNemar on the discordant pairs {t[1]}:{t[2]} (marginal symmetry, a different question): "
          f"{mcnemar_exact(t[1], t[2]):.4f}")
    or_ = (t[0] * t[3]) / (t[1] * t[2]) if t[1] * t[2] else float('inf')
    se = math.sqrt(sum(1 / x for x in t))
    print(f"odds ratio {or_:.2f}   Woolf 95% CI {math.exp(math.log(or_) - 1.96 * se):.2f} - {math.exp(math.log(or_) + 1.96 * se):.2f}")
    den = math.sqrt((t[0] + t[1]) * (t[2] + t[3]) * (t[0] + t[2]) * (t[1] + t[3]))
    phi = (t[0] * t[3] - t[1] * t[2]) / den
    boots = []
    for _ in range(4000):
        s = [rng.randrange(n) for _ in range(n)]
        xs = [(ids[i] in ra, ids[i] in rb) for i in s]
        c = Counter(xs)
        d = math.sqrt((c[(1, 1)] + c[(1, 0)]) * (c[(0, 1)] + c[(0, 0)]) * (c[(1, 1)] + c[(0, 1)]) * (c[(1, 0)] + c[(0, 0)]))
        if d:
            boots.append((c[(1, 1)] * c[(0, 0)] - c[(1, 0)] * c[(0, 1)]) / d)
    boots.sort()
    print(f"inter-run correlation phi (= across-run ICC of the 0/1 outcome) {phi:.3f}   task-bootstrap 95% CI "
          f"{boots[int(.025 * len(boots))]:.3f} - {boots[int(.975 * len(boots))]:.3f}   (n boot {len(boots)})")
    print(f"\nrepeat rates: P(also solved in EXP-003 | solved in E0) = {t[0]}/{len(ra)} = {t[0] / len(ra):.3f};"
          f"  P(also solved in E0 | solved in EXP-003) = {t[0]}/{len(rb)} = {t[0] / len(rb):.3f}")
    print(f"P(solved in EXP-003 | NOT solved in E0) = {t[2]}/{n - len(ra)} = {t[2] / (n - len(ra)):.3f}   "
          f"Jaccard {t[0] / len(ra | rb):.3f}")
    m = t[0]
    chap = (len(ra) + 1) * (len(rb) + 1) / (m + 1) - 1
    var = (len(ra) + 1) * (len(rb) + 1) * (len(ra) - m) * (len(rb) - m) / ((m + 1) ** 2 * (m + 2))
    print(f"capture-recapture (treat the runs as two 'captures' of the solvable set): Lincoln-Petersen "
          f"{len(ra) * len(rb) / m:.1f}, Chapman {chap:.1f} +/- {1.96 * math.sqrt(var):.1f} (95%, normal). "
          f"Assumes equal catchability, so it is a LOWER bound when tasks differ.")
    print()
    print("per repo (from the instance_id prefix; E0 / EXP-003 / union resolved of tasks):")
    repos = sorted({i.rsplit("_", 1)[0] for i in ids})
    for rp in repos:
        sub = [i for i in ids if i.rsplit("_", 1)[0] == rp]
        print(f"  {rp:10s} tasks {len(sub):>2d}   E0 {sum(1 for i in sub if i in ra):>2d}   EXP-003 {sum(1 for i in sub if i in rb):>2d}   union {sum(1 for i in sub if i in ra or i in rb):>2d}")
    return phi, n


# ----------------------------------------------------------------------------------------------- B
def section_b(a: dict, b: dict) -> None:
    h("B. WHAT THE 2x2 TABLE CAN AND CANNOT SEPARATE: a deterministic core (pi) vs continuous heterogeneity")
    ids = sorted(set(a) & set(b))
    n = len(ids)
    ra = sum(a[i]["resolved"] for i in ids)
    rb = sum(b[i]["resolved"] for i in ids)
    m = sum(a[i]["resolved"] and b[i]["resolved"] for i in ids)
    cells = [m, ra - m, rb - m, n - ra - rb + m]

    def ll(probs):
        return sum(c * math.log(max(1e-300, p)) for c, p in zip(cells, probs))

    p1, p2 = ra / n, rb / n
    ll_ind = ll([p1 * p2, p1 * (1 - p2), (1 - p1) * p2, (1 - p1) * (1 - p2)])
    ll_sat = ll([c / n for c in cells])
    g2 = 2 * (ll_sat - ll_ind)
    print(f"independent runs (2 parameters, p1={p1:.3f}, p2={p2:.3f}): logL {ll_ind:.3f};  saturated (3 df): logL {ll_sat:.3f}")
    print(f"likelihood-ratio G2 = {g2:.3f} on 1 df, P = {1 - chi2_cdf(g2, 1):.4f}   -> 'the runs are independent' is rejected")
    print("\nprofile over the core fraction pi (tasks that resolve with probability 1 in BOTH runs); the periphery is "
          "independent with run-specific rates:")
    print("  cell probs: both = pi + (1-pi) q1 q2 ; E0-only = (1-pi) q1 (1-q2) ; EXP3-only = (1-pi)(1-q1) q2 ; neither = (1-pi)(1-q1)(1-q2)")
    print("   pi     core tasks   best q1   best q2   logL      G2 vs saturated   inside 95% profile?")
    best = []
    for k in range(0, 49):
        pi = k / n
        if pi > cells[0] / n + 1e-12:
            break
        top = (-1e18, None, None)
        for i in range(0, 201):
            q1 = i / 200
            for j in range(0, 201):
                q2 = j / 200
                pr = [pi + (1 - pi) * q1 * q2, (1 - pi) * q1 * (1 - q2), (1 - pi) * (1 - q1) * q2, (1 - pi) * (1 - q1) * (1 - q2)]
                if min(pr) <= 0:
                    continue
                v = ll(pr)
                if v > top[0]:
                    top = (v, q1, q2)
        g = 2 * (ll_sat - top[0])
        best.append((k, g))
        print(f"  {pi:5.3f}   {k:3d}         {top[1]:.3f}     {top[2]:.3f}   {top[0]:8.3f}   {g:8.3f}          {'yes' if g < 3.841 else 'no'}")
    ok = [k for k, g in best if g < 3.841]
    print(f"\nconsistent core sizes (profile 95%): {min(ok)} to {max(ok)} of {n} tasks. The table cannot say whether the 'core' is a")
    print("sharp set of tasks or the upper tail of a smooth difficulty distribution: both give the same four cell probabilities.")
    print("A THIRD run (the C4 repeat of one configuration) is what separates them, because it measures within-config luck.")


# ----------------------------------------------------------------------------------------------- C
def section_c(phi: float, rng: random.Random) -> None:
    h("C. THE SIX-SUBMISSION DISPERSION TEST, re-done against the right null")
    k = LB_SCORES
    n = N_LB
    mean = st.mean(k)
    s2 = st.variance(k)
    p = sum(k) / (n * len(k))
    binom = n * p * (1 - p)
    x2 = (len(k) - 1) * s2 / binom
    print(f"scores {k}: mean {mean:.3f}, sample variance {s2:.3f}, pooled p {sum(k)}/{n * len(k)} = {p:.5f}")
    print(f"binomial expectation n p q = {binom:.3f}; X2 = {x2:.3f} on {len(k) - 1} df; P(X2 <= observed) = {chi2_cdf(x2, len(k) - 1):.3f} (low tail)")
    print("\nThe six runs score the SAME 58 tasks. Conditional on that fixed task set the count is Poisson-binomial, whose variance is")
    print("sum p_i(1-p_i) = n mu (1-mu) (1 - rho), strictly BELOW the binomial n mu (1-mu) whenever tasks differ in difficulty.")
    print("So 'variance below binomial' is what ordinary difficulty heterogeneity predicts; it is not evidence of a deterministic core.")
    print(f"\nsimulation: draw one 58-vector of task probabilities p_i ~ Beta(mean {p:.4f}, ICC rho), then six independent runs, "
          f"s2 = sample variance of the six counts ({20000} reps each).")
    print("  rho     E[s2]    P(s2 <= 2.267)   P(s2 >= 5.9)")
    reps = 20000
    for rho in (0.0, 0.25, 0.40, phi, 0.60, 0.75):
        if rho == 0:
            vecs = None
        cnt_le = cnt_ge = 0
        acc = 0.0
        for _ in range(reps):
            if rho == 0:
                ps = [p] * n
            else:
                s = 1.0 / rho - 1.0
                aa, bb = max(1e-3, p * s), max(1e-3, (1 - p) * s)
                ps = [rng.betavariate(aa, bb) for _ in range(n)]
            xs = [sum(1 for q in ps if rng.random() < q) for _ in range(6)]
            v = st.variance(xs)
            acc += v
            cnt_le += v <= s2 + 1e-9
            cnt_ge += v >= binom
        print(f"  {rho:5.3f}  {acc / reps:6.3f}   {cnt_le / reps:8.3f}         {cnt_ge / reps:8.3f}")
    print()
    print("moment-matching the 'core + iid periphery' model to the six LB scores (mean 6.667, s2 2.267): c always-solved tasks, the other 58-c")
    print("solve independently with prob q per run, so mean = c + (58-c) q and variance = (58-c) q (1-q). Post-hoc, two moments, one free parameter:")
    print("   c    q       mean    variance   (observed variance 2.267)")
    for c in range(0, 8):
        m = N_LB - c
        q = (st.mean(LB_SCORES) - c) / m
        print(f"  {c:2d}  {q:6.4f}  {c + m * q:6.3f}  {m * q * (1 - q):7.3f}")
    print("  -> variance 2.267 is matched at c of roughly 4 to 5: about two thirds of a typical run's resolves would be 'core', one third lottery.")
    print("     This is the same split as the dev-48 overlap (6/11 and 6/9 repeat), obtained from independent data, and it is a consistency check only:")
    print("     the LB variance cannot distinguish a sharp core from smooth heterogeneity (section C simulation above).")
    print("\nreading: at rho ~ the dev-48 inter-run correlation the observed 2.267 is an unremarkable draw. The 'low tail' (P=0.14) came from")
    print("comparing against a homogeneous binomial, which is the wrong null for a fixed task set.")


# ----------------------------------------------------------------------------------------------- D
def section_d(phi: float, rng: random.Random) -> dict:
    h("D. LEADERBOARD POWER for a single new draw (task set fixed, theta = expected count on these 58 tasks)")
    base = st.mean(LB_SCORES)
    print(f"baseline family: mean of our six scored draws = {base:.3f} tasks. Hypothesised theta for the EXT-19 replica:")
    thetas = [("H0 no transfer", base), ("H-low", 8.5), ("H1 field mode (0.18)", 10.4), ("H2 face value (0.22)", 12.8)]
    out = {}
    print("  rho = across-run task ICC. Columns are P(k >= t) for a single graded run.")
    for rho in (0.30, phi, 0.65):
        print(f"\n  rho = {rho:.2f}")
        print("  hypothesis              theta   sd     P(>=8)  P(>=9)  P(>=10) P(>=11) P(>=12) P(>=13)")
        for name, th in thetas:
            pm = mixed_pmf(rng, N_LB, th, rho)
            mu, sd = moments(pm)
            print(f"  {name:22s} {th:6.2f} {sd:5.2f}  " + "  ".join(f"{tail(pm, t):6.3f} " for t in (8, 9, 10, 11, 12, 13)))
            out[(round(rho, 2), name)] = pm
    pre = out[(round(phi, 2), "H0 no transfer")]
    print("\nPRE-REGISTERED READING (EXP-022 section 4.2), error rates at rho = %.2f:" % phi)
    print(f"  R-A  k >= 11 (score >= 0.18):  P under H0 = {tail(pre, 11):.4f}  (false-positive rate)")
    for name, th in thetas[1:]:
        print(f"                                  P under {name} (theta {th}) = {tail(out[(round(phi, 2), name)], 11):.3f}  (power)")
    print(f"  R-C  k <= 8  (score <= 0.13):  P under H0 = {1 - tail(pre, 9):.3f};  under H1 = {1 - tail(out[(round(phi, 2), 'H1 field mode (0.18)')], 9):.3f};"
          f"  under H2 = {1 - tail(out[(round(phi, 2), 'H2 face value (0.22)')], 9):.3f}")
    print(f"  R-B  k in 9..10:               P under H0 = {tail(pre, 9) - tail(pre, 11):.3f};  under H1 = "
          f"{tail(out[(round(phi, 2), 'H1 field mode (0.18)')], 9) - tail(out[(round(phi, 2), 'H1 field mode (0.18)')], 11):.3f}")
    print("\nlikelihood ratios P(outcome | H1) / P(outcome | H0) at rho = %.2f:" % phi)
    h1 = out[(round(phi, 2), "H1 field mode (0.18)")]
    h2 = out[(round(phi, 2), "H2 face value (0.22)")]
    for lo, hi, lab in ((0, 8, "k <= 8"), (9, 10, "k = 9-10"), (11, 58, "k >= 11")):
        a0, a1, a2 = (sum(x[lo:hi + 1]) for x in (pre, h1, h2))
        print(f"  {lab:9s}  P|H0 {a0:.4f}  P|H1 {a1:.4f}  P|H2 {a2:.4f}   LR(H1:H0) {a1 / a0 if a0 else float('inf'):7.2f}   LR(H2:H0) {a2 / a0 if a0 else float('inf'):7.2f}")
    # prior-weighted expectation
    prior = {"H0 no transfer": .35, "H-low": .30, "H1 field mode (0.18)": .25, "H2 face value (0.22)": .10}
    ev = sum(prior[nm] * th for nm, th in thetas)
    print(f"\nstated prior over theta (written before the draw): {prior}  -> prior mean theta {ev:.2f} tasks "
          f"(= {ev - base:+.2f} vs our six-draw mean)")
    mix = [sum(prior[nm] * out[(round(phi, 2), nm)][k] for nm, _ in thetas) for k in range(N_LB + 1)]
    print(f"prior-predictive probabilities of the graded count: P(k<=8)={1 - tail(mix, 9):.3f}, "
          f"P(9<=k<=10)={tail(mix, 9) - tail(mix, 11):.3f}, P(k>=11)={tail(mix, 11):.3f}")
    post = {nm: prior[nm] * sum(out[(round(phi, 2), nm)][11:]) for nm, _ in thetas}
    z = sum(post.values())
    print("posterior if k >= 11 is observed: " + ", ".join(f"{nm}: {v / z:.2f}" for nm, v in post.items()))
    post = {nm: prior[nm] * sum(out[(round(phi, 2), nm)][:9]) for nm, _ in thetas}
    z = sum(post.values())
    print("posterior if k <= 8 is observed:  " + ", ".join(f"{nm}: {v / z:.2f}" for nm, v in post.items()))

    print("\n-- MDE of one new draw against the six-draw baseline (two-sided alpha .05, power .80) --")
    for rho in (0.30, phi, 0.65):
        sd_new = moments(mixed_pmf(rng, N_LB, 10.0, rho))[1]
        sd_old = moments(mixed_pmf(rng, N_LB, base, rho))[1]
        se = math.sqrt(sd_new ** 2 + sd_old ** 2 / len(LB_SCORES))
        print(f"  rho {rho:.2f}: sd(new draw at theta=10) {sd_new:.2f}, sd(one baseline draw) {sd_old:.2f}, SE of (new - baseline mean) {se:.2f}, MDE = (1.96+0.84) x SE = {2.8 * se:.2f} tasks")

    se_c = math.sqrt(st.variance(LB_SCORES) * (1 + 1 / len(LB_SCORES)))
    print(f"  conditional (same 58 tasks, observed s2 = {st.variance(LB_SCORES):.3f}): SE = sqrt(s2 (1 + 1/6)) = {se_c:.2f}, MDE = 2.8 x SE = {2.8 * se_c:.2f} tasks;"
          f" one-sided alpha .05 / power .80: {(1.645 + 0.84) * se_c:.2f} tasks")

    h("D2. WINNER'S CURSE: expected best-of-N for a team whose every submission has the same theta (rho = %.2f)" % phi)
    print("  columns: expected leaderboard count (max of N graded runs); then P(max >= 13), P(max >= 14)")
    for th in (6.67, 8.0, 9.0, 10.0, 11.0, 12.0):
        row = []
        for nsub in (6, 17, 44):
            e = p13 = p14 = 0.0
            for v in beta_vectors(rng, N_LB, th / N_LB, phi, 120):
                pm = pb_pmf(shift_to_sum(v, th))
                cdf = [sum(pm[: k + 1]) for k in range(len(pm))]
                mx = [(cdf[k] ** nsub) - (cdf[k - 1] ** nsub if k else 0.0) for k in range(len(pm))]
                e += sum(k * x for k, x in enumerate(mx)) / 120
                p13 += sum(mx[13:]) / 120
                p14 += sum(mx[14:]) / 120
            row.append(f"N={nsub:2d}: E[max]={e:5.2f} P(>=13)={p13:.2f} P(>=14)={p14:.2f}")
        print(f"  theta {th:4.1f} ({th / N_LB:.3f}) | " + " | ".join(row))
    return out


# ----------------------------------------------------------------------------------------------- E
def section_e(phi: float, rng: random.Random) -> None:
    h("E. dev-48 PAIRED POWER (single run per arm, exact McNemar two-sided alpha .05), arm A at E0's 11 resolves")
    reps = 3000
    print("  true gain (tasks of 48)   power    mean discordant pairs")
    for delta in (0, 2, 3, 4, 6, 8, 10):
        sig = 0
        disc = 0.0
        for _ in range(reps):
            v = beta_vectors(rng, 48, 11 / 48, phi, 1)[0]
            pa = shift_to_sum(v, 11.0)
            pb = shift_to_sum(v, 11.0 + delta)
            xa = [rng.random() < q for q in pa]
            xb = [rng.random() < q for q in pb]
            bb = sum(1 for x, y in zip(xa, xb) if x and not y)
            cc = sum(1 for x, y in zip(xa, xb) if y and not x)
            disc += bb + cc
            if bb + cc and mcnemar_exact(bb, cc) < 0.05:
                sig += 1
        print(f"  {delta:>3d}                        {sig / reps:5.3f}    {disc / reps:5.2f}")
    print("  normal-approximation cross-check (paired difference of two proportions with inter-run correlation phi, n = 48, 80% power, two-sided .05):")
    for lab, pr, ph in (("resolve rate at p = .20, phi = .50", .20, .50), ("resolve rate at p = .20, phi = .30", .20, .30), ("empty-patch rate at p = .35, phi = .42", .35, .42)):
        se_ = math.sqrt(2 * pr * (1 - pr) * (1 - ph) / 48)
        print(f"    {lab}: SE {se_:.3f}, MDE {2.8 * se_:.3f} = {2.8 * se_ * 48:.1f} tasks of 48")
    print("  so the normal approximation (about 8 tasks) is optimistic against the exact-test simulation above (about 10), and the empty-patch rate is NOT a")
    print("  lower-noise metric than the resolve rate at n = 48. A second run per arm shrinks every MDE by sqrt(2).")


# ----------------------------------------------------------------------------------------------- F
def edit_times(run: Path, tid: str) -> list[float]:
    t = json.loads((run / "traces" / f"trace_{tid}.json").read_text(encoding="utf-8"))
    out = []
    for s in t["steps"]:
        for tc in s.get("tool_calls") or []:
            if tc["function_name"] in ("edit_file", "write_file"):
                out.append(tc["extra"]["elapsed_s"])
    return out


def section_f(runs: dict[str, Path]) -> None:
    h("F. WALL-CLOCK: projection and the price of the 4.5-minute cap (existing dev-48 traces)")
    rs = {n_: load_results(r_) for n_, r_ in runs.items()}
    (na, ra_), (nb, rb_) = list(rs.items())
    ids_ = sorted(set(ra_) & set(rb_))
    ea = {i for i in ids_ if not ra_[i].get("patch_chars")}
    eb = {i for i in ids_ if not rb_[i].get("patch_chars")}
    t_ = (len(ea & eb), len(ea - eb), len(eb - ea), len(ids_) - len(ea | eb))
    den_ = math.sqrt((t_[0] + t_[1]) * (t_[2] + t_[3]) * (t_[0] + t_[2]) * (t_[1] + t_[3]))
    print(f"empty-patch tasks: first run {len(ea)}, second run {len(eb)}, both {t_[0]}, only first {t_[1]}, only second {t_[2]}, neither {t_[3]}")
    print(f"  Fisher two-sided p = {fisher_exact_2x2(*t_):.2e}, phi = {(t_[0] * t_[3] - t_[1] * t_[2]) / den_:.3f}  (comparable to the resolve outcome's inter-run phi, so empty-patch is NOT more task-determined; its only advantage as a metric is the larger event count)")
    for name_, rr_, e_ in ((na, ra_, ea), (nb, rb_, eb)):
        ne = [i for i in ids_ if i not in e_]
        print(f"  {name_}: non-empty patches {len(ne)}, resolved among them {sum(rr_[i]['resolved'] for i in ne)} ({sum(rr_[i]['resolved'] for i in ne) / len(ne):.1%}); resolved among empty {sum(rr_[i]['resolved'] for i in e_)}")
    for name, run in runs.items():
        res = load_results(run)
        dur = [r["duration_s"] for r in res.values()]
        calls = [r["tool_calls"] for r in res.values()]
        empty = sum(1 for r in res.values() if not r.get("patch_chars"))
        print(f"\n{name}: n={len(res)} resolved={sum(r['resolved'] for r in res.values())} empty patch={empty} ({empty / len(res):.1%})")
        print(f"  duration_s mean {st.mean(dur):.1f} median {st.median(dur):.1f} max {max(dur):.1f};  tool_calls mean {st.mean(calls):.1f} median {st.median(calls):.1f} max {max(calls)}")
        print(f"  projected 120-task agent hours = 120 x mean = {120 * st.mean(dur) / 3600:.2f} h (excludes notebook start-up and model load)")
        resolved = [t for t, r in res.items() if r["resolved"]]
        last = {t: (max(edit_times(run, t)) if edit_times(run, t) else None) for t in resolved}
        late = [t for t, v in last.items() if v is not None and v > 270.0]
        print(f"  resolved tasks {len(resolved)}; last edit_file/write_file elapsed (s): " +
              ", ".join(f"{t}={v:.0f}" for t, v in sorted(last.items())))
        print(f"  resolved tasks whose LAST edit comes after 270 s (a 4.5-min cap would have cut them): {late} = {len(late)}/{len(resolved)}")


# ----------------------------------------------------------------------------------------------- G
def section_f2(runs: dict[str, Path]) -> None:
    h("F2. THE TIME GATE vs THE MEASURED RUNTIME MODEL (inputs cited from experiments/EXP-020-today-plan.md section 2.3, not re-measured here)")
    startup, setup, grade = 461.8, 3.3, 14.0
    print(f"measured inputs cited: startup {startup} s once, setup {setup} s/task, grading {grade} s/task; 120 hidden tasks; hard limit 12 h")
    print("  cap (min)   project gate 120*(cap+1.0 min)   measured-input hard bound 120*(cap+setup+grade)+startup   fits 12 h?")
    for cap in (4.0, 4.5, 5.0, 5.3, 5.5, 5.65, 6.0, 8.0):
        gate = 120 * (cap + 1.0) / 60
        hard = (120 * (cap * 60 + setup + grade) + startup) / 3600
        print(f"  {cap:7.2f}     {gate:6.2f} h {'(passes 11.0 h gate)' if gate <= 11.0 + 1e-9 else '(REJECTED by gate)':22s}   {hard:6.2f} h                                              {'yes' if hard <= 12 else 'NO'}")
    cap_max = ((12 * 3600 - startup) / 120 - setup - grade) / 60
    cap_11 = ((11 * 3600 - startup) / 120 - setup - grade) / 60
    print(f"  largest cap whose hard bound is <= 12.0 h: {cap_max:.2f} min;  <= 11.0 h: {cap_11:.2f} min (the gate's own 11.0 h line is reached at 4.5 min only because it prices setup at 60 s, 3.5x the measured 17.3 s)")
    for name, run in runs.items():
        res = load_results(run)
        sp = [r["duration_s"] / max(1, r["tool_calls"]) for r in res.values()]
        tot_d = sum(r["duration_s"] for r in res.values())
        tot_c = sum(r["tool_calls"] for r in res.values())
        print(f"  {name}: pooled seconds per tool call {tot_d / tot_c:.1f} -> a 270 s cap buys about {270 / (tot_d / tot_c):.0f} calls; a 480 s cap about {480 / (tot_d / tot_c):.0f}")


def section_g(path: Path) -> None:
    h("G. LEADERBOARD TIERS (public CSV, read as data)")
    rows = list(csv.DictReader(path.open(encoding="utf-8-sig")))
    sc = [float(r["Score"]) for r in rows]
    cnt = Counter(sc)
    cum = 0
    print(f"teams {len(rows)}   median score {st.median(sc):.2f}")
    print("  score  tasks  teams  cumulative>=  share>=   successive ratio")
    prev = None
    for s in sorted(cnt, reverse=True)[:12]:
        cum += cnt[s]
        k = next(k for k in range(0, 59) if math.floor(k / 58 * 100 + 1e-9) / 100 == round(s, 2))
        print(f"  {s:.2f}  {k:>3d}   {cnt[s]:>5d}  {cum:>6d}       {cum / len(rows):6.1%}   {'' if prev is None else f'{cnt[s] / prev:.2f}'}")
        prev = cnt[s]
    print()
    print("POST-HOC (not pre-registered): submission count by tier. If the top is partly best-of-N selection, higher tiers should have submitted more.")
    print("  score  teams  mean subs  median subs")
    bytier = {}
    for r in rows:
        bytier.setdefault(round(float(r["Score"]), 2), []).append(int(r["SubmissionCount"]))
    for sc_ in sorted(bytier, reverse=True)[:10]:
        v = bytier[sc_]
        print(f"  {sc_:.2f}  {len(v):>5d}  {st.mean(v):8.2f}  {st.median(v):8.1f}")

    def ranks(xs):
        order = sorted(range(len(xs)), key=lambda i: xs[i])
        rk = [0.0] * len(xs)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
                j += 1
            for t in range(i, j + 1):
                rk[order[t]] = (i + j) / 2 + 1
            i = j + 1
        return rk

    xs, ys = [float(r["Score"]) for r in rows], [float(r["SubmissionCount"]) for r in rows]
    rx, ry = ranks(xs), ranks(ys)
    mx, my = st.mean(rx), st.mean(ry)
    rho_s = sum((a - mx) * (b - my) for a, b in zip(rx, ry)) / math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    print(f"  Spearman(score, submission count) over {len(rows)} teams = {rho_s:.3f}  (confounded: persistent and capable teams both submit more; it shows that selection is available, not that it explains the top)")
    ours = [r for r in rows if r["TeamName"] == "RainM4"]
    if ours:
        o = float(ours[0]["Score"])
        ahead = sum(1 for x in sc if x > o)
        tied = sum(1 for x in sc if x == o)
        print(f"\nRainM4: score {o:.2f}, listed rank {ours[0]['Rank']}, strictly ahead {ahead} ({ahead / len(sc):.1%}), tied {tied}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--e0", type=Path, required=True)
    ap.add_argument("--exp3", type=Path, required=True)
    ap.add_argument("--lb-csv", type=Path)
    ap.add_argument("--seed", type=int, default=22)
    a = ap.parse_args()
    rng = random.Random(a.seed)
    r0, r3 = load_results(a.e0), load_results(a.exp3)
    phi, _ = section_a(r0, r3, rng)
    section_b(r0, r3)
    section_c(phi, rng)
    section_d(phi, rng)
    section_e(phi, rng)
    section_f({"E0 (4.5 min / 45 calls / thinking 256)": a.e0, "EXP-003 (8 min / 28 calls / thinking 4096)": a.exp3})
    section_f2({"E0 (thinking 256)": a.e0, "EXP-003 (thinking 4096)": a.exp3})
    if a.lb_csv:
        section_g(a.lb_csv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
