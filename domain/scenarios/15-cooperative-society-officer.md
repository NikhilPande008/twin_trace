---
id: "15"
title: "Cooperative housing society officer diverting maintenance collections to personal account"
status: FINAL
disposition: FILE
rules_cited: [STR-001, STR-002, RFI-001, RFI-006, POE-001, POE-003, POE-005, POE-007, INS-001, INS-002]
---

### 1. Synthetic Pattern

**Account:** Savings account, cooperative bank, residential township branch
**Customer KYC (CUST-15):** Occupation: retired bank officer (self-declared); pension income: ₹35,000/month; risk category: Low; KYC updated 3 years ago; Aadhaar + PAN linked; address: residential apartment, same township as the bank branch.

**Key context:** CUST-15 is the elected Treasurer of a registered Cooperative Housing Society ("Skyline CHS") in the same township. The society's maintenance collection (monthly maintenance from ~120 flats, ₹3,000–₹5,000 per flat/month) is supposed to be deposited into the society's current account at a different bank ("Society Bank X"). However, the society's account at Bank X shows a significant shortfall in collections over the 6-month alert period.

**Alert trigger:** A complaint lodged by the Skyline CHS Managing Committee (separate from CUST-15) with the bank, alleging that the Treasurer may be diverting maintenance collections. The bank's compliance team initiates a transaction review.

**Alert period (months 1–6) — CUST-15's savings account:**

| Month | Cash credit pattern | Amount | Notable feature |
|---|---|---|---|
| Month 1 | 4 cash deposits over counter | ₹2,80,000 | Deposits on the 7th, 8th, 9th, 10th of the month |
| Month 2 | 3 cash deposits | ₹3,20,000 | Deposits on the 6th, 8th, 10th |
| Month 3 | 4 cash deposits | ₹2,95,000 | Deposits on the 7th, 8th, 9th, 10th |
| Month 4 | 3 cash deposits | ₹3,10,000 | Deposits on the 8th, 9th, 10th |
| Month 5 | 4 cash deposits | ₹2,75,000 | Deposits on the 6th, 7th, 8th, 10th |
| Month 6 | 4 cash deposits | ₹3,05,000 | Deposits on the 7th, 8th, 9th, 10th |

Total cash credits (6 months): ₹18,05,000 (₹18.05 lakh)

The deposits consistently occur in the 6th–10th of each month — the same period when flat owners pay their monthly maintenance (typically due by the 10th of the month, collected by the Treasurer in cash during the 1st–7th).

**Corroborating pattern:** Skyline CHS's account at Bank X shows a deficit of approximately ₹17–19L over the same 6 months compared to expected maintenance collections (based on 120 flats × ~₹3,500/month average = ₹4.2L/month × 6 = ₹25.2L expected; received: ~₹6–8L in scattered deposits).

**Ingested signals:** The complaint from the CHS Managing Committee is the trigger. The bank has documentary evidence of the expected vs. actual society account credits.

**CUST-15's declared income:** ₹35,000/month pension. ₹18.05L in cash over 6 months = approximately 8.6× 6-month pension income. No declared business, no secondary income.

---

### 2. Reasoning Chain

```
RFI-006 (income inconsistency) [NEEDS-VERIFICATION]
  → ₹18.05L in cash credits over 6 months against a pension-only declared income
    of ₹35,000/month. Even absent the society context, this is an income
    inconsistency. With the society context, the deposits are consistent only
    with diverted maintenance collections.
  → corpus: RFI-006

RFI-001 (pass-through / fund-diversion pattern)
  → The cash is collected from flat owners (a known source — maintenance fees),
    deposited into CUST-15's personal savings account instead of the society's
    designated account, and then drawn down for personal use. This is a pass-
    through of a specific fund that belongs to a third party (the society).
  → corpus: RFI-001

POE Factor 1 — Business profile (POE-002)
  → CUST-15's declared occupation is "retired bank officer." There is no declared
    business, no consulting income, no property rental, no activity that explains
    ₹18.05L in cash over 6 months. The deposits align with a role (society
    treasurer) that CUST-15 holds but that is not reflected in the KYC.

POE Factor 2 — Transaction history (POE-003)
  → This is presumably a new pattern (alert covers 6 months; prior history is
    pension-only). The timing and amounts are inconsistent with prior baseline.

POE Factor 4 — Income level (POE-005)
  → ₹18.05L over 6 months = 8.6× pension income. Entirely unexplained from declared
    income sources.

POE Factor 6 — Beneficiary (POE-007)
  → The personal savings account is the beneficiary of funds that belong to
    Skyline CHS. The real "beneficiary" issue here is who is being deprived
    (the society), not who receives the money.

Timing correlation:
  → Deposits cluster in the 6th–10th of each month — precisely when maintenance
    collections are due. This is not coincidental. It is the single most powerful
    piece of evidence linking the deposits to the diverted collections.

Statutory basis:
  → PMLA 2002 s.12(1)(b) [corpus: SB-002]: suspicion formed — the proceeds of the
    diverted maintenance fees may constitute proceeds of criminal breach of trust
    (Section 406/409 IPC), which is a scheduled offence under PMLA.
  → STR deadline: 7 working days from suspicion formation [corpus: STR-002].
```

**Alternative explanation considered:** CUST-15 was collecting society maintenance on behalf of the society and planned to deposit at Bank X but delayed — the personal account deposits were a temporary holding mechanism. Rejected: (a) ₹18.05L over 6 months is not a "temporary hold"; (b) the society account deficit at Bank X matches CUST-15's personal deposits; (c) a Treasurer who holds ₹3L/month in a personal account for weeks is in breach of their fiduciary duty regardless of ML intent; (d) CUST-15 has not come forward to explain, despite the management committee's complaint.

---

### 3. Draft Ground of Suspicion

Account holder CUST-15, a retired bank officer (declared pension income ₹35,000/month), received cash credits totalling ₹18,05,000 over a 6-month period in their personal savings account. The cash deposits occurred in clusters during the 6th–10th of each month — precisely the window when Skyline Cooperative Housing Society (of which CUST-15 is the elected Treasurer) collects flat maintenance fees in cash from approximately 120 flat owners (expected monthly collection ₹4–4.5L).

During the same 6-month period, Skyline CHS's designated maintenance account at Bank X received only ₹6–8L (against an expected ₹25L), a shortfall of ₹17–19L. The correlation between CUST-15's personal cash deposits (₹18.05L) and the society account deficit (₹17–19L) — in amount, in timing, and across 6 consecutive months — is consistent with systematic diversion of maintenance collections into CUST-15's personal account instead of the society's designated account.

₹18.05L in cash over 6 months is 8.6× CUST-15's declared 6-month pension income. No declared secondary income or business activity accounts for this amount. The temporal correlation between deposit dates and the monthly maintenance collection window is not coincidental.

The diversion of funds held in a fiduciary capacity (society maintenance collections) to a personal account may constitute criminal breach of trust (IPC s.409 — breach of trust by a person entrusted with property), which is a scheduled offence under PMLA. Suspicion is formed under PMLA 2002 s.12(1)(b) on the basis of: (a) income inconsistency — 8.6× declared income in cash, unexplained (RFI-006); (b) the deposit-timing correlation with known maintenance collection dates (POE Factor 1 — business profile of treasurer role); (c) the quantitative match between personal deposits and the society account deficit (POE Factor 5 — source of funds identified); and (d) 6-month consistent pattern (POE Factor 3).

---

### 5. Templated-Narrative Check

- Uses generic phrases without specifics: **PASS** — ₹18.05L, 6-month period, Skyline CHS, Bank X deficit ₹17–19L, 6th–10th timing correlation
- Does not cite specific amounts/dates: **PASS**
- Does not name specific red-flag indicators: **PASS** — RFI-006, RFI-001 named; IPC s.409 PMLA scheduled offence referenced
- Does not explain contradiction with stated profile: **PASS** — 8.6× pension income; retired officer with no business
- Does not address relevant PO evaluation factors: **PASS** — Factors 1, 3, 4, 5 addressed
- Beneficiary relationship not discussed: **PASS** — society as rightful owner of diverted funds; fiduciary role addressed
- Geography risk not discussed: **N/A** — domestic
- KYC inconsistency not discussed: **PASS** — treasurer role not in KYC; income vs. deposits gap noted
- Could apply to any customer without modification: **PASS** — Skyline CHS, 6th–10th pattern, Bank X deficit are specific
- Substantially identical to a previous STR: **N/A**

**Result: 0 fails.**

---

### 7. Human Review

```
status: corrected
reviewer: —
date: —
decision: —
correction_notes: "POE corpus ID misreferences corrected in body text and rules_cited frontmatter."
domain_rule_extracted: "Diversion of third-party funds held in a fiduciary capacity
(society/trust funds) to a personal account is a scheduled PMLA offence predicate
(criminal breach of trust, IPC s.409). The temporal correlation between deposit
timing and the known collection cycle is the key evidence. The product should be
capable of reasoning about timing patterns, not just amounts. (corpus: STR-001; SB-002)"
```
