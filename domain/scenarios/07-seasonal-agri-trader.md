---
id: "07"
title: "Seasonal agricultural trader — large post-harvest cash deposits with documented pattern"
status: FINAL
disposition: CLOSE-NO-FILE
rules_cited: [STR-001, CTR-001, POE-001, POE-002, POE-003, POE-005, POE-009, INS-001]
---

### 1. Synthetic Pattern

**Account:** Current account, cooperative bank, small-town branch, Maharashtra
**Customer KYC (CUST-07):** Business: sole proprietor grain trader (wheat, soybean); GST-registered (trading); declared annual turnover: ₹1.8 crore; mandi licence number on file; risk category: Medium; KYC updated 8 months ago; business address: APMC yard, Latur.

**Baseline (4 prior years):** Transaction history at this RE spans 5 years. Annual pattern observed in each prior year:

| Period | Pattern |
|---|---|
| June–September | Low activity; occasional small payments to suppliers; working-capital loan debit (MSME loan) |
| October–November | Large cash deposits (post-kharif harvest procurement season); ₹35L–₹55L aggregate cash per year |
| December–March | RTGS payments to commodity traders and exporters; slow drawdown |
| April–May | Account near-zero; working-capital loan utilisation; Rabi inputs |

**Alert year (year 5), October–November:**
- 22 cash deposits over 45 days; amounts range from ₹80,000 to ₹3,50,000 per deposit
- Total cash deposits: ₹48,20,000 (₹48.2 lakh)
- CTR obligation triggered: monthly aggregate > ₹10L [corpus: CTR-001]

**Additional documents on file:**
- Mandi procurement receipts (farukha/kanda receipts) totalling ₹46.8L for kharif wheat purchased from 15 registered farmers; matching dates and amounts to the deposit pattern
- Previous 4 years' ITR (audited) confirming seasonal turnover of ₹1.5–2.1 crore
- Bank's own credit officer conducted business review 8 months ago; report on file confirms seasonal cash business, APMC registration, and farmer supplier relationships

**Case record in the seed (`ddp/seed_data.py`, 2026-10-28):** 22 cash deposits of ₹80,000 to ₹3,50,000 over 45 days, ending the day before the alert date (18 Jul – 31 Aug 2026). ASSUMED: the individual amounts and dates. FOR DOMAIN REVIEW: the seed's alert date (1 Sep 2026) puts these deposits in July–August, not the October–November season described above (the draft no longer names the months); and wheat is a rabi crop, so "kharif wheat" may need correcting.

---

### 2. Reasoning Chain

```
Alert trigger: automated CTR-threshold rule on October monthly aggregate > ₹10L
  → CTR obligation exists and is being filed. This is not in dispute.
  → corpus: CTR-001

STR evaluation — does suspicion exist?

POE Factor 1 — Business profile (POE-002)
  → CUST-07's stated business is grain trading at APMC. Cash procurement from
    farmers is the norm in Indian agricultural markets; most kisan transactions
    are cash-based, particularly at mandi level. Large seasonal cash deposits
    are entirely consistent with the declared business.

POE Factor 2 — Transaction history (POE-003)
  → The October–November cash deposit pattern has been observed identically in
    each of the 4 prior years (₹35L–₹55L seasonal). This is the baseline, not
    a deviation from it. The alert is pattern-consistent, not anomalous.

POE Factor 4 — Income level (POE-005)
  → ₹48.2L in the harvest season is 26.8% of declared annual turnover of ₹1.8Cr.
    Consistent with the scale of declared operations.

POE Factor 8 — Transaction size (POE-009)
  → Individual deposits ₹80K–₹3.5L. This is consistent with a trader making
    multiple daily purchases from different farmers; no single deposit suggests
    structuring (amounts are irregular, not systematically sub-₹10K).

Supporting documentation:
  → Mandi receipts (farukha) totalling ₹46.8L match the deposit amounts and dates.
    These are primary-source documents issued by the APMC mandi; they are not
    self-prepared by CUST-07. 15 named farmer-suppliers.
  → 4 years of audited ITR confirm seasonal pattern.
  → RE's own credit officer business review 8 months ago is on file.
```

**Conclusion:** Suspicion is not formed. The alert was triggered by an automated CTR-threshold rule, which is correct (CTR must be filed). But the STR threshold requires suspicion [corpus: STR-001], and the evidence here supports a documented innocent explanation: seasonal agricultural procurement cash in a correctly profiled business with consistent prior-year pattern and primary-source documentation.

A PO who files an STR here without engaging with the available documentation would be filing without genuine suspicion — which is itself an inspection risk (implausibly high alert-to-STR ratio; corpus: INS-003).

---

### 4. Draft Closure Rationale

Alert raised by automated CTR monitoring: cash deposits of ₹48,20,000 over 45 days, with each calendar month's cash total above the CTR-001 threshold. CTR is being filed for the relevant months.

STR evaluation conducted by the undersigned PO. Suspicion is not formed for the following reasons:

(a) **Documented business purpose:** CUST-07 is a GST-registered grain trader with a mandi licence operating from the APMC yard, Latur. Cash procurement from farmers is standard market practice in the kharif grain trade. Mandi farukha receipts for the same period, corresponding to purchases from 15 named registered farmers, have been verified.

(b) **Consistent 4-year pattern:** The seasonal cash deposit pattern is consistent with the prior 4 years of transaction history at this RE. The amount (₹48.2L) falls within the range observed in those years.

(c) **Income consistency:** ₹48.2L represents 26.8% of declared annual turnover; consistent with scale of operations. Four years of audited ITR are on file.

(d) **Recent business review:** The RE's credit officer conducted a business review 8 months ago and confirmed the seasonal cash business model, APMC registration, and farmer supplier relationships.

No other red-flag indicators are present. Alert closed. CTR filed per schedule. Mandi receipts, ITR copies, and business review report retained per PMLA s.12(1)(c) [corpus: RR-001]. Re-evaluation triggered if deposit pattern in subsequent months deviates materially from this established profile.

---

### 5. Templated-Narrative Check

(Applicable to closure rationale — all four rationale elements are specific to CUST-07)

- Rationale is generic / could apply to any trader: **PASS** — Latur APMC, specific amounts, specific document references
- Does not cite the specific alternative explanation: **PASS** — mandi receipts, ITR, credit review all cited
- Does not address each triggered PO factor: **PASS** — Factors 1, 2, 4, 8 all addressed in the rationale

**Result: Closure rationale is defensible.**

---

### 7. Human Review

```
status: corrected
reviewer: —
date: —
decision: —
correction_notes: "POE corpus ID misreferences corrected in body text and rules_cited frontmatter."
domain_rule_extracted: "Automated CTR-threshold alerts do not automatically trigger STR obligations.
A PO must form genuine suspicion before filing an STR. Well-documented seasonal business patterns
with consistent prior-year history and primary-source documentation are grounds for a not-file
closure. The closure rationale must document the alternative explanation and the evidence
that supports it. (corpus: STR-001; INS-001)"
```
