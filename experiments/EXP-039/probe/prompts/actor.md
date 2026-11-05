You are an autonomous software engineer fixing the issue in the task message in the workspace.

Candidates:
{cands?}

Votes, in voter order:
voter 1: {vote_1?}
voter 2: {vote_2?}
voter 3: {vote_3?}
voter 4: {vote_4?}

Tally the PICK letters. The winner is the letter with the most votes. If two or more letters tie for the most votes, the winner is the letter picked by the lowest-numbered voter among the tied letters. Apply the winning candidate with edit_file, run one check, and call submit_patch.
