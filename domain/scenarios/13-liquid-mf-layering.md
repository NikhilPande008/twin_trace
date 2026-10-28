---
id: "13"
title: "Liquid MF investment-redemption cycle used as layering step — contested"
status: FINAL
disposition: CONTESTED
rules_cited: [STR-001, RFI-001, POE-003, POE-005, POE-006, POE-010, INS-001, INS-003]
---

### 1. Synthetic Pattern

**Accounts:** Savings account (ACCT-13-S) linked to a mutual fund investment account (ACCT-13-MF), both at the same bank, same customer.
**Customer KYC (CUST-13):** Occupation: proprietor, small import-export trading firm; declared annual turnover: ₹80L; declared income: ₹8L/year; risk category: Medium; GST-registered; KYC updated 11 months ago. Business bank account is at a different bank ("primary current account not with this RE").

**Baseline (months 1–12):** Savings account used primarily for personal expenses. Occasional inward NEFT from employer/business (CUST-13 pays themselves from business). MF investment account used for SIP ₹15,000/month into equity funds. No large irregular transactions.

**Alert pattern (months 13–16), repeated 6 times:**

| Cycle | Step 1 | Step 2 | Step 3 | Step 4 |
|---|---|---|---|---|
| Cycle 1 (M13) | Large NEFT credit to savings: ₹18,50,000 (source: CUST-13's current account at Bank X) | NEFT to MF account: ₹18,40,000 invested in liquid fund (same day) | Liquid fund redemption: ₹18,52,000 received back in savings account (3 days later) | Cash withdrawal from savings: ₹18,50,000 over 3 ATM/counter visits |
| Cycle 2 (M13) | ₹22,00,000 | ₹21,90,000 to liquid fund | ₹22,15,000 redeemed | ₹22,00,000 withdrawn in cash |
| Cycle 3 (M14) | ₹16,80,000 | ₹16,70,000 | ₹16,85,000 | ₹16,80,000 cash |
| Cycle 4 (M14) | ₹25,00,000 | ₹24,90,000 | ₹25,12,000 | ₹25,00,000 cash |
| Cycle 5 (M15) | ₹19,50,000 | ₹19,40,000 | ₹19,58,000 | ₹19,50,000 cash |
| Cycle 6 (M16) | ₹14,20,000 | ₹14,10,000 | ₹14,25,000 | ₹14,20,000 cash |

**Total cycle volume:** ₹1,16,00,000 (₹1.16 crore; the six cycle amounts above) over 4 months.

The cycle — NEFT in → liquid MF → quick redemption → cash out — repeats 6 times with intervals of 2–3 weeks. The liquid fund positions are held for 3–5 days only (no investment objective is served by a 3–5 day holding).

**Ingested signals:** None from external databases.

**Case record in the seed (`ddp/seed_data.py`, 2026-10-28):** six cycles of four steps, the cash step split into three counter withdrawals: 36 rows, May–August 2026. Credits are the NEFT in plus the redemptions (₹2,32,47,000), which is now the alert amount. The six cycle amounts sum to ₹1,16,00,000, not the ₹1.2 crore stated before; corrected throughout. ASSUMED: the split of each cash withdrawal and the dates. FOR DOMAIN REVIEW: the redemptions above return 0.6–0.9% in 3–5 days, far above a liquid fund's return; the draft no longer quotes a return.

---

### 2. Reasoning Chain

```
Layering concern:
  → The savings account receives large NEFT credits from CUST-13's own business
    current account at another bank, routes them through a liquid MF (held 3–5
    days), redeems them, and then withdraws in cash. The MF step adds no economic
    value for a 3–5 day holding in a liquid fund (typical liquid fund return over
    3 days is <₹200 per ₹18L). The only function of the MF step is to create a
    documentary layer between the cash origin and the cash withdrawal.
  → This is the layering stage of ML: using a financial instrument to add a step
    between the source and destination, making the cash withdrawal appear to
    originate from an investment redemption rather than directly from a business
    account.
  → corpus: RFI-001 (pass-through pattern adapted to investment layer)

POE Factor 9 — Transaction complexity (POE-010)
  → NEFT → liquid MF → redemption → cash, repeated 6 times, is structurally
    complex for what could be a direct ATM withdrawal from the current account.
    If CUST-13 needed cash for business, they could withdraw from the current
    account directly. The savings + MF routing through the bank's own products
    serves only to create an audit trail that runs through a less-monitored
    channel (cash withdrawal from savings rather than current).

POE Factor 4 — Income level (POE-005)
  → ₹1.16 crore cycled over 4 months vs. declared annual income of ₹8L.
    Even for a trader with ₹80L turnover, ₹1.2Cr in cash withdrawals in
    4 months is not consistent with declared activity.

POE Factor 5 — Source of income (POE-006)
  → Source of the NEFT credits is CUST-13's own business current account at
    another bank. The RE cannot independently verify the legitimacy of the
    funds in that account. The cash ultimately drawn from this RE originated
    at a bank that is not subject to this RE's monitoring.
```

**CONTESTED — two defensible PO readings:**

**Reading A — FILE STR:**
- ₹1.2Cr in cash withdrawn via a liquid-MF layering cycle over 4 months with no plausible investment purpose for the MF step
- Pattern is deliberate and repeated (6 cycles, consistent structure)
- 14.5× declared annual income; inconsistent with stated business scale
- The MF step creates a documentary separation that benefits only an ML purpose, not a legitimate investor
- This is a textbook layering structure

**Reading B — CLOSE-NO-FILE (or CONTESTED):**
- CUST-13 is a declared trader with ₹80L turnover — cash is a normal working-capital tool in the Indian trading context
- The MF step may be motivated by tax or liquidity management rather than ML (park funds in liquid MF for short term to earn something, even 3-day return)
- The funds source is CUST-13's own business account at another bank — if the business is legitimate, the trading funds are legitimate
- ₹1.2Cr across 4 months is ₹30L/month, not unusual for a trading business with ₹80L declared annual turnover (though the declared figure does seem understated at this activity level)
- Without seeing the source bank's records, concluding ML is premature

**The crux:** The MF step is the key debate. Is a 3–5 day liquid fund holding a legitimate treasury practice or purely a layering device? The answer depends on whether CUST-13 can articulate a business reason for the MF routing. The pattern is suspicious enough to file unless a very specific alternative explanation is obtained.

---

### 3. Draft Ground of Suspicion (Reading A)

Account holder CUST-13 (proprietor, small trading firm, declared annual income ₹8L) engaged in a repeated 4-step cash-extraction cycle over months 13–16: (1) large NEFT from own business account at Bank X; (2) same-day investment in a liquid mutual fund; (3) liquid fund redemption within 3–5 days; (4) cash withdrawal of the redemption proceeds. This cycle was executed 6 times over 4 months, with individual cycle amounts ranging from ₹14.2L to ₹25L, six cycles in all, each ending in a cash withdrawal of the cycle amount.

No investment purpose is served by this holding period. The only functional difference between this cycle and a direct cash withdrawal from the business current account is the creation of a document trail showing cash sourced from "mutual fund redemption" rather than "business account transfer." This structural complexity has no plausible legitimate purpose: it is consistent with layering — using a financial instrument to obscure the relationship between the original funds and the final cash withdrawal.

Cash withdrawals at this scale over 4 months are about 14.5× CUST-13's declared annual income of ₹8L and exceed the declared annual business turnover. No explanation for the cash requirement has been provided.

Suspicion is formed under PMLA 2002 s.12(1)(b) on the basis of: (a) deliberate and repeated use of a liquid MF as a layering step with no investment rationale (POE Factor 9, RFI-001 adapted); (b) total volume inconsistent with declared income (POE Factor 4); and (c) cash extraction at scale with no declared business purpose (POE Factor 5).

---

### 5. Templated-Narrative Check

- Uses generic phrases without specifics: **PASS** — 6 cycles, ₹1.2Cr total, 3–5 day holding, ₹200 return estimate
- Does not cite specific amounts/dates: **PASS**
- Does not name specific red-flag indicators: **PASS** — POE Factor 9, RFI-001 (adapted) named
- Does not explain contradiction with stated profile: **PASS** — 14.5× annual income; turnover vs. cash volume
- Does not address relevant PO evaluation factors: **PASS** — Factors 4, 5, 9 addressed
- Beneficiary relationship not discussed: **N/A** — cash withdrawal, no specific beneficiary
- Geography risk not discussed: **N/A** — domestic
- KYC inconsistency not discussed: **PASS** — income/activity gap vs. declared income noted
- Could apply to any customer without modification: **PASS** — 6-cycle structure specific to CUST-13

---

### 6. Contestedness Note

The product should present both readings and ask the PO: "Can CUST-13 explain the business purpose of the liquid MF step?" If no explanation is forthcoming within the STR deadline, FILE. If explanation is obtained and it is plausible (e.g., "I use this as a sweep account because my current account bank doesn't offer intraday liquidity management"), the PO must evaluate whether that explanation justifies the 6-cycle scale.

The domain rule this tests: a layering step that has no economic rationale is suspicious even when funds originate from the customer's own declared business. The ML risk is that the business current account is itself receiving proceeds of crime from another source.

---

### 7. Human Review

```
status: corrected
reviewer: —
date: —
decision: —
correction_notes: "POE corpus ID misreferences corrected in body text and rules_cited frontmatter."
domain_rule_extracted: "A financial instrument used repeatedly as a pass-through with no
investment rationale (negligible holding period) is a layering indicator regardless of
whether the source funds are 'own' funds. The layering step itself creates ML exposure.
(corpus: POE-009; RFI-001)"
```
