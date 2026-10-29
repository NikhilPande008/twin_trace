---
id: "10"
title: "Five unrelated accounts all channelling funds to a single UPI handle — layering indicator"
status: FINAL
disposition: FILE
rules_cited: [STR-001, STR-002, RFI-007, RFI-001, POE-006, POE-010, POE-003, INS-001]
---

### 1. Synthetic Pattern

**Bank:** Public sector bank, urban branch
**Detection source:** Bank's transaction monitoring system identifies beneficiary concentration: five savings accounts — held by different customers with no apparent relationship — are all sending funds to the same UPI handle ([HANDLE-Z]) within a 60-day window.

**Account profiles:**

| Account | Customer | KYC occupation | Income declared | Account vintage |
|---|---|---|---|---|
| ACCT-10-1 | CUST-10-A | Courier delivery agent | ₹18K/month | 8 months |
| ACCT-10-2 | CUST-10-B | Domestic worker | ₹10K/month | 14 months |
| ACCT-10-3 | CUST-10-C | Retired government clerk | ₹15K/month pension | 4 years |
| ACCT-10-4 | CUST-10-D | Small kirana shop owner | ₹25K/month | 11 months |
| ACCT-10-5 | CUST-10-E | Construction labourer | ₹12K/month | 6 months |

No family, business, or social relationship between these five account holders is apparent from KYC records, linked accounts, or nominee/guarantor records.

**Debit pattern to [HANDLE-Z] over 60 days:**

| Account | # of debits to [HANDLE-Z] | Total amount sent |
|---|---|---|
| ACCT-10-1 | 4 | ₹48,000 |
| ACCT-10-2 | 3 | ₹32,000 |
| ACCT-10-3 | 5 | ₹67,000 |
| ACCT-10-4 | 6 | ₹82,000 |
| ACCT-10-5 | 3 | ₹35,000 |
| **Total** | **21 transfers** | **₹2,64,000** |

**Credit pattern for each account during the same period:**
All five accounts received regular small UPI credits (amounts ₹5,000–₹25,000 per credit) from multiple different unknown handles — not from each other. No salary NEFT, no known employer credit. Credits are irregular in amount and timing.

**Ingested signals:** [HANDLE-Z] appears in I4C Suspect Registry as flagged in connection with a "cyber fraud — investment scam" scheme, registration date 3 weeks before the first debit to [HANDLE-Z] from any of these accounts.

**Case record in the seed (`ddp/seed_data.py`, 2026-10-28):** 21 UPI debits to HANDLE-Z (marked flagged), split per account as in the table, and 17 small UPI credits from unknown handles (₹5,000–₹25,000), ₹2,64,000 in all, so that credits equal the alert amount. ASSUMED: individual amounts and dates (6 Jul – 3 Sep 2026).

---

### 2. Reasoning Chain

```
RFI-007 (beneficiary concentration across unrelated accounts) [NEEDS-VERIFICATION]
  → 5 accounts with no apparent relationship, across different KYC profiles,
    all routing funds to the same single UPI handle. The concentration is the
    signal: individual amounts may be small, but the pattern of 21 transfers
    totalling ₹2.64L from 5 unrelated accounts to one destination is a layering
    indicator (aggregation to [HANDLE-Z] from dispersed sources).
  → corpus: RFI-007

RFI-001 (pass-through elements) [NEEDS-VERIFICATION]
  → The credit pattern for each account (multiple small UPI credits from unknown
    handles → aggregate debit to [HANDLE-Z]) mirrors a mini pass-through per
    account. Individual amounts are modest; aggregate across 5 accounts is material.
  → corpus: RFI-001

I4C signal:
  → [HANDLE-Z] flagged in I4C Suspect Registry (cyber fraud — investment scam),
    registration 3 weeks before first debit. Funds from all 5 accounts flowed
    to a known-suspect beneficiary. This is the RFI-005 pattern applied to a
    group: all 5 accounts are effectively feeders to a fraud network endpoint.

POE Factor 6 — Beneficiary (POE-007)
  → [HANDLE-Z] identity is unknown to any of the 5 REs; no business or personal
    relationship between [HANDLE-Z] and any of the 5 customers is documented.
    The beneficiary is a registered I4C suspect.

POE Factor 9 — Transaction complexity (POE-010)
  → The multi-account structure with a single beneficiary concentration point
    is more complex than any legitimate purpose would require. Each individual
    transfer appears small; the aggregation pattern is the complexity signal.

POE Factor 2 — Transaction history (POE-003)
  → For ACCT-10-3 (4-year-old account), prior history shows pension deposits and
    household debits — no prior UPI transfer to this type of counterparty.
    For the newer accounts, the transfer pattern is visible from early in the
    account lifecycle, consistent with accounts opened for this purpose.

Statutory basis:
  → PMLA 2002 s.12(1)(b) [corpus: SB-002]: suspicion formed for all 5 accounts.
  → STRs to be filed for each account: all 5 accounts are independently reportable.
    Reference the beneficiary concentration link in each STR.
```

**Alternative explanation considered:** Independent transfers from different customers to a single legitimate entity (e.g., a popular vendor, subscription service, informal savings group). Rejected: (a) [HANDLE-Z] is I4C-flagged; (b) the beneficiary's handle name ([HANDLE-Z]) is a personal mobile handle, not a merchant UPI ID (format difference); (c) the crediting pattern for each account (multiple small unknown UPI credits → single debit to [HANDLE-Z]) is inconsistent with organic personal spending; (d) no declared relationship.

---

### 3. Draft Ground of Suspicion

(Template for one account; specific facts differ per account — the common elements are the beneficiary concentration and I4C flag.)

Account ACCT-10-3, held by CUST-10-C (retired government clerk, monthly pension), was identified through cross-account analysis as one of five accounts at this RE transferring funds to a common UPI handle ([HANDLE-Z]) within a 60-day period. ACCT-10-3 made 5 UPI transfers to [HANDLE-Z] during this period. [HANDLE-Z] appears in the I4C Suspect Registry as associated with a cyber fraud investment scam, registered 3 weeks before the first transfer from ACCT-10-3.

CUST-10-C's account shows no prior transaction with [HANDLE-Z] or with counterparties of this character (pension + household debits was the 4-year baseline). These transfers total 4.4× the monthly pension income; no source for the credit inflows (multiple small UPI credits from unknown handles) has been explained.

Cross-account analysis reveals that four additional accounts at this RE — held by individuals with no documented relationship to CUST-10-C — transferred funds to the same [HANDLE-Z] in the same period, for a total of ₹2,64,000 across all five accounts. This beneficiary-concentration pattern (RFI-007) indicates aggregation of funds from dispersed mule accounts to a single criminal endpoint.

Suspicion is formed under PMLA 2002 s.12(1)(b) on the basis of: (a) beneficiary concentration across 5 unrelated accounts to a single I4C-flagged handle (RFI-007, RFI-005); (b) credit-then-debit pass-through element per account (RFI-001); (c) income inconsistency (POE Factor 4); (d) beneficiary is a registered fraud suspect (POE Factor 6); and (e) unnecessary structural complexity — 5 unrelated accounts, single destination (POE Factor 9). Reference is made to companion STRs filed for ACCT-10-1, 2, 4, and 5.

---

### 5. Templated-Narrative Check

- Uses generic phrases without specifics: **PASS** — 5 account references, ₹2.64L total, ₹67K for CUST-10-C specifically, I4C flag
- Does not cite specific amounts/dates: **PASS**
- Does not name specific red-flag indicators: **PASS** — RFI-007, RFI-001, RFI-005 named
- Does not explain contradiction with stated profile: **PASS** — 4-year pension baseline vs. unknown UPI credits + ₹67K
- Does not address relevant PO evaluation factors: **PASS** — Factors 3, 4, 6, 9 addressed
- Beneficiary relationship not discussed: **PASS** — I4C flag; no documented relationship; 5 unrelated accounts
- Geography risk not discussed: **N/A** — domestic
- KYC inconsistency not discussed: **N/A** — KYC complete; the issue is transaction pattern
- Could apply to any customer without modification: **PASS** — CUST-10-C specific + cross-account reference
- Substantially identical to a previous STR: **N/A** (companion STRs noted, not identical)

**Result: 0 fails.**

---

### 7. Human Review

```
status: corrected
reviewer: —
date: —
decision: —
correction_notes: "POE corpus ID misreferences corrected in body text and rules_cited frontmatter."
domain_rule_extracted: "Cross-account beneficiary concentration is an independent suspicion basis
even where individual account amounts are sub-threshold and the individual account's
transaction history appears modest. Each account warrants its own STR; the beneficiary
concentration link must be referenced in each STR's Ground of Suspicion. (corpus: RFI-007)"
```
