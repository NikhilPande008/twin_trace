# Regulatory retrieval: BM25 vs hybrid — 2026-10-28T18:26:02+00:00 (LIVE)

Embedding model `Qwen/Qwen3-Embedding-8B` via Nebius Token Factory. 16 paraphrased questions with an author-assigned answering rule; 4 off-corpus questions that must get no answer. Too few to support a general accuracy claim. The questions and labels were written by the coding assistant after reading the corpus and before either method was run on them; a reviewer's own questions would be a fairer test.

| | Labelled rule in top 3 | Off-corpus abstained |
|---|---|---|
| BM25 only | 13 / 16 | 4 / 4 |
| Hybrid | 16 / 16 | 4 / 4 |

| Question | Expected | BM25 top 3 | Hybrid top 3 |
|---|---|---|---|
| How many days do we have to report a suspicious customer once we suspect them? | STR-002 | CTR-001, INS-001, CTR-002 | STR-002, STR-001, CTR-002 |
| Is there a minimum amount below which suspicion need not be reported? | STR-005 | STR-005, STR-001, POE-005 | STR-005, STR-001, POE-005 |
| A customer tried to send money but the payment was blocked. Do we still report? | STR-003 | STR-003, CCR-001, INS-001 | STR-003, STR-001, STR-004 |
| Can the officer tell the customer that we have reported them? | SB-003 | RS-004, INS-002, CTR-001 | RS-004, INS-002, SB-003 |
| Which portal do suspicious transaction reports go through? | STR-006 | STR-006, CTR-003, POE-008 | STR-006, RS-003, CTR-003 |
| By which date must last month's large cash deposits be reported? | CTR-002 | CTR-002, POE-002, CTR-001 | CTR-002, CTR-001, CTR-003 |
| Above what cash amount must a report be made regardless of suspicion? | CTR-001 | STR-001, CCR-001, CTR-001 | STR-001, CCR-001, CTR-001 |
| If a cash deposit is both large and suspicious, do we file both reports? | CTR-003 | CTR-003, CTR-001, STR-001 | CTR-003, STR-001, CTR-001 |
| How long must transaction records be kept? | RR-001 | RR-001, SB-001 | RR-001, SB-001, RS-003 |
| What must the narrative section of a suspicious report contain? | RS-004 | RS-001, RS-004, SB-002 | RS-001, RS-004, SB-002 |
| We found fake currency notes at the branch counter. What report applies? | CCR-001 | CCR-001, RS-003, STR-005 | CCR-001, RS-003, STR-005 |
| Transactions involving a charity or non-profit: is there a separate report? | NTR-001 | NTR-001, CTR-001, RS-001 | NTR-001, RS-003, RS-001 |
| What will inspectors look at when an alert was closed without a report? | INS-001 | INS-001, INS-003, CTR-002 | INS-001, INS-003, INS-002 |
| Who is allowed to make the decision to report, and by when? | INS-002 | STR-001, INS-002, INS-001 | INS-002, STR-002, STR-001 |
| Does the customer's declared salary explain the money coming in? | POE-005 | POE-002, STR-004, SB-001 | POE-002, POE-009, POE-005 |
| Are the countries involved in the transfers high risk? | POE-011 | POE-011, POE-004, POE-007 | POE-011, POE-004, POE-007 |
