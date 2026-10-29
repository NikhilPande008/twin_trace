---
id: "03"
title: "Dormant retiree account reactivated for ₹85L cash withdrawal — contested"
status: FINAL
disposition: CONTESTED
rules_cited: [STR-001, RFI-003, POE-003, POE-005, POE-006, POE-012, INS-001, INS-003]
---

### 1. Synthetic Pattern

**Account:** Savings account, public sector bank, semi-urban branch
**Customer KYC (CUST-03):** Occupation: retired school principal; declared income: ₹20,000/month (pension); risk category: Low; age: 68; KYC last updated 3 years ago; Aadhaar + PAN linked.

**Baseline (months 1–30):** Monthly pension credit ₹19,800–₹20,200 from state government. Periodic debits for utilities, insurance premium (LIC, ₹8,000/quarter). No large transactions. Account becomes dormant (RBI definition: no customer-initiated transaction for 24 months) — bank internally classifies as dormant at month 25; however, the auto-debit for LIC premium continues, so transactions technically occur but are not customer-initiated.

**Alert period (month 31):**
- Day T+1: Credit of ₹85,00,000 (₹85 lakh) via RTGS from account of "Greenfield Developers Pvt Ltd" (a private company; unknown to the RE).
- Day T+2: Customer walks into branch; requests cash withdrawal of ₹84,00,000 in high-denomination currency notes.
- Branch manager flags the cash withdrawal request; customer provides a handwritten letter stating "proceeds from sale of ancestral property."
- No sale deed, registered document, or TDS certificate is presented at the time of the withdrawal request.
- Branch delays cash disbursement pending verification; customer provides verbal confirmation of a property sale but cannot recall the sub-registrar's office or registration number.

**Ingested signals:** None from external databases. Alert is internal/branch-initiated.

**Case record in the seed (`ddp/seed_data.py`, 2026-10-28):** a pension credit (₹20,000) and the LIC standing-instruction debit (₹8,000) earlier in the month, then the ₹85,00,000 RTGS. The ₹84L cash withdrawal was requested but not paid, so it is not a transaction. ASSUMED: the dates of the pension and LIC rows; the pension amount within the stated range.

---

### 2. Reasoning Chain

```
RFI-003 (dormant account reactivation) [NEEDS-VERIFICATION]
  → Account has had no customer-initiated transactions for 25+ months. First significant
    inflow is ₹85L from an unknown company, immediately followed by a near-total cash
    withdrawal request. Pattern matches dormant-account reactivation for ML purposes.
  → corpus: RFI-003

POE Factor 2 — Transaction history (POE-003)
  → 30-month pattern of ₹20K/month pension only. ₹85L single credit with same-day
    near-total cash withdrawal is a complete deviation from established baseline.

POE Factor 4 — Income level (POE-005)
  → ₹85L = ~354 months of pension income. If from a property sale, the amount is
    potentially consistent with urban property values, but no documentation.

POE Factor 5 — Source of income (POE-006)
  → Stated source: property sale. No documentary evidence provided. The sender
    (Greenfield Developers Pvt Ltd) appears to be a private company; no business
    relationship with this customer is on record.

POE Factor 12 — KYC availability (POE-012)
  → KYC last updated 3 years ago. No mention of property ownership in the KYC record.
    No update to reflect any property sale transaction.
```

**CONTESTED — two defensible PO readings:**

**Reading A — FILE STR:**
- Dormancy + sudden large credit from unknown company + same-day near-total cash withdrawal = classic cash-back scheme or placement layer
- No documentation provided; verbal explanation is insufficient
- ₹85L cash withdrawal would itself be a reportable cash transaction (CTR)
- The RE cannot verify the property sale claim without documents
- A PO who waits for documents and the customer never returns has suppressed a flagged case without a filed STR
- Safer to file now; documentation can be updated if customer provides evidence

**Reading B — CLOSE-NO-FILE (conditional on documentation):**
- Retired principal, 68 years, 30-month pension-only account — not a typical ML profile
- Property sale at ₹85L is entirely plausible in urban India (even a tier-2 city flat)
- The sale proceeds routing through a developer's account (Greenfield Developers) would make sense if the developer was the buyer and paid directly
- If the customer provides (a) registered sale deed, (b) TDS certificate (Form 16B), (c) capital gains computation — the transaction is fully explained
- Filing an STR on a genuine elderly property seller because documentation was not immediately available at a bank branch is a false positive with real harm to the customer

**The crux:** The RE currently has no documentation. The PO must decide: file now on incomplete information, or defer for 5–7 working days pending document collection?

---

### 4. Draft Closure Rationale (conditional — if documentation received)

If within 5 working days of the alert, CUST-03 provides a registered sale deed (with sub-registrar stamp and registration number), TDS certificate (Form 16B showing deduction at source on property sale), and buyer confirmation that Greenfield Developers Pvt Ltd was the purchasing party, the following closure rationale would apply:

The ₹85L credit from Greenfield Developers Pvt Ltd represents confirmed proceeds from the registered sale of [property description] by CUST-03. The sale deed is registered at [sub-registrar's office], registration no. [X], dated [date]. TDS at the applicable rate was deducted by the buyer. The cash withdrawal request (for nearly the full credit) was fulfilled after documentation was verified and the branch manager obtained the RE's compliance officer's sign-off.

The dormancy anomaly (RFI-003) is explained by the property sale being a one-time event; the customer's 30-month pension-only baseline is consistent with a retired individual with limited financial activity. No other red-flag indicators apply. Alert closed; documentation retained per PMLA s.12(1)(c) [corpus: RR-001].

---

### 5. Templated-Narrative Check

(Applicable to Reading A — FILE version)

- Uses generic phrases without specifics: **PASS** — specific amounts, sender name, withdrawal request date
- Does not cite specific amounts/dates: **PASS**
- Does not name specific red-flag indicators: **PASS** — RFI-003 named; dormancy period cited
- Does not explain contradiction with stated profile: **PASS** — 354-month income equivalent; pension-only baseline
- Does not address relevant PO evaluation factors: **PASS** — Factors 3, 4, 5, 12 addressed
- Beneficiary relationship not discussed: **PASS** — Greenfield Developers relationship unexplained
- Geography risk not discussed: **N/A** — domestic
- KYC inconsistency not discussed: **PASS** — no property ownership in KYC noted
- Could apply to any customer without modification: **PASS** — CUST-03 specific
- Substantially identical to a previous STR: **N/A**

**Result: 0 fails (on Reading A version).**

---

### 6. Contestedness Note

This is a genuine two-PO disagreement scenario. The key variable is whether documentation is received within the 7-working-day STR deadline window.

**Decision tree the product should present:**
1. Can the customer provide documentation within 5 working days (leaving 2 WD buffer)?
   - YES → request documentation, defer disposition, re-evaluate at day 5
   - NO / customer unresponsive → FILE STR, note "documentation requested, not received"
2. If documentation received and verified → CLOSE-NO-FILE with documented rationale
3. If documentation received but does not check out (mismatched registration, etc.) → FILE STR

**Human decision required:** Which reading to hard-code as the FINAL scenario? Options:
(A) FILE because documentation not provided within deadline — tests STR-002 SLA
(B) CLOSE-NO-FILE because documentation was provided — tests INS-001 rationale quality
(C) Keep as CONTESTED — tests the product's ability to present both readings

**Recommended:** Keep as CONTESTED. This scenario tests the most valuable product capability: supporting a PO through a genuinely ambiguous case rather than outputting a deterministic answer.

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
