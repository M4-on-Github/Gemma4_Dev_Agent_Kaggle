---
id: kg-747519-kaggle-error-queue
topic_id: 747519
title: Update on "Kaggle Error" Submissions & Queue Delays
author: Dustin (Kaggle staff, posted 2026-10-08)
author_role: staff
credibility: high
topics: [budget, grading, noise]
first_seen: 2026-11-03
last_checked: 2026-11-03
---

## Summary
Staff post on the queue backlog. Submissions that waited more than 15 h for a machine were marked "Kaggle Error" even when they later ran. Staff extended the queue timeout, reprocessed affected runs for scoring, and added a pending-submission limit separate from the 1/day limit. Participant comments from 2026-10-09 to 2026-11-03 report pending times of 18 to 32 h. Read in full on 2026-11-03 (101 comments; deleted comments not visible).

## Claims made (quoted numbers)
- [V] Staff, 2026-10-08: "Submissions that waited >15h to start were being marked as 'Kaggle Error' even if they eventually did run."
- [V] Staff, 2026-10-08: pending limit, "If your team's previous submission is still scoring, you will need to wait until it finishes to submit again."
- [V] Staff (Dustin), 2026-10-10: "The current queue delay is around ~33h". 2026-10-13: "Queue delay has fallen to around ~14h ... most runs should finish within ~24hish of submit now."
- [V] Staff (Ryan Holbrook, comment 2026-10-09): "even after doubling the number of L4 machines, we were still seeing the queue grow without bounds."
- [M] Participant, 2026-11-02: submission 57858834 "pending approximately 30 hours"; submission 57862929 "PENDING state for 32 hours".
- [M] Participant, 2026-11-03 (topic 755318): "every submission of mine for the past 2 weeks have been for 18-28h until a score".
- [M] Participant, 2026-11-03 (comment on 747519): Notebook Timeout issue "persists", no successful attempt in weeks.

## Possible claims for us
- The pending limit means a stuck run blocks the next upload, so the final upload window needs margin beyond the 12 h run. [I] Queue wait plus run time, not the 12 h run alone, is the constraint on the last slots.
- [I] Staff's "no action needed" (10-08) covers queue timeouts only. It says nothing about a Notebook Timeout (run exceeded 12 h), which the 11-03 comments report as recurring. Whether a timed-out slot is ever re-run stays unknown.

## Files
None downloaded.

## Updates
- 2026-11-03: first full read. The 2026-10-28 digest listed this thread as unread.
