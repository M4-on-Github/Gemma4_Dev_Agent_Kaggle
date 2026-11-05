---
id: kg-755554-fastapi-14186-unresolvable
topic_id: 755554
title: [fastapi_14186] Task unresolvable: required test skipped due to @needs_pydanticv1 and Pydantic v2 setup (Aridio Silva)
author: Aridio Silva (participant)
author_role: participant
credibility: medium
topics: [grading, test-dependencies, pydantic, rich]
first_seen: 2026-11-05
last_checked: 2026-11-05
---

## Summary
A participant reports that public task fastapi_14186 cannot pass with any patch on the public setup, because two required tests carry skip markers that cannot both hold. Also reports rich_3486 with opposing skipif markers. Posted 2026-11-03 22:28:16 UTC, 0 votes, 0 comments at read time. Credibility [M]: a specific derivation from the harness that can be re-checked by any participant; no host reply.

## Claims made (quoted numbers)
- Setup: "the public tasks.jsonl, the task snapshot, the official sandbox/setup.py with the dataset wheels, and the swegemma verifier. The task's own reference patch was applied, and it applies cleanly. The test command exits with code 0."
- "the verifier derives 7 required tests from test_patch" (the task has no FAIL_TO_PASS / PASS_TO_PASS). Among them: test_model_description_escaped_with_formfeed (2 params) with @needs_pydanticv1; test_invalid_response_model_field_pv1 with @needs_pydanticv1; test_model_field_default_required with @needs_pydanticv2; three tests in tests/test_compat.py with @needs_py_lt_314; one with none.
- "needs_pydanticv1 and needs_pydanticv2 are defined in tests/utils.py as skipif(PYDANTIC_V2) and skipif(not PYDANTIC_V2). No single environment can run all required tests, so a skipped required test makes the task impossible to resolve with any patch."
- Public setup detail: "The dataset ships both pydantic-1.10.15 and pydantic-2.13.4, but deduplicate_wheels in sandbox/setup.py keeps only the highest version. Pydantic 2.13.4 is therefore always installed, and the JUnit report shows the three v1-only nodes as skipped: requires Pydantic v1."
- Verifier message: "Required test node did not pass: test_model_description_escaped_with_formfeed".
- rich_3486: "test_traceback_finely_grained_missing has @pytest.mark.skipif(sys.version_info.minor >= 11, …) and test_traceback_finely_grained has @pytest.mark.skipif(sys.version_info.minor < 11, …). One of them is always skipped on any Python version."

## Possible claims for us
- fastapi_14186 and rich_3486 are unresolvable under the grader as derived here; they should be excluded from any dev-48 headroom claim, or reported as a separate class. Our §1g already lists rich_3486 with opposing skipif markers; this thread is an independent derivation of the same. [M; suggested for the cohort check]
- The deduplicate_wheels rule (highest pydantic version kept) is the public setup's behaviour according to this author; we have not verified it in our own run. [I]

## Files
None.

## Updates
- 2026-11-05: first full read (saved topic text). The digest lists it under suggested claims.
