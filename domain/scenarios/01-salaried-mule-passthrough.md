---
id: "01"
title: "Salaried mule pass-through with I4C counterparty signal"
status: FINAL
disposition: FILE
rules_cited: [STR-001, STR-002, RFI-001, RFI-005, POE-003, POE-005, POE-007, INS-001, INS-002]
---

### 1. Synthetic Pattern

**Account:** Savings account, private sector bank, urban branch
**Customer KYC (CUST-01):** Occupation: data entry operator; declared income: ₹28,000/month; risk category at onboarding: Low; KYC complete (Aadhaar + PAN); account open 14 months

**Baseline (months 1–13):** Regular salary credit ₹27,800–₹28,200/month from employer (NEFT, consistent sender); periodic small UPI debits (₹200–₹3,000); no cash transactions.

**Alert period (month 14, days T+1 to T+6):**

| Day | Type | Amount | Counterparty |
|---|---|---|---|
| T+1 | Credit (UPI) | ₹1,10,000 | Unknown mobile handle A |
| T+2 | Credit (UPI) | ₹1,40,000 | Unknown mobile handle B |
| T+3 | Debit (UPI) | ₹2,46,500 | Unknown mobile handle C |
| T+4 | Credit (UPI) | ₹95,000 | Unknown mobile handle D |
| T+5 | Debit (UPI) | ₹94,200 | Unknown mobile handle C (same as T+3) |

Total credits month 14 (excl. salary): ₹3,45,000 (~12.3× declared monthly income)
Total debits to handle C: ₹3,40,700 (98.5% of non-salary credits)

**Ingested signal:** I4C Suspect Registry — mobile handle C flagged as associated with cyber fraud (online gaming scam), registration date 3 weeks prior to T+1.

**Linked accounts:** None at this bank. Handle C not linked to any account at this bank.

---

### 2. Reasoning Chain

```
RFI-001 (pass-through pattern) [NEEDS-VERIFICATION — no primary FIU-IND citation yet]
  → 3 credits from different unknown handles; 98.5% of proceeds immediately onward-transferred
    to a single beneficiary (handle C); account performs no other economic function during period.
  → corpus: RFI-001

RFI-005 (flagged counterparty) [NEEDS-VERIFICATION]
  → Handle C confirmed in I4C Suspect Registry 3 weeks before this activity.
    Funds flowed TO a registered suspect, not merely from one.
  → corpus: RFI-005

POE Factor 2 — Transaction history (POE-003)
  → 13 months of consistent ₹28K salary-only pattern; month 14 shows a completely
    different profile (multiple unknown-party UPI credits, large immediate debits).
    Deviation from established baseline is stark.

POE Factor 4 — Income level (POE-005)
  → ₹3,45,000 in credits from non-employer sources in one week = 12.3× declared monthly
    income. No declared secondary income or business.

POE Factor 6 — Beneficiary (POE-007)
  → Handle C appears in both debit events; beneficiary identity unknown to the RE;
    counterparty registered as suspect by I4C; relationship to CUST-01 unexplained.

Statutory basis:
  → PMLA 2002 s.12(1)(b) [corpus: SB-002]: suspicion formed — pass-through pattern
    + I4C signal + income anomaly.
  → STR deadline: 7 working days from suspicion formation [corpus: STR-002].
  → No customer contact (tipping-off prohibition applies) [corpus: STR-004 / SB-003].
```

**Alternative explanation considered:** Informal group savings (chit fund), remittances from family members. Rejected: chit fund credits are typically periodic/scheduled from known individuals; ₹3.45L in 5 days from 4 unknown mobile handles with near-immediate onward transfer to a single flagged suspect does not fit the informal savings pattern.

---

### 3. Draft Ground of Suspicion

Account holder CUST-01, a self-declared data entry operator with stated monthly income of ₹28,000, exhibited a materially anomalous transaction pattern in month 14 of the account's operation. After 13 months of consistent salary-only credits (₹27,800–₹28,200/month, single NEFT sender), the account received three credits from four distinct unknown UPI mobile handles totalling ₹3,45,000 over a five-day period — approximately 12.3× the declared monthly income. Within the same period, ₹3,40,700 (98.5% of the non-salary inflows) was transferred out to a single UPI handle (handle C) in two transactions.

Handle C is registered in the I4C Suspect Registry as associated with a cyber fraud scheme (online gaming), with the registration date three weeks prior to the first credit in this sequence. This RE has no independent information on the identity, business, or relationship of handle C to CUST-01. The KYC record discloses no secondary income, business interest, or other legitimate source that would account for this volume of third-party credits.

The pattern is consistent with mule-account pass-through activity (RFI-001, corpus): funds from multiple unknown sources are aggregated in the account and immediately forwarded to a single known-suspect counterparty. The account has performed no function other than transit during this period.

Suspicion is formed under PMLA 2002 s.12(1)(b) on the basis of: (a) the pass-through pattern (RFI-001); (b) confirmed credit flow to an I4C-registered suspect (RFI-005); (c) income inconsistency (POE Factor 4 — 12.3× declared income); (d) complete deviation from 13-month transaction baseline (POE Factor 3); and (e) unexplained beneficiary identity (POE Factor 6). No customer contact has been made (tipping-off prohibition, PMLA s.12A).

---

### 5. Templated-Narrative Check

Against DOMAIN.md §7 checklist:
- Uses generic phrases without specifics: **PASS** — amounts, dates, handle labels, I4C registration date all cited
- Does not cite specific amounts/dates: **PASS**
- Does not name specific red-flag indicators: **PASS** — RFI-001, RFI-005 named
- Does not explain contradiction with stated profile: **PASS** — 12.3× income, 0 declared secondary income
- Does not address relevant PO evaluation factors: **PASS** — Factors 3, 4, 6 addressed
- Beneficiary relationship not discussed: **PASS** — handle C identity, I4C flag, unknown relationship addressed
- Geography risk not discussed: **N/A** — domestic transaction
- KYC inconsistency not discussed: **PASS** — KYC complete; the inconsistency is income vs. transaction volume
- Could apply to any customer without modification: **PASS** — CUST-01 specific throughout
- Substantially identical to a previous STR: **N/A** — first scenario

**Result: 0 fails. GoS meets the non-templated standard.**

---

### 7. Human Review

```
status: corrected
reviewer: —
date: —
decision: —
correction_notes: "POE corpus ID misreferences corrected in body text and rules_cited frontmatter."
domain_rule_extracted: —
```
