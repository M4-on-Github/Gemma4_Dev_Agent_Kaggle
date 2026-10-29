# Upload approvals

Only the user writes here. No agent's write guard allows this folder.

To approve proposal `knowledge/submissions/S-NNN.md` (NNN = the `submissions.md` row the upload becomes), create
`approvals/S-NNN.txt` containing the SHA-256 of the exact file to upload, as stated in the proposal:

```powershell
(Get-FileHash out\submission.zip -Algorithm SHA256).Hash.ToLower() | Out-File -Encoding ascii approvals\S-NNN.txt
```

or in Git Bash:

```bash
sha256sum out/submission.zip | cut -d" " -f1 > approvals/S-NNN.txt
```

The submit hook (`.claude/hooks/guard_submit.py`) refuses any `kaggle competitions submit` whose file hash is not in the
matching approval file, whose message does not name the S-NNN, or that is not issued by the submitter agent. The
upload must be named `submission.zip`. The paper-track Writeup is submitted by the user through the Kaggle UI and
needs no approval file.

Rows 1-11 of `submissions.md` predate this folder; their proposals are migrated under `knowledge/submissions/` with
`status: submitted` and no approval file.
