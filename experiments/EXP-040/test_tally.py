"""Unit cases for experiments/EXP-040/tally.py. Synthetic data only. Run: python -m pytest experiments/EXP-040/test_tally.py"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import tally as T  # noqa: E402

L = ["A", "B", "C", "D"]


def pad(votes):
    return votes + [None] * (T.N_VOTERS - len(votes))


def test_clear_majority():
    votes = pad(["B"] * 9 + ["A"] * 4 + ["C"] * 3)
    r = T.tally(votes, L)
    assert r["winner"] == "B" and r["rule"] == "majority" and r["n_valid"] == 16


def test_tie_goes_to_lowest_numbered_voter_among_tied():
    # A: voters 3 and 4, B: voters 1 and 2, C: one vote. B and A tie at 2; the lowest-numbered voter among them is voter 1 (B).
    votes = pad(["B", "B", "A", "A", "C"])
    r = T.tally(votes, L)
    assert r["tied"] == ["A", "B"] and r["winner"] == "B" and r["rule"] == "tie_lowest_voter"
    # Same counts, A picked first: A wins.
    r2 = T.tally(pad(["A", "C", "B", "A", "B"]), L)
    assert r2["tied"] == ["A", "B"] and r2["winner"] == "A"


def test_tie_ignores_a_lower_voter_whose_letter_is_not_tied():
    # voter 1 picked C (one vote, not tied for most), A and B tie at 2: winner is the tied letter picked earliest, A (voter 2).
    r = T.tally(pad(["C", "A", "B", "A", "B"]), L)
    assert r["winner"] == "A" and r["rule"] == "tie_lowest_voter"


def test_no_valid_vote_falls_back_to_a():
    r = T.tally(pad([]), L)
    assert r["winner"] == "A" and r["rule"] == "fallback" and r["n_valid"] == 0


def test_parse_vote_accepts_only_exact_pick_lines():
    assert T.parse_vote("PICK: B", L) == "B"
    assert T.parse_vote("  PICK:C  \n", L) == "C"
    assert T.parse_vote("PICK: b", L) is None
    assert T.parse_vote("I pick B", L) is None
    assert T.parse_vote("PICK: B because it is simplest", L) is None
    assert T.parse_vote("", L) is None and T.parse_vote(None, L) is None
    assert T.parse_vote("my reasoning\nPICK: D", L) == "D"


def test_letter_outside_candidate_set_is_ignored():
    assert T.parse_vote("PICK: E", ["A", "B"]) is None
    assert T.parse_vote("PICK: E\nPICK: B", ["A", "B"]) == "B"
    r = T.tally([None, "A", None], ["A", "B"])
    assert r["winner"] == "A" and r["n_valid"] == 1


def test_candidate_letters():
    text = "ISSUE: x\nA. edit a.py\nB) edit b.py\n**C.** edit c.py\nA. dup\nnot a candidate E. foo"
    assert T.candidate_letters(text) == ["A", "B", "C"]
    assert T.candidate_letters("ISSUE: only") == []
    assert T.candidate_letters(None) == []


def test_d_definition():
    votes = pad(["A"] + ["B"] * 10 + ["A"] * 3)
    assert T.d_flag(votes, L) is True  # winner B differs from voter 1's A
    assert T.d_flag(pad(["B"] * 12 + ["A"] * 2), L) is False  # winner B equals voter 1's B
    assert T.d_flag(pad([None] + ["B"] * 5), L) is None  # voter 1 invalid: undefined, reported apart


def test_lead_tie_is_zero():
    assert T.lead(pad(["B", "B", "A", "A", "C"]), L) == 0  # B and A tie at 2: top minus runner-up is 0
    assert T.lead(pad(["A"] * 8 + ["B"] * 8), L) == 0
    assert T.lead(pad([]), L) == 0  # no valid vote


def test_lead_unanimous_all_16_is_16_and_margins():
    assert T.lead(["B"] * 16, L) == 16
    assert T.lead(["B"] * 15 + [None], L) == 15  # one malformed vote: the lead is over valid votes
    assert T.lead(pad(["A"] * 9 + ["B"] * 5 + ["C"] * 2), L) == 4  # 9 - 5
    assert T.lead(pad(["A"] * 10 + ["B"] * 4), L) == 6
    assert T.lead(["A"] * 8 + ["B"] * 5 + ["C"] * 3, L) == 3  # lead 3 is the 'ge 3' side


def test_lead_ignores_letters_outside_the_set():
    assert T.lead(["E"] * 10 + ["A"] * 6, ["A", "B"]) == 6  # the E votes are not valid, A alone has 6


def test_temperature_buckets_as_built():
    assert [T.voter_temperature(k) for k in (1, 6, 7, 11, 12, 16)] == [0.2, 0.6, 0.68, 1.0, 1.08, 1.4]
    assert [T.temperature_bucket(k) for k in range(1, 17)] == (
        ["le_0.6"] * 6 + ["gt_0.6_le_1.0"] * 5 + ["gt_1.0"] * 5
    )


def test_malformed_vote_counts_in_its_buckets_denominator():
    texts = ["PICK: A"] * 16
    texts[0] = "I think A"  # voter 1, bucket le_0.6, malformed
    texts[7] = ""  # voter 8, 0.76, an empty reply is recorded and malformed
    texts[15] = "PICK: Z"  # voter 16, 1.40, a letter outside the set
    r = T.malformed_by_bucket(texts, ["A", "B"])
    assert r["le_0.6"] == {"n": 6, "malformed": 1, "absent": 0}
    assert r["gt_0.6_le_1.0"] == {"n": 5, "malformed": 1, "absent": 0}
    assert r["gt_1.0"] == {"n": 5, "malformed": 1, "absent": 0}


def test_absent_voter_is_neither_counted_nor_malformed():
    texts = ["PICK: A"] * 16
    texts[13] = None  # voter 14, bucket gt_1.0, no recorded step
    r = T.malformed_by_bucket(texts, ["A"])
    assert r["gt_1.0"] == {"n": 4, "malformed": 0, "absent": 1}


def test_score_round_carries_lead_and_buckets():
    cands = "ISSUE: x\nA. a\nB. b"
    steps = [_step("proposer", cands)] + [_step("voter_%02d" % i, "PICK: B") for i in range(1, 17)]
    f = T.score_trace({"steps": steps})["first"]
    assert f["lead"] == 16 and f["D"] is False
    assert all(v["malformed"] == 0 for v in f["malformed_by_bucket"].values())


def test_stated_winner():
    assert T.stated_winner("Tally: B 9, A 7. The winner is B.") == "B"
    assert T.stated_winner("Winner: C") is None  # requires the phrase 'winner is' or '='
    assert T.stated_winner("winner is candidate D") == "D"
    assert T.stated_winner(None) is None


def _step(author, msg, calls=False):
    s = {"source": "agent", "message": msg, "extra": {"author": author}}
    if calls:
        s["tool_calls"] = [{"function_name": "read_file"}]
    return s


def test_extraction_fixture_two_passes():
    cands = "ISSUE: fix x\nA. edit a.py in f\nB. edit b.py in g"
    steps = [
        {"source": "system", "message": "sys"},
        {"source": "user", "message": "issue"},
        _step("proposer", "reading", calls=True),
        _step("proposer", cands),
    ]
    picks = ["B", "A", "B", "B", "garbage"] + ["B"] * 11
    for i, p in enumerate(picks, 1):
        steps.append(_step("voter_%02d" % i, p if p == "garbage" else "PICK: " + p))
    steps.append(_step("actor", "Tally: B 14, A 1. The winner is B.", calls=True))
    # a restart pass: proposer and voters again, voter 1 now picks A and the rest A, B alternately
    steps.append(_step("proposer", cands))
    for i in range(1, 17):
        steps.append(_step("voter_%02d" % i, "PICK: " + ("A" if i % 2 else "B")))
    steps.append(_step("actor", "The winner is A.", calls=True))

    s = T.score_trace({"steps": steps})
    assert s["passes"] == 2
    f = s["first"]
    assert f["C"] == 2 and f["letters"] == ["A", "B"]
    assert f["parseable"] == 15 and f["P1"] == "B" and f["winner"] == "B" and f["D"] is False
    assert f["stated_winner"] == "B" and f["rule"] == "majority"
    second = s["all"][1]
    assert second["rule"] == "tie_lowest_voter" and second["winner"] == "A" and second["P1"] == "A"
    assert second["stated_winner"] == "A"


def test_trace_without_votes():
    s = T.score_trace({"steps": [_step("swe_agent", "hi", calls=True)]})
    assert s["passes"] == 0 and s["first"] is None
