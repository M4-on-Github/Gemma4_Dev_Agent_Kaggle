You are writer 3 of 5 independent writers. Your angle: the guard. Identify the one input or state the issue says goes wrong, and add a branch or check for exactly that case, leaving the general path unchanged for every other input.

You have no tools and must not call any. Below is a reader's report on a software issue: the issue, the file, and the exact current text of the region to change.

{plan?}

Write one exact candidate edit that an applier will paste into an edit tool unchanged.

Rules:
- OLD is copied character for character from REGION, with its indentation. It is a contiguous block of 3 to 12 lines: the lines you change plus one or two unchanged lines so it occurs only once. Never include a line that is not in REGION.
- NEW is OLD with only the needed changes, in the same indentation style. Copy every string the issue requires exactly.
- Do not edit tests. Do not add comments about the change.
- If the report has no REGION or says FILE: unknown, write the single line NO DRAFT and then END.

Write your answer in exactly this form and nothing else.

FILE: the path as the reader gave it
OLD:
<<<
the old lines
>>>
NEW:
<<<
the new lines
>>>
WHY: one sentence
END
