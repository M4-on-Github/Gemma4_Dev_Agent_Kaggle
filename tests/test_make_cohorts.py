from pathlib import Path

import make_cohorts as M


def flat(chosen: dict) -> set[str]:
    return {t for ids in chosen.values() for t in ids}


def test_cohort_sizes_and_disjointness(synthetic_tasks: Path):
    by_repo = M.load_task_ids(synthetic_tasks)
    cohorts, warnings = M.build_cohorts(by_repo, exclude=set(), seed=20261013,
                                        dev_spec=M.DEFAULT_DEV, held_spec=M.DEFAULT_HELD)
    dev, held, smoke = flat(cohorts["dev-48"]), flat(cohorts["held-out-24"]), flat(cohorts["smoke-8"])
    assert len(dev) == 48 and len(held) == 24 and len(smoke) == 8
    assert not dev & held
    assert smoke <= dev
    assert cohorts["dev-48"] == {"fastapi/fastapi": cohorts["dev-48"]["fastapi/fastapi"], **{k: v for k, v in cohorts["dev-48"].items() if k != "fastapi/fastapi"}}
    assert {k: len(v) for k, v in cohorts["dev-48"].items()} == M.DEFAULT_DEV
    # httpx has one task: held-out cannot get it -> shortfall filled from the largest repo and a warning
    assert any("encode/httpx" in w for w in warnings)


def test_deterministic_and_exclusion(synthetic_tasks: Path):
    by_repo = M.load_task_ids(synthetic_tasks)
    a, _ = M.build_cohorts(by_repo, exclude=set(), seed=1, dev_spec=M.DEFAULT_DEV, held_spec=M.DEFAULT_HELD)
    b, _ = M.build_cohorts(by_repo, exclude=set(), seed=1, dev_spec=M.DEFAULT_DEV, held_spec=M.DEFAULT_HELD)
    assert a == b
    victim = sorted(flat(a["dev-48"]))[0]
    c, _ = M.build_cohorts(by_repo, exclude={victim}, seed=1, dev_spec=M.DEFAULT_DEV, held_spec=M.DEFAULT_HELD)
    assert victim not in flat(c["dev-48"]) | flat(c["held-out-24"])


def test_cli_writes_files(synthetic_tasks: Path, tmp_path: Path):
    out = tmp_path / "cohorts"
    excl = tmp_path / "excl.txt"
    excl.write_text("# gold failures\nfastapi_1000\n")
    assert M.main(["--tasks", str(synthetic_tasks), "--exclude", str(excl), "--out", str(out)]) == 0
    ids = M.read_cohort(out / "dev-48.txt")
    assert len(ids) == 48 and "fastapi_1000" not in ids
    header = (out / "dev-48.txt").read_text().splitlines()[0]
    assert "seed=20261013" in header and "excluded=1" in header
