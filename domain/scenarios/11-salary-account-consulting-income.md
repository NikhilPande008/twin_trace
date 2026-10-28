---
id: "11"
title: "Salary account receiving undisclosed ₹3–5L/month 'consulting fees' — contested"
status: FINAL
disposition: CONTESTED
rules_cited: [STR-001, RFI-006, POE-001, POE-005, POE-006, POE-012, INS-001, INS-003]
---

### 1. Synthetic Pattern

**Account:** Savings account, private sector bank, urban branch
**Customer KYC (CUST-11):** Occupation: software engineer; employer: mid-size IT company (salary NEFT visible); declared income: ₹85,000/month; risk category: Low; KYC updated 18 months ago; Aadhaar + PAN linked.

**Baseline (months 1–24):** Regular salary NEFT ₹84,000–₹86,000/month from single employer. Monthly SIP ₹10,000. EMI ₹35,000/month. Standard professional expense pattern. No other income visible.

**Alert period (months 25–27):**

In addition to the normal salary credit, the account receives:

| Month | Additional credit | From | Remarks field |
|---|---|---|---|
| Month 25 | ₹3,40,000 | NEFT from private individual (Mr. Vikram S.) | "Consulting fees" |
| Month 26 | ₹4,20,000 | NEFT from same individual (Mr. Vikram S.) | "Consulting fees" |
| Month 27 | ₹4,80,000 | NEFT from same individual (Mr. Vikram S.) | "Professional charges" |

Total additional credits over 3 months: ₹12,40,000 (₹12.4 lakh)
Average: ₹4.13L/month — approximately 4.9× declared monthly salary.

CUST-11's KYC declares no secondary employment, no business, no consultancy. No GST registration on file.

**Case record in the seed (`ddp/seed_data.py`, 2026-10-28):** the three NEFT credits above, plus the home-loan EMI (₹35,000) and SIP (₹10,000) each month. Salary credits are not in the case record. ASSUMED: debit dates (June–August 2026).

---

### 2. Reasoning Chain

```
RFI-006 (income inconsistency in salary account) [NEEDS-VERIFICATION]
  → Salary account receiving ₹3.4–4.8L/month from a private individual in addition
    to declared salary, with no declared secondary income source in KYC.
  → corpus: RFI-006

POE Factor 1 — Business profile (POE-002)
  → Declared business: employee of IT company. No consulting business declared.
    CUST-11 could be moonlighting (permitted by employer terms or otherwise) but
    this is not disclosed in KYC.

POE Factor 4 — Income level (POE-005)
  → Additional credits of 4.9× declared salary with no declared secondary income.
    If genuine consulting income, this represents material undisclosed economic
    activity for 3 consecutive months.

POE Factor 5 — Source of income (POE-006)
  → "Consulting fees" from a private individual (Mr. Vikram S.) with no further
    context. Who is Mr. Vikram S.? What is the nature of the consulting engagement?
    No contract, invoice, or prior relationship visible.

POE Factor 12 — KYC availability (POE-012)
  → KYC is 18 months old and does not reflect this consulting income. Under RBI
    Master Direction on KYC, a material change in income profile should trigger
    a KYC update request. The KYC is technically available but is stale in
    relation to the customer's apparent current income.
```

**CONTESTED — two defensible PO readings:**

**Reading A — FILE STR:**
- ₹12.4L over 3 months from a single private individual with no declared relationship or business is a significant unexplained income stream
- "Consulting fees" is one of the most common labels used to legitimise illicit payments in an ML context
- No GST registration (freelancers above ₹20L threshold must register; 3 months × ₹4L = ₹12L annualised is below GST threshold, but the scale suggests ongoing engagement)
- No client-disclosed relationship; no contract
- The pattern is consistent with RFI-006 and income layering

**Reading B — CLOSE-NO-FILE after KYC update:**
- ₹3–5L/month consulting income for a senior software engineer is entirely plausible and common in the Indian IT market (moonlighting, freelancing on platforms like Upwork, Toptal, etc.)
- RBI Master Direction on KYC addresses this: the bank should request a KYC update reflecting the consulting income and obtain professional details (client name, nature of work, any contract or SOW)
- If CUST-11 provides documentation (a simple consulting agreement, or even a letter from the client confirming the engagement), the income is fully explained
- Filing an STR on a mid-career software engineer for freelance income without first requesting a KYC update is a false positive with real harm to the customer
- The volume (₹12.4L annualised) doesn't rise to the level where the absence of documentation alone creates strong suspicion

**The crux:** The key procedural question is whether the PO should request a KYC update before making the disposition decision. If the KYC update procedure is followed and CUST-11 provides plausible documentation, CLOSE-NO-FILE is appropriate. If CUST-11 is unresponsive or the documentation doesn't check out, FILE becomes the right answer.

---

### 4. Draft Closure Rationale (conditional — if KYC update satisfactory)

Following identification of undisclosed consulting income of ₹12,40,000 over months 25–27, CUST-11 was contacted for a KYC update per RBI Master Direction on KYC (without disclosing that an STR review was underway — tipping-off prohibition noted). CUST-11 provided: (a) a consulting agreement with [Client Entity] for software architecture advisory services; (b) invoices raised in CUST-11's name for the three monthly payments; (c) a GST registration certificate (obtained in month 26 upon crossing an annual threshold).

The documented consulting engagement is consistent with CUST-11's professional profile (senior software engineer). The payer (Mr. Vikram S. / [Client Entity]) is identified as a registered startup in the technology sector with a verifiable web presence. The amounts (₹3,40,000 to ₹4,80,000 a month) are within market range for senior technology consulting.

Suspicion not formed. KYC updated to reflect consulting income. Alert closed. Documentation retained [corpus: RR-001].

---

### 5. Templated-Narrative Check

(Reading A — FILE version)

- Uses generic phrases without specifics: **PASS** — ₹12.4L, 3 months, Mr. Vikram S., "consulting fees" label cited
- Does not cite specific amounts/dates: **PASS**
- Does not name specific red-flag indicators: **PASS** — RFI-006 named
- Does not explain contradiction with stated profile: **PASS** — no secondary income declared; no GST registration
- Does not address relevant PO evaluation factors: **PASS** — Factors 1, 4, 5, 12 addressed
- Beneficiary relationship not discussed: **N/A** — this is a credits case
- Geography risk not discussed: **N/A** — domestic
- KYC inconsistency not discussed: **PASS** — stale KYC; undisclosed income source
- Could apply to any customer without modification: **PASS** — CUST-11, IT sector, specific amounts

---

### 6. Contestedness Note

The product should not auto-generate a FILE recommendation for this scenario. The correct product behaviour is to:

1. Surface both readings
2. Flag that a KYC update procedure is available and appropriate
3. Recommend: "Request KYC update within [N] working days; defer STR disposition pending response. If no response or unsatisfactory documentation by day [SLA-3]: FILE."
4. Record the deferral in the DECISION_LEDGER with a re-evaluation timestamp

**Human decision required:** Does this RE's SOP allow deferral of STR disposition for KYC update? What is the maximum deferral period consistent with the 7-working-day deadline? This is a process question that varies by RE.

---

### 7. Human Review

```
status: corrected
reviewer: —
date: —
decision: —
correction_notes: "POE corpus ID misreferences corrected in body text and rules_cited frontmatter."
domain_rule_extracted: "KYC update procedure can be a legitimate intermediate step before
STR disposition, provided the deferral stays within the 7-working-day deadline. The
product should model this deferral-with-deadline pattern as a first-class disposition
state (DEFERRED) in the DECISION_LEDGER. (corpus: STR-002; POE-012; INS-002)"
```
