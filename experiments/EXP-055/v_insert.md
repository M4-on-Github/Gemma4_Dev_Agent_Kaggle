Three edits to `prompts/system.md` section 4, one variable (the post-edit check is required and a broken edited file is repaired).

1. Insert after the first bullet ("After the edit, run at most one focused check: ..."):

- Your last tool call before `submit_patch` must be that check, run after your last edit. Run it as one command with no scratch file: the named test file, or `python -c "import <module>"` for the module you changed. If the output shows a `SyntaxError`, `IndentationError`, `NameError` or `ImportError` that points into a file you edited, fix that file with one `edit_file`, run the same command once more, then submit.

2. In the fourth bullet, delete the words "import errors," so it reads:

- If it fails because of missing fixtures or pre-existing breakage, ignore it. Do not repair tests and do not install packages.

3. In the fifth bullet, delete "or you skipped it" so it reads:

- Call `submit_patch` after that, even when the local check is red. A local green test is not the grader.
