"""EXP-040 offline recompute of the vote tally, the tie rule, C, D and the stated winner.

Pure functions of the texts a trace records. No GPU, no network, no imports outside the standard library.
The actor tallies the votes in its own head (the tally cannot be code in a declarative config); this module
recomputes the same rule from the vote texts so that D (the vote changed a pick) and tie-rule fidelity are
measured by code after the run, never by reading.

Rule, identical to the sentence in candidate-v1/prompts/actor.md and to EXP-039 Q4:
  - a vote is valid when a line of the voter's text is exactly  PICK: X  (X one capital letter) and X is one
    of the proposer's candidate letters; the first such line counts, every other line is ignored;
  - the winner is the letter with the most valid votes;
  - on a tie for most, the winner is the tied letter picked by the lowest-numbered voter among them;
  - with no valid vote the winner is A.

Trace schema (ATIF-v1.7): trace["steps"] is a list; an agent step has source "agent", a "message" and
extra.author naming the ADK agent ("proposer", "voter_01" .. "voter_16", "actor").
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

N_VOTERS = 16
FALLBACK = "A"

_PICK_LINE = re.compile(r"^[ \t]*PICK:[ \t]*([A-Z])[ \t]*$", re.MULTILINE)
_CAND_LINE = re.compile(r"^[ \t]*\**([A-D])\**[.)]\**[ \t]", re.MULTILINE)
_STATED = re.compile(r"winner\s+(?:is|=|:)\s*(?:candidate\s+)?\**([A-D])\b", re.IGNORECASE)
_VOTER = re.compile(r"^voter_(\d\d)$")


def candidate_letters(cands_text):
    """Distinct lettered candidates A to D at the start of a line of the proposer's text, in order of appearance."""
    seen = []
    for m in _CAND_LINE.finditer(cands_text or ""):
        if m.group(1) not in seen:
            seen.append(m.group(1))
    return seen


def parse_vote(text, letters):
    """The first line that is exactly PICK: X with X in letters, else None (malformed or out-of-set votes count for nothing)."""
    for m in _PICK_LINE.finditer(text or ""):
        if m.group(1) in letters:
            return m.group(1)
    return None


def tally(votes, letters):
    """votes: list ordered voter 1 .. N of a letter or None. Returns counts, the winner and how it was decided."""
    counts = Counter(v for v in votes if v is not None and v in letters)
    n_valid = sum(counts.values())
    if n_valid == 0:
        return {"counts": {}, "n_valid": 0, "winner": FALLBACK, "tied": [], "rule": "fallback"}
    top = max(counts.values())
    tied = sorted(k for k, c in counts.items() if c == top)
    if len(tied) == 1:
        return {"counts": dict(counts), "n_valid": n_valid, "winner": tied[0], "tied": tied, "rule": "majority"}
    first_voter = {k: min(i for i, v in enumerate(votes) if v == k) for k in tied}
    winner = min(tied, key=lambda k: first_voter[k])
    return {"counts": dict(counts), "n_valid": n_valid, "winner": winner, "tied": tied, "rule": "tie_lowest_voter"}


def d_flag(votes, letters):
    """D for one task: True when the tally winner differs from voter 1's pick, None when voter 1's vote is not valid."""
    p1 = votes[0] if votes else None
    if p1 is None or p1 not in letters:
        return None
    return tally(votes, letters)["winner"] != p1


def stated_winner(actor_text):
    """Heuristic: the letter the actor names as the winner in its first message, or None. Fidelity of the actor's own count."""
    m = _STATED.search(actor_text or "")
    return m.group(1).upper() if m else None


def extract_rounds(trace):
    """Group a trace into vote rounds. A round starts when voter_01's step appears (a restart pass gives a second round).

    Each round: cands (the last proposer step without a tool call before it), vote_texts (16 entries, None when absent)
    and actor_first_text (the first actor agent step message after the round's last voter step).
    """
    rounds = []
    cands = None
    current = None
    for step in trace.get("steps", []):
        if step.get("source") != "agent":
            continue
        author = (step.get("extra") or {}).get("author", "")
        msg = step.get("message") or ""
        if author == "proposer" and not step.get("tool_calls"):
            cands = msg
            continue
        m = _VOTER.match(author)
        if m:
            k = int(m.group(1))
            if k == 1 or current is None:
                current = {"cands": cands, "vote_texts": [None] * N_VOTERS, "actor_first_text": None}
                rounds.append(current)
            if 1 <= k <= N_VOTERS:
                current["vote_texts"][k - 1] = msg
            continue
        if author == "actor" and current is not None and current["actor_first_text"] is None:
            current["actor_first_text"] = msg
    return rounds


def score_round(rnd):
    letters = candidate_letters(rnd["cands"])
    votes = [parse_vote(t, letters) for t in rnd["vote_texts"]]
    res = tally(votes, letters)
    return {
        "C": len(letters),
        "letters": letters,
        "votes": votes,
        "parseable": sum(1 for v in votes if v is not None),
        "winner": res["winner"],
        "rule": res["rule"],
        "tied": res["tied"],
        "counts": res["counts"],
        "P1": votes[0] if votes else None,
        "D": d_flag(votes, letters),
        "stated_winner": stated_winner(rnd["actor_first_text"]),
    }


def score_trace(trace):
    rounds = extract_rounds(trace)
    scored = [score_round(r) for r in rounds]
    return {"passes": len(scored), "first": scored[0] if scored else None, "all": scored}


def main(argv):
    """Usage: tally.py <traces_dir>. Prints one JSON line per trace and a summary of C, D, parseable and tie use."""
    traces = sorted(Path(argv[1]).glob("trace_*.json"))
    rows = []
    for p in traces:
        s = score_trace(json.loads(p.read_text(encoding="utf-8")))
        f = s["first"]
        rows.append({"task": p.stem[len("trace_"):], "passes": s["passes"], **(f or {})})
        print(json.dumps(rows[-1]))
    firsts = [r for r in rows if "C" in r]
    print(json.dumps({
        "tasks": len(rows),
        "C_ge_2": sum(1 for r in firsts if r["C"] >= 2),
        "D": sum(1 for r in firsts if r["D"] is True),
        "D_undefined_p1_invalid": sum(1 for r in firsts if r["D"] is None),
        "tasks_with_12_parseable": sum(1 for r in firsts if r["parseable"] >= 12),
        "tie_rule_used": sum(1 for r in firsts if r["rule"] == "tie_lowest_voter"),
        "stated_winner_matches": sum(1 for r in firsts if r["stated_winner"] == r["winner"]),
    }))


if __name__ == "__main__":
    main(sys.argv)
