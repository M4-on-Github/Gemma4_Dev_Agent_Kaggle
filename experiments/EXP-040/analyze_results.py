#!/usr/bin/env python3
"""EXP-040 results: validity checks, endpoints E1-E12 and the cost figure, as defined in
experiments/EXP-040-voting-v1-e4b-smoke8.md sections 3, 4 and 4.1, plus the paired per-task view against
EXP-033 and the smoke-8 subset of EXP-038.

Inputs (read as data; run with `python -I -X utf8`):
  runs/EXP-040-v1/{task_results.jsonl, summary.jsonl, gemma4-exp040-v1.log, traces/}
  runs/EXP-033-e4b/runs/EXP-033-e4b/task_results.jsonl, runs/EXP-038-e4b-dev48/task_results.jsonl
  experiments/cohorts/smoke-8.txt, experiments/EXP-040/tally.py (the pre-registered recompute)
Output: experiments/EXP-040/results.json, holding task ids, counts, letters, voter indices, temperatures and
seconds only. No vote, candidate, proposer or actor text is written (plan.md:52, the hygiene ruling of 2026-11-05).
E5 (A) is a hand judgement and is not computed here; section 9 records it.
"""
from __future__ import annotations

import importlib.util
import json
import re
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "runs/EXP-040-v1"
LOG = RUN / "gemma4-exp040-v1.log"
REF033 = ROOT / "runs/EXP-033-e4b/runs/EXP-033-e4b/task_results.jsonl"
REF038 = ROOT / "runs/EXP-038-e4b-dev48/task_results.jsonl"
SMOKE8 = ROOT / "experiments/cohorts/smoke-8.txt"
OUT = ROOT / "experiments/EXP-040/results.json"

TIME_CAP_S, CALL_CAP, TURN_CAP, WALL_BAR_S, COMPACT_TOK = 480.0, 28, 200, 140.0, 14336
SERVED_MODEL = "gemma-4-e4b-it-qat-w4a16-ct"

_spec = importlib.util.spec_from_file_location("tally", ROOT / "experiments/EXP-040/tally.py")
T = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(T)

_ISSUE = re.compile(r"^[ \t*]*ISSUE:", re.MULTILINE)
_VOTER = re.compile(r"^voter_(\d\d)$")


def jl(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def ids_of(p: Path) -> list[str]:
    return [x.strip() for x in p.read_text(encoding="utf-8").splitlines() if x.strip() and not x.lstrip().startswith("#")]


def author(step: dict) -> str:
    return (step.get("extra") or {}).get("author") or ""


def ts(step: dict):
    return (step.get("extra") or {}).get("timestamp")


def extract_rounds_contiguous(trace: dict) -> list[dict]:
    """Defect fix found at analysis (section 9): tally.extract_rounds opens a new pass only at voter_01's step,
    so in a restart pass the replies that complete before voter_01's are written into the previous pass. Here a
    pass is a maximal run of consecutive voter steps; cands and actor_first_text as in tally.extract_rounds."""
    rounds, cands, cur, prev_voter = [], None, None, False
    for step in trace.get("steps", []):
        if step.get("source") != "agent":
            prev_voter = False
            continue
        a, msg = author(step), step.get("message") or ""
        m = _VOTER.match(a)
        if m:
            if not prev_voter:
                cur = {"cands": cands, "vote_texts": [None] * T.N_VOTERS, "actor_first_text": None, "ts": []}
                rounds.append(cur)
            k = int(m.group(1))
            if 1 <= k <= T.N_VOTERS:
                cur["vote_texts"][k - 1] = msg
            cur["ts"].append(ts(step))
            prev_voter = True
            continue
        prev_voter = False
        if a == "proposer" and not step.get("tool_calls"):
            cands = msg
        if a == "actor" and cur is not None and cur["actor_first_text"] is None:
            cur["actor_first_text"] = msg
    return rounds


def trace_view(trace: dict) -> dict:
    """Counts and timings of one trace; no text leaves this function except booleans."""
    steps = trace.get("steps", [])
    agent_steps = [s for s in steps if s.get("source") == "agent"]
    model_calls = [s for s in agent_steps if s.get("metrics")]
    authors = {author(s) for s in agent_steps}
    voters = sorted({int(m.group(1)) for a in authors if (m := _VOTER.match(a))})
    models = sorted({str(s.get("model_name") or "") for s in agent_steps})
    # passes: maximal runs of consecutive voter steps (see extract_rounds_contiguous)
    passes, cur, prev_voter = [], None, False
    for s in agent_steps:
        a = author(s)
        m = _VOTER.match(a)
        if m:
            if not prev_voter:
                cur = {"voter_ts": [], "prompt_tokens": []}
                passes.append(cur)
            cur["voter_ts"].append(ts(s))
            if s.get("metrics"):
                cur["prompt_tokens"].append(s["metrics"].get("prompt_tokens"))
        prev_voter = bool(m)
    # the proposer's last step before the first voter, and the actor's first model call after it
    first_voter_i = next((i for i, s in enumerate(agent_steps) if _VOTER.match(author(s))), None)
    prop_before = [s for s in agent_steps[: first_voter_i or 0] if author(s) == "proposer"]
    prop_final_ts = ts(prop_before[-1]) if prop_before else None
    prop_final_text = next((s.get("message") or "" for s in reversed(prop_before) if not s.get("tool_calls")), "")
    actor_after = [s for s in agent_steps[(first_voter_i or 0):] if author(s) == "actor"]
    actor_first = next((s for s in actor_after if s.get("metrics")), None)
    actor_any_stated = [T.stated_winner(s.get("message") or "") for s in actor_after]
    harness = [s for s in steps if s.get("source") == "user"]
    t0 = ts(harness[0]) if harness else None
    p1 = passes[0] if passes else None
    vt = [x for x in (p1["voter_ts"] if p1 else []) if x is not None]
    return {
        "agent_steps": len(agent_steps),
        "model_calls_with_metrics": len(model_calls),
        "voters_seen": voters,
        "has_proposer": "proposer" in authors,
        "has_actor": "actor" in authors,
        "model_names_e4b_only": all(SERVED_MODEL in m for m in models if m),
        "passes": len(passes),
        "proposer_final_has_issue_line": bool(_ISSUE.search(prop_final_text)),
        "voter_prompt_tokens_pass1": [min(p1["prompt_tokens"]), max(p1["prompt_tokens"])] if p1 and p1["prompt_tokens"] else None,
        "actor_first_prompt_tokens": (actor_first or {}).get("metrics", {}).get("prompt_tokens") if actor_first else None,
        "actor_first_msg_nonempty": bool(actor_first and (actor_first.get("message") or "").strip()),
        "actor_stated_winner_any_msg_pass1": next((x for x in actor_any_stated if x), None),
        "max_prompt_tokens": max((s["metrics"].get("prompt_tokens") or 0 for s in model_calls), default=0),
        "proposer_stage_s": round(prop_final_ts - t0, 1) if (prop_final_ts and t0) else None,
        "vote_stage_first_to_last_voter_s": round(max(vt) - min(vt), 2) if vt else None,
        "vote_stage_proposer_final_to_last_voter_s": round(max(vt) - prop_final_ts, 2) if (vt and prop_final_ts) else None,
    }


def main() -> None:
    rows = jl(RUN / "task_results.jsonl")
    summ = {r["task_id"]: r for r in jl(RUN / "summary.jsonl")}
    ids = ids_of(SMOKE8)
    log = json.loads(LOG.read_text(encoding="utf-8"))
    log_text = "\n".join(e.get("data", "") for e in log)
    served = re.search(r"model: (\S+) -> /kaggle/input/models/", log_text)
    vllm = re.search(r"vLLM up in ([\d.]+)s", log_text)
    span_s = float(log[-1]["time"])

    per = {}
    for r in rows:
        tid = r["instance_id"]
        trace = json.loads((RUN / "traces" / f"trace_{tid}.json").read_text(encoding="utf-8"))
        sc = T.score_trace(trace)
        f = sc["first"] or {}
        tv = trace_view(trace)
        s = summ.get(tid, {})
        fixed = [T.score_round(rd) for rd in extract_rounds_contiguous(trace)]
        cf = fixed[0] if fixed else {}
        later = [{"C": x["C"], "parseable": x["parseable"], "winner": x["winner"], "P1": x["P1"], "D": x["D"],
                  "lead": x["lead"], "rule": x["rule"], "malformed_by_bucket": x["malformed_by_bucket"]}
                 for x in fixed[1:]]
        per[tid] = {
            "resolved": bool(r["resolved"]),
            "wall_s": r["duration_s"],
            "error_empty": r["error"] in (None, ""),
            "status": r["status"],
            "harness_llm_calls": r["llm_calls"],
            "tool_calls": r["tool_calls"],
            "patch_nonempty": (r.get("patch_chars") or 0) > 0,
            "summary_n_turns": s.get("n_turns"),
            "n_calls": s.get("n_calls"),
            "n_malformed": s.get("n_malformed"),
            "compactions": s.get("compactions"),
            "time_cap_hit": s.get("time_cap_hit"),
            "calls_cap_hit": s.get("calls_cap_hit"),
            "C": f.get("C"), "letters": f.get("letters"), "votes": f.get("votes"), "parseable": f.get("parseable"),
            "W": f.get("winner"), "P1": f.get("P1"), "D": f.get("D"), "rule": f.get("rule"), "lead": f.get("lead"),
            "counts": f.get("counts"), "stated_winner_first_actor_msg": f.get("stated_winner"),
            "malformed_by_bucket": f.get("malformed_by_bucket"),
            "fixed": {"C": cf.get("C"), "votes": cf.get("votes"), "parseable": cf.get("parseable"), "W": cf.get("winner"),
                      "P1": cf.get("P1"), "D": cf.get("D"), "rule": cf.get("rule"), "lead": cf.get("lead"),
                      "counts": cf.get("counts"), "stated_winner": cf.get("stated_winner"),
                      "malformed_by_bucket": cf.get("malformed_by_bucket"), "passes": len(fixed)},
            "later_passes": later,
            **tv,
        }

    walls = [p["wall_s"] for p in per.values()]
    firsts = list(per.values())
    buckets = {b: {"n": 0, "malformed": 0, "absent": 0} for b in T.BUCKETS}
    for p in firsts:
        for b, c in (p["malformed_by_bucket"] or {}).items():
            for k in c:
                buckets[b][k] += c[k]

    fx = [p["fixed"] for p in firsts]
    fbuckets = {b: {"n": 0, "malformed": 0, "absent": 0} for b in T.BUCKETS}
    for q in fx:
        for b, c in (q["malformed_by_bucket"] or {}).items():
            for k in c:
                fbuckets[b][k] += c[k]
    corrected = {
        "note": "pass 1 with passes segmented as maximal runs of consecutive voter steps (defect in tally.extract_rounds, section 9)",
        "tasks_differing_from_as_written": sorted(t for t, p in per.items() if p["fixed"]["votes"] != p["votes"]),
        "per_task": {t: {k: p["fixed"][k] for k in ("C", "parseable", "W", "P1", "D", "lead", "rule", "counts", "passes")}
                     for t, p in per.items()},
        "C_ge_2": sum((q["C"] or 0) >= 2 for q in fx),
        "voted_ge_12": sum((q["parseable"] or 0) >= 12 for q in fx),
        "D_true": sum(q["D"] is True for q in fx),
        "D_undefined_p1_invalid": sum(q["D"] is None for q in fx),
        "tie_rule_used": sum(q["rule"] == "tie_lowest_voter" for q in fx),
        "D_lead_lt_3": sum(q["D"] is True and q["lead"] < 3 for q in fx),
        "D_lead_ge_3": sum(q["D"] is True and q["lead"] >= 3 for q in fx),
        "leads": {t: p["fixed"]["lead"] for t, p in per.items()},
        "unanimous_all_16": sum(q["lead"] == T.N_VOTERS for q in fx),
        "unanimous_with_C_ge_2": sum(q["lead"] == T.N_VOTERS and (q["C"] or 0) >= 2 for q in fx),
        "stated_matches_W": sum(q["stated_winner"] == q["W"] for q in fx),
        "E12_malformed_by_bucket_pass1": fbuckets,
    }

    def ref(path: Path) -> dict:
        return {r["instance_id"]: {"resolved": bool(r["resolved"]), "wall_s": r["duration_s"]} for r in jl(path)
                if r["instance_id"] in ids}

    r033, r038 = ref(REF033), ref(REF038)

    def paired(refd: dict) -> dict:
        shared = [t for t in ids if t in refd and t in per]
        both = [t for t in shared if refd[t]["resolved"] and per[t]["resolved"]]
        ref_only = [t for t in shared if refd[t]["resolved"] and not per[t]["resolved"]]
        v1_only = [t for t in shared if per[t]["resolved"] and not refd[t]["resolved"]]
        return {
            "n_shared": len(shared),
            "ref_resolved": sum(refd[t]["resolved"] for t in shared),
            "v1_resolved": sum(per[t]["resolved"] for t in shared),
            "both": both, "ref_only": ref_only, "v1_only": v1_only,
            "ref_mean_wall_s": round(statistics.mean(refd[t]["wall_s"] for t in shared), 1),
            "v1_mean_wall_s": round(statistics.mean(per[t]["wall_s"] for t in shared), 1),
            "per_task_wall_s": {t: [refd[t]["wall_s"], per[t]["wall_s"]] for t in shared},
            "v1_slower_on": sum(per[t]["wall_s"] > refd[t]["wall_s"] for t in shared),
        }

    out = {
        "validity": {
            "rows": len(rows),
            "ids_equal_smoke8": sorted(per) == sorted(ids),
            "errors_empty": sum(p["error_empty"] for p in firsts),
            "status_success": sum(p["status"] == "SUCCESS" for p in firsts),
            "served_model_line": served.group(1) if served else None,
            "trace_model_names_e4b_only": all(p["model_names_e4b_only"] for p in firsts),
            "vllm_up_s": float(vllm.group(1)) if vllm else None,
            "tasks_with_proposer_16_voters_actor": sum(p["has_proposer"] and p["has_actor"] and p["voters_seen"] == list(range(1, 17)) for p in firsts),
            "summary_json_resolved": json.loads((RUN / "summary.json").read_text(encoding="utf-8")).get("resolved"),
        },
        "row0": {
            "crashes": sum(not p["error_empty"] or p["status"] != "SUCCESS" for p in firsts),
            "tasks_with_12_parseable_pass1": sum((p["parseable"] or 0) >= 12 for p in firsts),
        },
        "E1_C": {"per_task": {t: p["C"] for t, p in per.items()}, "C_ge_2": sum((p["C"] or 0) >= 2 for p in firsts)},
        "E2_parseable": {"per_task": {t: p["parseable"] for t, p in per.items()},
                         "voted_ge_12": sum((p["parseable"] or 0) >= 12 for p in firsts)},
        "E3_D": {"per_task": {t: p["D"] for t, p in per.items()},
                 "D_true": sum(p["D"] is True for p in firsts),
                 "D_undefined_p1_invalid": sum(p["D"] is None for p in firsts),
                 "W_P1": {t: [p["W"], p["P1"]] for t, p in per.items()}},
        "E4_tie": {"tie_rule_used": sum(p["rule"] == "tie_lowest_voter" for p in firsts),
                   "stated_winner_first_actor_msg": {t: p["stated_winner_first_actor_msg"] for t, p in per.items()},
                   "stated_matches_W_first_msg": sum(p["stated_winner_first_actor_msg"] == p["W"] for p in firsts),
                   "stated_winner_any_actor_msg_pass1": {t: p["actor_stated_winner_any_msg_pass1"] for t, p in per.items()},
                   "stated_any_matches_W": sum(p["actor_stated_winner_any_msg_pass1"] == p["W"] for p in firsts),
                   "stated_any_mismatch_W": sum(p["actor_stated_winner_any_msg_pass1"] not in (None, p["W"]) for p in firsts)},
        "E6_F11": {"proposer_final_has_issue_line": {t: p["proposer_final_has_issue_line"] for t, p in per.items()},
                   "issue_line_tasks": sum(p["proposer_final_has_issue_line"] for p in firsts),
                   "voter_prompt_tokens_pass1": {t: p["voter_prompt_tokens_pass1"] for t, p in per.items()},
                   "actor_first_msg_nonempty": sum(p["actor_first_msg_nonempty"] for p in firsts),
                   "actor_first_prompt_tokens": {t: p["actor_first_prompt_tokens"] for t, p in per.items()},
                   "actor_first_over_compaction_threshold": sum((p["actor_first_prompt_tokens"] or 0) >= COMPACT_TOK for p in firsts)},
        "E7_passes_turns": {"passes": {t: p["passes"] for t, p in per.items()},
                            "tasks_more_than_one_pass": sum(p["passes"] > 1 for p in firsts),
                            "harness_llm_calls": {t: p["harness_llm_calls"] for t, p in per.items()},
                            "trace_agent_steps": {t: p["agent_steps"] for t, p in per.items()},
                            "max_trace_agent_steps": max(p["agent_steps"] for p in firsts),
                            "turn_cap": TURN_CAP,
                            "later_passes": {t: p["later_passes"] for t, p in per.items() if p["later_passes"]}},
        "E8_wall": {"per_task_s": {t: p["wall_s"] for t, p in per.items()},
                    "mean_s": round(statistics.mean(walls), 1),
                    "median_s": round(statistics.median(walls), 1),
                    "max_s": max(walls), "min_s": min(walls),
                    "over_140_mean": statistics.mean(walls) > WALL_BAR_S,
                    "tasks_past_480": sum(w > TIME_CAP_S for w in walls),
                    "time_cap_hit": sum(bool(p["time_cap_hit"]) for p in firsts),
                    "calls_cap_hit": sum(bool(p["calls_cap_hit"]) for p in firsts),
                    "turn_cap_hit": sum(p["agent_steps"] >= TURN_CAP for p in firsts),
                    "proposer_stage_s": {t: p["proposer_stage_s"] for t, p in per.items()},
                    "vote_stage_first_to_last_voter_s": {t: p["vote_stage_first_to_last_voter_s"] for t, p in per.items()},
                    "vote_stage_proposer_final_to_last_voter_s": {t: p["vote_stage_proposer_final_to_last_voter_s"] for t, p in per.items()}},
        "E9": {"malformed_calls": sum(p["n_malformed"] or 0 for p in firsts),
               "counted_calls": sum(p["n_calls"] or 0 for p in firsts),
               "compactions_per_task": {t: p["compactions"] for t, p in per.items()},
               "compactions_total": sum(p["compactions"] or 0 for p in firsts),
               "patch_nonempty": sum(p["patch_nonempty"] for p in firsts),
               "max_prompt_tokens": {t: p["max_prompt_tokens"] for t, p in per.items()}},
        "E10_resolves": {"resolved": sorted(t for t, p in per.items() if p["resolved"]),
                         "n": sum(p["resolved"] for p in firsts)},
        "E11_lead": {"per_task": {t: p["lead"] for t, p in per.items()},
                     "D_lead_lt_3": sum(p["D"] is True and p["lead"] < 3 for p in firsts),
                     "D_lead_ge_3": sum(p["D"] is True and p["lead"] >= 3 for p in firsts),
                     "unanimous_all_16": sum(p["lead"] == T.N_VOTERS for p in firsts),
                     "unanimous_with_C_ge_2": sum(p["lead"] == T.N_VOTERS and (p["C"] or 0) >= 2 for p in firsts),
                     "counts": {t: p["counts"] for t, p in per.items()}},
        "E12_malformed_by_bucket_pass1": buckets,
        "corrected_pass1": corrected,
        "malformed_votes_by_voter_pass1": {t: [i + 1 for i, v in enumerate(p["votes"] or []) if v is None]
                                           for t, p in per.items() if p["votes"] and None in p["votes"]},
        "cost": {"kernel_log_span_s": round(span_s, 1), "gpu_h": round(span_s / 3600, 3),
                 "tasks_s": round(sum(walls), 1), "overhead_s": round(span_s - sum(walls), 1)},
        "paired_vs_EXP033": paired(r033),
        "paired_vs_EXP038_smoke8_subset": paired(r038),
    }
    OUT.write_text(json.dumps(out, indent=1, sort_keys=False) + "\n", encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("validity", "row0", "cost")}, indent=1))
    print(json.dumps({k: v for k, v in corrected.items() if k != "per_task"}))
    print(json.dumps({"E8_mean": out["E8_wall"]["mean_s"], "E8_max": out["E8_wall"]["max_s"],
                      "p033": {k: v for k, v in out["paired_vs_EXP033"].items() if k != "per_task_wall_s"},
                      "p038": {k: v for k, v in out["paired_vs_EXP038_smoke8_subset"].items() if k != "per_task_wall_s"}}, indent=1))
    print("wrote", OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
