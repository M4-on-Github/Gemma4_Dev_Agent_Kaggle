Your first reply must be a read_file call, not text. An OLD written without that read is wrong and every edit built on it fails.

You are writer 4 of 5 independent writers. Your location is LOCATION 4 of the reader's report below; ignore every other location. If the report has fewer than 4 locations, or LOCATION 4 has no FILE and LINES, use LOCATION 1 instead. The report gives each location a FILE, a LINES range and a CHANGE line, and no code.

Step 1, the read. Call `read_file` exactly once, with `filepath` set to the FILE of your location, `start_line` set to its first LINES number minus 5 (at least 1) and `end_line` set to its last LINES number plus 5. Make no other tool call, before or after it. If LOCATION 1 has no FILE and LINES either, make no call and write the single line NO DRAFT and then END.

Step 2, the draft. Your angle: the contract, word for word. Take every symbol, signature, message, status code and return value that the issue requires, and make the code produce exactly those characters. Check each required string against your NEW lines before you answer.

Below is a reader's report on a software issue: the issue, and up to five numbered locations, each with a file, the first and last line of its region, and the change to make.

{plan?}

Write one exact candidate edit that an applier will paste into an edit tool unchanged.

Rules:
- OLD is copied character for character from the `read_file` result you just received, with its indentation, as plain text with real line breaks and real quotes, not in the escaped form the tool result shows. It is a contiguous block of 3 to 12 lines: the lines you change plus one or two unchanged lines so it occurs only once. Never include a line that is not in that result.
- NEW is OLD with only the needed changes, in the same indentation style. Copy every string the issue requires exactly.
- Do not edit tests. Do not add comments about the change.

Write your answer in exactly this form and nothing else.

FILE: the path as the reader gave it for your location
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
