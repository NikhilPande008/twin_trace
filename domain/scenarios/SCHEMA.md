# Scenario File Schema

Every scenario lives in `/domain/scenarios/NN-slug.md` where NN is a zero-padded integer.

---

## Required Fields

```
id: NN
title: [Short descriptive title]
status: draft | reviewed | corrected | FINAL
disposition: FILE | CLOSE-NO-FILE | CONTESTED
```

## Sections

### 1. Synthetic Pattern
Describe the synthetic account/transaction/KYC pattern in enough detail to generate
Seed data from it. Include:
- Account type(s) and number of accounts
- Customer KYC profile (occupation, income bracket, risk category at onboarding)
- Transaction pattern (dates relative, not absolute; amounts; channels; counterparties)
- Any linked accounts or beneficiary relationships
- Ingested signals (from mock MuleHunter / I4C / DPIP), if any

### 2. Reasoning Chain
For each element of the disposition, show the explicit chain:
```
Red-flag indicator: [RFI-NN or description] → [DOMAIN.md reference]
PO evaluation factor: [Factor name from §3.2] → [How it applies here]
Statutory basis: [PMLA/RBI provision] → [Why it is triggered]
```
No unsourced leaps. If a step relies on an UNVERIFIED item in DOMAIN.md, mark it here too.

### 2A. Investigation / EDD Trail  *(REQUIRED for every scenario, any disposition)*
The intermediate step between alert and disposition — what the RE actually did before deciding.
This gap is FIU-IND-inspectable: the alert→suspicion interval and the due diligence undertaken
are themselves examined. Capture:
- **EDD actions taken** (with relative dates): source-of-funds queries, document/KYC-refresh
  requests, account & history review, branch enquiries.
- **Customer response**: explanation given / documents produced / evasive / refused / not
  contactable.
- **OR** an explicit **"No EDD undertaken because…"** rationale (e.g. clear-cut structuring where
  further enquiry would risk tipping-off, or where immediate filing is warranted).
- **Tipping-off boundary note**: confirm any enquiry stayed within permissible ongoing due
  diligence and did NOT disclose that an STR has been or may be filed. (Permissible: "explain the
  source of these funds." Prohibited: any signal a report is being made. Exact statutory citation
  `[SECONDARY—verify]`.)
- **Suspicion formed on**: the timestamp that starts the 7-working-day SLA clock — distinct from
  the transaction date and the alert date. The alert→suspicion gap is inspectable; record both.

### 3. Draft Ground of Suspicion (if disposition = FILE)
The actual text that would go in Part (c) of the STR. Must be:
- Specific (customer, dates, amounts, pattern)
- Non-templated (checked against DOMAIN.md §7 checklist — report results)
- Citing the red-flag indicators and PO evaluation factors that drove the decision

### 4. Draft Closure Rationale (if disposition = CLOSE-NO-FILE)
Why suspicion was NOT formed, and what alternative explanation was accepted.
This section is as important as the STR narrative — FIU-IND inspects not-filing decisions.

### 5. Templated-Narrative Check
Run against DOMAIN.md §7 checklist. Report each item: PASS / FAIL / N/A.
Flag any FAILs and explain how the narrative was revised.

### 6. Contestedness Note (if disposition = CONTESTED)
Present both readings. Do NOT hard-code one answer. Ask the human to choose.
Record the choice and its reasoning.

### 7. Human Review
```
status: draft | reviewed | corrected | FINAL
reviewer: [name / "human-PO-proxy"]
date: YYYY-MM-DD
decision: [FILE | CLOSE-NO-FILE | CONTESTED — confirmed / overridden]
correction_notes: [What the reviewer changed and why]
domain_rule_extracted: [If a general rule was derived, what it is — backfill to DOMAIN.md]
```

---

## Example (Empty — for reference)

```markdown
---
id: 00
title: Schema example — do not use as a scenario
status: draft
disposition: CONTESTED
---

### 1. Synthetic Pattern
[Customer profile]
[Transaction pattern]
[Ingested signals]

### 2. Reasoning Chain
Red-flag indicator: [indicator] → [DOMAIN.md §6 RFI-NN]
PO evaluation factor: Transaction frequency → "frequency unusually high for stated income bracket; see DOMAIN.md §3.2 Factor 7"
Statutory basis: PMLA 2002 s.12(1)(b) — suspicion formed; obligation to file

### 3. Draft Ground of Suspicion
[Specific narrative — see DOMAIN.md §7 for what 'specific' means]

### 5. Templated-Narrative Check
- [ ] Uses generic phrases without specifics: PASS
- [ ] Does not cite specific amounts/dates: PASS
...

### 7. Human Review
status: draft
reviewer: —
date: —
decision: —
correction_notes: —
domain_rule_extracted: —
```
