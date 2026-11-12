#!/usr/bin/env python3
"""EXP-078 design figures (zero GPU, no data read): binomial and Fisher tail probabilities behind the blind rows.

Reproduces the figures of experiments/EXP-074/critic.md (the 0.2 replicate table) from counts alone:
  base empties 19 of 96 (EXP-038 10, EXP-077 9); first 0.2 draw 5 of 48 (EXP-075)
  base arg-loss tasks 10 of 96 (EXP-038 6, EXP-077 4); first 0.2 draw 1 of 48
Usage: python -I -X utf8 experiments/EXP-078/power.py
"""
from __future__ import annotations

from math import comb

N = 48


def pmf(k: int, n: int, p: float) -> float:
    return comb(n, k) * p ** k * (1 - p) ** (n - k)


def cdf(k: int, n: int, p: float) -> float:
    return sum(pmf(i, n, p) for i in range(k + 1))


def fisher_lower(a: int, n1: int, b: int, n2: int) -> float:
    """One-sided Fisher: P(X <= a) for X the arm count in a 2x2 with margins fixed (hypergeometric)."""
    m = a + b
    tot = n1 + n2
    return sum(comb(n1, i) * comb(n2, m - i) for i in range(0, a + 1) if m - i <= n2) / comb(tot, m)


def main() -> int:
    p0 = 19 / 96
    print(f"empties: P(Eo <= 4 | p = 19/96, n 48) = {cdf(4, N, p0):.3f}")
    print(f"empties: one-sided Fisher, 4 of 48 against 19 of 96 = {fisher_lower(4, N, 19, 96):.3f}")
    p1 = 5 / 48
    print(f"power: P(Eo <= 4 | p = 5/48) = {cdf(4, N, p1):.3f}")
    print(f"middle band: P(5 <= Eo <= 8 | p = 5/48) = {cdf(8, N, p1) - cdf(4, N, p1):.3f}")
    print(f"not replicated under p = 5/48: P(Eo >= 9) = {1 - cdf(8, N, p1):.3f}")
    print(f"under the base p = 19/96: P(Eo <= 4) {cdf(4, N, p0):.3f}; P(5..8) {cdf(8, N, p0) - cdf(4, N, p0):.3f}; "
          f"P(9..15) {cdf(15, N, p0) - cdf(8, N, p0):.3f}; P(>= 16) {1 - cdf(15, N, p0):.3f}")
    q0 = 10 / 96
    print(f"arg-loss tasks: P(<= 1 | p = 10/96) = {cdf(1, N, q0):.3f}")
    print(f"arg-loss tasks: one-sided Fisher, 1 of 48 against 10 of 96 = {fisher_lower(1, N, 10, 96):.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
