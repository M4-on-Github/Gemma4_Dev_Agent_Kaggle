#!/usr/bin/env python3
"""EXP-078 results (zero GPU): experiments/EXP-077/pair.py run over four E4B dev-48 draws.

Runs: EXP-038-e4b-dev48 and EXP-077-base (temperature 1.0), EXP-075-t02 and EXP-078-t02r (temperature 0.2).
The pairs are EXP-078-t02r against each of the three earlier runs (the section 3 recorded-only tables), plus the
two earlier pairs, so the four-draw union and the per-run class counts come from one call. Nothing is pooled.
pair.py is loaded as is; only its RUNS and PAIRS lists are replaced.
Prints ids, class letters and counts only.
Usage: python -I -X utf8 experiments/EXP-078/pair4.py
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("pair77", ROOT / "experiments" / "EXP-077" / "pair.py")
P = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P)

P.RUNS = ["EXP-038-e4b-dev48", "EXP-077-base", "EXP-075-t02", "EXP-078-t02r"]
P.PAIRS = [("EXP-038-e4b-dev48", "EXP-078-t02r"), ("EXP-077-base", "EXP-078-t02r"), ("EXP-075-t02", "EXP-078-t02r"),
           ("EXP-038-e4b-dev48", "EXP-077-base"), ("EXP-038-e4b-dev48", "EXP-075-t02")]

if __name__ == "__main__":
    raise SystemExit(P.main())
