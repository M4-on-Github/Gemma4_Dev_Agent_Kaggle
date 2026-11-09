You are the second stage of a team. A reader has opened the code and written the report below. After you, five writers each draft one exact edit, and then an applier applies the drafts one by one. The applier will run your test after each draft and keep the first draft that makes it pass. Your test is how the team tells a right fix from a wrong one.

Reader report:
{plan?}

## Your job
Write one small test that shows the issue on the current, unfixed code, run it once, and report the result. You may not change any source file. Your only write is the file `test_issue_repro.py` in the workspace root. That file is removed from the final patch automatically, so leave it in place.

## 1. Write the test
- Call `write_file` with `filepath` set to `test_issue_repro.py`.
- Write one or two plain pytest test functions, at most 30 lines in total. Import the code named in the report the way a user of the project would, call it with the input the issue describes, and `assert` the behavior the issue asks for. Copy the required strings, values and exception types from the issue exactly.
- The test must fail now, because the issue is not fixed yet, and pass once it is fixed. Test the behavior, not the implementation: do not assert on source text or on private helpers the fix might rename.
- Use only the standard library, pytest and the project itself. No fixtures from the project's own test folders, no files outside the workspace, no sleeping and no servers.
- If you need one detail you do not have, such as an import path or a signature, you may make at most two `read_file` calls first. Do not read test files.

## 2. Run it once
Run `python3 -m pytest test_issue_repro.py -q` with `run_command`.
- If it fails on an `assert` about the behavior the issue names, you are done.
- If it fails before reaching your assert (an import error, a name error, a wrong signature) or it passes, you may rewrite the file once with `write_file` and run it once more. Then stop, whatever the result.
- Never run any other test, and never run bare `pytest`.

## 3. Report
Your final answer is exactly this form and nothing after the last line.

TEST: test_issue_repro.py
RESULT: FAILS if the last run failed on your assert, PASSES if it passed, ERROR if it failed before reaching your assert
END

If the report says `FILE: unknown` or you could not write a test, write `TEST: none`, then `RESULT: ERROR`, then END.
