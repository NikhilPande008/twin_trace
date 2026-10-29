# Inspection replay — 2026-10-28T18:26:06+00:00 (live)

Seed `969dda38cba7eb32…` · question bank `b5f7ce988b3a6f81…` · 16 synthetic alerts · 193.3 s

Questions are this project's, derived from FIU-IND Section 13 orders (`domain/enforcement/`); they are not an FIU-IND checklist. Records are synthetic. Neither record has a factor assessment (it needs a model) and both officers are self-asserted, so IQ-07 and IQ-08 are not answered in either.

| Question | Twin Trace record answers | Cursory closure answers |
|---|---|---|
| IQ-01 Why was this alert closed or filed? Show the reasoning recorded at the time. | 16 / 16 | 0 / 16 |
| IQ-02 Which facts does the decision rest on, and what would have changed it? | 16 / 16 | 0 / 16 |
| IQ-03 Is every amount in the reasoning traceable to a transaction or a recorded calculation? | 14 / 16 | 0 / 16 |
| IQ-04 Can the calculation behind those amounts be re-run and give the same result? | 16 / 16 | 0 / 16 |
| IQ-05 When was suspicion formed, and was the decision made within the reporting timeline? | 16 / 16 | 16 / 16 |
| IQ-06 Which regulatory provisions was the decision assessed against? | 2 / 16 | 0 / 16 |
| IQ-07 Who made the decision, and how was their identity established? | 0 / 16 | 0 / 16 |
| IQ-08 Were the suspicion-evaluation factors assessed and recorded? | 0 / 16 | 0 / 16 |
| IQ-09 Was outside information checked, and did that check actually run? | 0 / 16 | 0 / 16 |
| IQ-10 How many earlier alerts on this customer were closed, and does this decision account for them? | 16 / 16 | 16 / 16 |
| IQ-11 Has anything the decision rests on changed since, and was the decision re-checked? | 0 / 16 | 0 / 16 |

Total answered: Twin Trace 96 / 174; cursory 32 / 160 (questions that do not apply, such as IQ-03 when the reasoning cites no amount, are not counted).

## Cross-examination (live, `nvidia/nemotron-3-super-120b-a12b`)

Ran on 16 / 16 records. Findings 79; marked answered with valid citations 25; not answered by the record 54; rejected by the citation checker 0.

| Alert | Findings | Answered (valid cites) | Not answered | Rejected |
|---|---|---|---|---|
| ALERT-01 | 5 | 2 | 3 | 0 |
| ALERT-02 | 5 | 0 | 5 | 0 |
| ALERT-03 | 5 | 2 | 3 | 0 |
| ALERT-04 | 5 | 2 | 3 | 0 |
| ALERT-05 | 5 | 2 | 3 | 0 |
| ALERT-06 | 5 | 0 | 5 | 0 |
| ALERT-07 | 5 | 2 | 3 | 0 |
| ALERT-08 | 5 | 1 | 4 | 0 |
| ALERT-09 | 5 | 1 | 4 | 0 |
| ALERT-10 | 5 | 1 | 4 | 0 |
| ALERT-11 | 5 | 2 | 3 | 0 |
| ALERT-12 | 5 | 1 | 4 | 0 |
| ALERT-13 | 5 | 1 | 4 | 0 |
| ALERT-14 | 5 | 0 | 5 | 0 |
| ALERT-15 | 5 | 4 | 1 | 0 |
| ALERT-16 | 4 | 4 | 0 | 0 |

Questions the model said the record does not answer (first alert with any):
- ALERT-01: What specific AML training or certification does the decision maker PO-001 possess?
- ALERT-01: Was the alert disposition reviewed and approved by a supervisor or a second-line AML reviewer before filing?
- ALERT-01: Does the decision record include a reference to the SAR/STR filed with FIU‑IND (e.g., acknowledgement number or filing timestamp)?
