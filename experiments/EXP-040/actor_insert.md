## Team plan and votes
Before you started, a reader examined the repository and proposed lettered candidate edits, and sixteen independent voters each picked one. The reader's calls count toward your 28. Their output follows.

Reader report:
{cands?}

Votes, in voter order (a valid vote is a line of the form PICK: followed by one capital letter):
voter 1: {vote_01?}
voter 2: {vote_02?}
voter 3: {vote_03?}
voter 4: {vote_04?}
voter 5: {vote_05?}
voter 6: {vote_06?}
voter 7: {vote_07?}
voter 8: {vote_08?}
voter 9: {vote_09?}
voter 10: {vote_10?}
voter 11: {vote_11?}
voter 12: {vote_12?}
voter 13: {vote_13?}
voter 14: {vote_14?}
voter 15: {vote_15?}
voter 16: {vote_16?}

Tally the votes before your first tool call. Count only valid votes whose letter is one of the reader's candidates; ignore every other line. The winner is the letter with the most votes. If two or more letters tie for the most votes, the winner is the tied letter picked by the lowest-numbered voter among them. If there is no valid vote, the winner is candidate A. If the reader report is empty, ignore this section and follow the rest of the prompt. State the counts and the winner in one sentence that ends with the words "The winner is X." where X is the letter. Then start from the winning candidate: open the region of its file that you need with `read_file` and make its edit as your first edit, adjusting the exact lines to match the code. Do not switch to another candidate unless the winning one cannot be applied, and if you do, say why in one sentence. The edit-by-call-12 rule and every rule below still apply.
