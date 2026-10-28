---
id: "00"
title: "SCHEMA EXAMPLE — not a real scenario, do not include in evaluation set"
status: draft
disposition: CONTESTED
---

> This file illustrates the schema only. See /domain/scenarios/SCHEMA.md for full spec.

### 1. Synthetic Pattern

**Account type:** Savings account, public-sector bank, urban branch
**Customer KYC:** Occupation: daily-wage labourer; declared income: ₹12,000/month;
  risk category at onboarding: Low; KYC complete (Aadhaar + PAN linked)
**Transaction pattern (T = account opening date):**
  - T+0 to T+30: No activity (dormant)
  - T+31: Credit ₹95,000 from unknown mobile UPI handle
  - T+31 (same day): Debit ₹94,500 to different UPI handle
  - T+32 to T+60: No activity
**Ingested signals:** I4C Suspect Registry — counterparty (the debit UPI handle) flagged as
  suspect; flagged date: T+28 (pre-dates this transaction)
**Linked accounts:** None identified

### 2. Reasoning Chain

```
Red-flag indicator: RFI-01 (credit followed by near-immediate near-total debit)
  → DOMAIN.md §6 RFI-01 [UNVERIFIED — not yet mapped to primary source]

Red-flag indicator: RFI-05 (counterparty matched to I4C Suspect Registry)
  → DOMAIN.md §6 RFI-05 [UNVERIFIED]

PO evaluation factor: Income level (Factor 4)
  → ₹95,000 credit is ~8× monthly declared income; inconsistent with stated profile
  → DOMAIN.md §3.2 Factor 4

PO evaluation factor: Transaction history (Factor 2)
  → Account dormant for 30 days; single large credit + immediate debit; no prior pattern
  → DOMAIN.md §3.2 Factor 2

PO evaluation factor: Beneficiary (Factor 6)
  → Beneficiary (debit counterparty) is I4C-flagged suspect; relationship not explained
  → DOMAIN.md §3.2 Factor 6

Statutory basis: PMLA 2002 s.12(1)(b)
  → Suspicion arguably formed: pattern + signal match + income inconsistency
  → BUT: single transaction, low absolute amount; could be a gift or informal transfer
```

**CONTESTED because:** A real PO might file (I4C signal + pass-through pattern is strong)
OR might close (₹95,000 is below CTR threshold; single event; no prior pattern; could be
legitimate informal transfer). A false-positive here has cost to the customer. A false-negative
risks complicity if the account is a mule. This is a genuine two-PO disagreement scenario.

### 3. Draft Ground of Suspicion

> **[UNVERIFIED — drafted for schema illustration only; do not use]**
>
> Account holder [CUST-00], a self-declared daily-wage labourer with stated monthly income of
> ₹12,000, received a credit of ₹95,000 via UPI (handle: [REDACTED]) on [DATE] — approximately
> 8× the declared monthly income. Within the same business day, ₹94,500 (99.5% of the credit)
> was transferred out to a different UPI handle ([REDACTED]). This UPI handle was registered
> in the I4C Suspect Registry as of [DATE-3 DAYS PRIOR], predating this transaction.
>
> The account had been dormant for 30 days prior to this activity. No business relationship,
> gift, or legitimate explanation for the credit has been identified through KYC or customer
> interaction (tipping-off prohibition applies; no customer contact made).
>
> The pattern — dormancy, large single credit inconsistent with income, near-immediate near-total
> onward transfer to a flagged suspect counterparty — is consistent with mule-account pass-through
> behaviour. Suspicion is formed under PMLA 2002 s.12(1)(b) on the basis of RFI-01 (pass-through
> pattern) and RFI-05 (flagged counterparty).

### 4. Draft Closure Rationale

> **[UNVERIFIED — for schema illustration only]**
>
> While the pass-through pattern and I4C flag are noted, the following factors weigh against
> filing: (1) single-event, no prior or subsequent pattern; (2) absolute amount (₹95,000) is
> sub-threshold for CTR; (3) informal transfers at this scale are common in the daily-wage
> segment for family remittances or group savings (chit funds). Alert closed: monitoring for
> 30 days; re-evaluate if further activity. Documented rationale retained per PMLA s.12(1)(c).

### 5. Templated-Narrative Check

Against DOMAIN.md §7 checklist:
- Uses generic phrases without specifics: **PASS** (specific amounts, dates, handles cited)
- Does not cite specific amounts/dates: **PASS**
- Does not name specific red-flag indicators: **PASS** (RFI-01, RFI-05 cited)
- Does not explain contradiction with stated profile: **PASS** (8× income noted)
- Does not address relevant PO evaluation factors: **PASS** (Factors 2, 4, 6 addressed)
- Beneficiary relationship not discussed: **PASS** (counterparty flag noted)
- Geography risk not discussed: **N/A** (domestic transaction)
- KYC inconsistency not discussed: **PASS** (KYC complete; income inconsistency is the flag)
- Could apply to any customer without modification: **PASS** (customer-specific facts throughout)

**Result: No fails. Schema illustration passes the checklist.**

### 6. Contestedness Note

This scenario is CONTESTED. Two reasonable PO readings:

**Reading A — FILE STR:**
- I4C signal + pass-through pattern + income inconsistency = suspicion formed
- The I4C flag predates the transaction; the counterparty was already suspect
- A PO who does not file risks being found to have suppressed a flagged case
- Safer to file; FIU-IND can evaluate

**Reading B — CLOSE-NO-FILE:**
- Single event; no prior pattern; sub-threshold amount
- Informal transfers common in this customer segment
- Filing every I4C-adjacent transaction without pattern would inflate the alert-to-STR ratio
- Document rationale and monitor; re-evaluate at 30 days

**Human decision required:** Do not hard-code either answer. Present to Nikhil.

### 7. Human Review

```
status: draft
reviewer: —
date: —
decision: —
correction_notes: —
domain_rule_extracted: —
```
