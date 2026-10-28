---
id: "05"
title: "IT services exporter routes SWIFT via DPRK-linked correspondent to UAE free-zone entity"
status: FINAL
disposition: FILE
rules_cited: [STR-001, STR-002, CBTR-001, RFI-008, POE-001, POE-002, POE-011, SB-005, INS-001]
---

### 1. Synthetic Pattern

**Account:** Current account, private sector bank, export-import business
**Customer KYC (CUST-05):** Business name: Techvision Export Solutions Pvt Ltd; business type: IT services (software development, BPO); declared annual turnover: ₹4.2 crore; GST-registered; risk category: Medium (business account with cross-border activity); KYC: CIN, GST, PAN, director details on file.

**Baseline (months 1–24):** Regular SWIFT inward remittances from IT clients in USA, UK, Singapore, Australia (typical IT export client countries). Occasional outward SWIFT for server hosting costs (USD 3,000–8,000 per payment to AWS, Azure in USA). Consistent turnover pattern. Clean track record.

**Alert period (month 25):**

| Date | Transaction | Amount | Counterparty | Purpose stated |
|---|---|---|---|---|
| T+1 | Outward SWIFT | USD 45,000 (≈₹37.5L) | Regal Trading FZCO, Sharjah, UAE via an intermediary bank in a Democratic People's Republic of Korea (DPRK)-linked correspondent network | "Software development subcontracting" |
| T+22 | Outward SWIFT | USD 32,000 (≈₹26.7L) | Same beneficiary (Regal Trading FZCO) | "Software development subcontracting" |

**Additional facts:**
- DPRK is on the FATF "Black List" (High-Risk Jurisdictions Subject to a Call for Action). The routing through a DPRK-linked correspondent bank is flagged by the RE's SWIFT monitoring.
- Regal Trading FZCO is a UAE free-zone company. UAE was removed from the FATF Grey List at the June 2024 FATF Plenary and is NOT on any FATF risk list as of Sep 2026. The UAE itself is therefore not a jurisdiction-level risk factor in this scenario; the primary risk is the DPRK-linked correspondent routing, not the beneficiary's jurisdiction. (Gap DG-07 is closed for this scenario.)
- The stated purpose "software development subcontracting" is inconsistent with CUST-05's business model: their clients are inward-remittance IT service buyers; they have no known history of subcontracting software work abroad.
- Invoice provided for the first transfer: a one-page PDF invoice from "Regal Trading FZCO" for "technology consulting services." No contract, no deliverable description, no prior relationship documented.
- CUST-05's bank RMs have no record of this vendor in previous discussions with the company.

**CBTR obligation:** Both transfers exceed the indicative CBTR threshold (DG-01 — threshold NEEDS-VERIFICATION at ₹5L). Each transfer (~₹37.5L and ~₹26.7L) far exceeds any plausible threshold. CBTR must be filed; STR must also be filed (the transactions warrant both — corpus: CTR-003 by analogy).

---

### 2. Reasoning Chain

```
RFI-008 (cross-border to high-risk jurisdiction) [NEEDS-VERIFICATION — primary source]
  → First transfer routed through DPRK-linked correspondent bank. DPRK is FATF
    Black-listed (Call for Action — highest risk designation). SWIFT monitoring flagged
    the correspondent chain. The transfer reaches a UAE free-zone company; UAE was
    removed from the FATF grey list in June 2024 and is not risk-listed as of Sep 2026.
    The suspicion basis is the DPRK correspondent routing, not UAE's jurisdiction.
  → corpus: RFI-008, POE-011

POE Factor 1 — Business profile (POE-002)
  → CUST-05 is an IT services exporter (inward remittances for software/BPO work).
    Outward SWIFT for "software subcontracting" to a UAE free-zone trading company
    is inconsistent with this business model. IT services firms typically subcontract
    to other IT firms, not to trading companies. Regal Trading FZCO's "FZCO" suffix
    (Free Zone Company) is a UAE entity type commonly used for trade facilitation.

POE Factor 10 — Geographies (POE-011)
  → DPRK correspondent chain: FATF Black List jurisdiction — highest risk.
    UAE: removed from FATF grey list June 2024; not risk-listed as of Sep 2026.
    Geography risk in this scenario is entirely from the DPRK correspondent routing,
    not from the UAE beneficiary jurisdiction.
    Neither the DPRK routing nor UAE appears in CUST-05's 24-month transaction history.

Invoice quality assessment:
  → One-page invoice with no contract reference, no deliverable description, no
    prior payment history, no SWIFT message confirming prior relationship. Invoice
    alone is insufficient to explain the transaction (POE Factor 5 — source of
    outgoing funds / commercial purpose not established).

Statutory basis:
  → PMLA 2002 s.12(1)(b) [corpus: SB-002]: suspicion formed.
  → CBTR obligation [corpus: CBTR-001]: both transfers trigger CBTR (threshold
    verification pending DG-01; both transfers far exceed any plausible threshold).
  → STR and CBTR to be filed independently [corpus: CTR-003 by analogy].
```

**Alternative explanation considered:** Legitimate offshore subcontracting to a UAE vendor for cost arbitrage. Rejected: (a) routing through a DPRK-linked correspondent bank has no legitimate cost-arbitrage explanation; (b) the vendor is a trading company, not an IT firm; (c) no prior relationship or contract documentation; (d) the invoice is a bare one-pager. The combination of DPRK correspondent routing + UAE trading company + thin documentation + inconsistent business purpose is sufficient for suspicion without requiring certainty about the ultimate purpose.

---

### 3. Draft Ground of Suspicion

Techvision Export Solutions Pvt Ltd (CUST-05), an IT services exporter with a 24-month history of inward remittances from USA, UK, Singapore, and Australia, made two outward SWIFT transfers on [T+1] and [T+22] — USD 45,000 (≈₹37.5L) and USD 32,000 (≈₹26.7L) respectively — to Regal Trading FZCO, Sharjah, UAE, citing "software development subcontracting." The first transfer was routed through a correspondent bank with known links to DPRK financial networks (FATF High-Risk Jurisdiction — Black List, Call for Action). The SWIFT monitoring system flagged the correspondent chain.

Regal Trading FZCO is a UAE free-zone company with no prior relationship documented in CUST-05's account history. The stated purpose of "software development subcontracting" is inconsistent with CUST-05's business model: the company receives inward remittances for IT services (it is a net exporter of services) and has no documented history of procuring subcontracted services abroad. The only documentation produced is a one-page invoice with no contract reference, no deliverable specification, and no prior payment history.

The combination of (a) a DPRK-linked correspondent routing, (b) a UAE free-zone entity as nominal beneficiary, (c) a stated purpose inconsistent with the company's business profile, and (d) insufficient supporting documentation is the basis for suspicion that these transfers may be a layering mechanism — using a thin commercial invoice to route funds through FATF-risk jurisdictions.

Suspicion is formed under PMLA 2002 s.12(1)(b) on the basis of: (a) cross-border transfer through a FATF Black-Listed jurisdiction correspondent chain (RFI-008); (b) beneficiary business profile inconsistent with stated purpose (POE Factor 1); (c) jurisdictional risk — DPRK (POE Factor 10); and (d) insufficient commercial documentation for the transaction amount (POE Factor 5 by analogy). CBTR also being filed for both transfers.

---

### 5. Templated-Narrative Check

- Uses generic phrases without specifics: **PASS** — entity name, amounts, dates, DPRK-linked routing, FZCO type all specific
- Does not cite specific amounts/dates: **PASS**
- Does not name specific red-flag indicators: **PASS** — RFI-008 named; FATF Black List cited
- Does not explain contradiction with stated profile: **PASS** — IT exporter vs. outward subcontracting to trading company
- Does not address relevant PO evaluation factors: **PASS** — Factors 1, 5, 10 addressed
- Beneficiary relationship not discussed: **PASS** — no prior relationship; invoice quality assessed
- Geography risk not discussed: **PASS** — DPRK and UAE FATF status discussed
- KYC inconsistency not discussed: **N/A** — KYC complete; the issue is transaction inconsistency
- Could apply to any customer without modification: **PASS** — CUST-05's specific business model is central
- Substantially identical to a previous STR: **N/A**

**Result: 0 fails.**

---

### 7. Human Review

```
status: corrected
reviewer: —
date: —
decision: —
correction_notes: "Domain content: UAE removed from FATF grey list June 2024 — UAE is NOT grey-listed as of Sep 2026; DPRK-linked correspondent routing is the sole FATF-risk factor; all grey-list references corrected. Title updated to reflect this. POE-010→POE-011 (Geographies) corrected in frontmatter. POE-002 (Business Profile) added to frontmatter."
domain_rule_extracted: —
```
