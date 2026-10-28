---
id: "04"
title: "State government officer (PEP) receiving large corporate credits inconsistent with public function"
status: FINAL
disposition: FILE
rules_cited: [STR-001, STR-002, RFI-009, RFI-006, POE-001, POE-005, POE-006, SB-004, INS-001]
---

### 1. Synthetic Pattern

**Account:** Savings account, private sector bank, Tier-1 city branch
**Customer KYC (CUST-04):** Occupation: Deputy Director, State PWD (Public Works Department); salary: ₹75,000/month (government); risk category at onboarding: High (PEP designation — correctly applied); PEP type: domestic PEP; KYC: Aadhaar + PAN + employer letter on file; enhanced due diligence (EDD) conducted at onboarding. No declared secondary income, investments, or business interests. No family member business disclosed.

**Baseline (months 1–18):** Regular government salary credit ₹74,500–₹75,500/month. Household expenses (grocery, fuel, school fees). One LIC premium debit ₹15,000/year. No large credits. Clean pattern.

**Alert period (months 19–21):**

| Month | Credit amount | Sender | Sender description |
|---|---|---|---|
| Month 19 | ₹8,50,000 | ABC Infrastructure Ltd | Mid-size road construction contractor |
| Month 19 | ₹6,20,000 | DEF Engineering Pvt Ltd | Civil works contractor |
| Month 20 | ₹11,00,000 | ABC Infrastructure Ltd | (same as above) |
| Month 20 | ₹4,80,000 | GHI Constructions | Road contractor |
| Month 21 | ₹9,30,000 | DEF Engineering Pvt Ltd | (same as above) |
| Month 21 | ₹8,20,000 | JKL Roadways Pvt Ltd | Highway contractor |

Total credits from corporate senders over 3 months: ₹47,70,000 (₹47.7 lakh)
All senders are contractors in the road/civil construction sector — the sector regulated/tendered by PWD.

CUST-04's declared salary over the same period: ₹2,25,000.
Ratio of corporate credits to declared income: 21.2×

**Ingested signals:** None from external databases. Internal PEP-watchlist monitoring triggered the alert.

**Linked accounts:** None at this RE.

---

### 2. Reasoning Chain

```
RFI-009 (PEP with transactions inconsistent with public-function income) [NEEDS-VERIFICATION]
  → CUST-04 is a correctly designated domestic PEP (state government officer).
    The EDD framework requires heightened scrutiny of all significant transactions.
    ₹47.7L from PWD contractors, transmitted to the personal savings account of a
    serving PWD officer, fails the income-level test comprehensively.
  → corpus: RFI-009

RFI-006 (income inconsistency) [NEEDS-VERIFICATION]
  → The credits do not match any declared income source. CUST-04 has no declared
    consultancy, secondary employment, or business. ₹47.7L = 21.2× three-month
    government salary. The senders are regulated contractors in the PEP's own
    department's procurement domain.
  → corpus: RFI-006

POE Factor 1 — Business profile (POE-002)
  → CUST-04's declared business: government employment. There is no stated basis
    (consultancy, investment income, services) for receiving payments from private
    contractors. PWD contractors paying a PWD officer creates an obvious conflict
    of interest, regardless of legal categorisation.

POE Factor 4 — Income level (POE-005)
  → ₹47.7L over 3 months is 21× the declared income for the period. No documented
    explanation.

POE Factor 5 — Source of income (POE-006)
  → The sources — ABC Infrastructure, DEF Engineering, GHI Constructions, JKL
    Roadways — are all active contractors in CUST-04's own sector. The logical
    inference is that these payments are related to the PEP's public function
    (award of contracts, inspection clearances, tender evaluation). No innocent
    commercial relationship is apparent.

Statutory basis:
  → PMLA 2002 s.12(1)(b) [corpus: SB-002]: suspicion formed.
  → RBI Master Direction on KYC — PEP EDD obligation [corpus: SB-004].
  → STR deadline: 7 working days [corpus: STR-002].
```

**Alternative explanation considered:** Repayment of personal loans made to these companies; rental income from property leased to contractors; inheritance or family gifts coincidentally from these specific companies. All rejected as implausible: the payers are uniformly sector-specific contractors, the amounts are structured as round figures in multiple tranches, and no such explanation appears in the KYC record or any prior customer disclosure.

---

### 3. Draft Ground of Suspicion

Account holder CUST-04, a serving Deputy Director in the State Public Works Department and a correctly designated domestic PEP under the RBI Master Direction on KYC, received corporate credits totalling ₹47,70,000 to their personal savings account over a three-month period from six private entities — all of which are contractors operating in the road and civil construction sector regulated and tendered by the PWD. CUST-04's declared government salary for the same period is ₹2,25,000. The corporate credits are 21.2× the declared income and have no basis in the KYC record, which discloses no secondary employment, consultancy, business interest, or other income source.

The six creditor entities (ABC Infrastructure Ltd, DEF Engineering Pvt Ltd, GHI Constructions, JKL Roadways Pvt Ltd, and two repeat credits from ABC and DEF) are active PWD contractors. Payments from a regulated contractor to the personal account of a serving regulatory/procurement official in the same department constitute a plausible bribery or kickback pattern and are inconsistent with any legitimate commercial relationship.

Enhanced due diligence was applied at onboarding and this monitoring event arises from the PEP watchlist flag. No customer contact has been made (tipping-off prohibition, PMLA s.12A).

Suspicion is formed under PMLA 2002 s.12(1)(b) on the basis of: (a) PEP with transactions inconsistent with public-function income (RFI-009); (b) income inconsistency — 21× declared income from contractor sources (RFI-006); (c) no declared business purpose for receiving payments from the PEP's own regulated sector (POE Factor 1); and (d) income level and source of income comprehensively inconsistent with the KYC profile (POE Factors 4, 5).

---

### 5. Templated-Narrative Check

- Uses generic phrases without specifics: **PASS** — six named entities, specific amounts, 3-month period, 21.2× ratio
- Does not cite specific amounts/dates: **PASS**
- Does not name specific red-flag indicators: **PASS** — RFI-009, RFI-006 named
- Does not explain contradiction with stated profile: **PASS** — government salary, no secondary income, contractors in own sector
- Does not address relevant PO evaluation factors: **PASS** — Factors 1, 4, 5 addressed
- Beneficiary relationship not discussed: **N/A** — this is a credits case; beneficiary not the primary issue
- Geography risk not discussed: **N/A** — domestic
- KYC inconsistency not discussed: **PASS** — no secondary income in KYC, no business interest noted
- Could apply to any customer without modification: **PASS** — CUST-04, PWD sector, contractor names are specific
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
domain_rule_extracted: —
```
