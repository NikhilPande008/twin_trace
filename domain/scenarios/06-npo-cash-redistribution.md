---
id: "06"
title: "NGO account receives large cash donations and immediately redistributes to unknown individuals"
status: FINAL
disposition: FILE
rules_cited: [STR-001, STR-002, NTR-001, CTR-001, RFI-010, POE-001, POE-006, POE-007, POE-008, INS-001]
---

### 1. Synthetic Pattern

**Account:** Current account, public sector bank, urban branch
**Customer KYC (CUST-06):** Entity name: Seva Prakash Welfare Trust; entity type: Registered trust (Trust Deed on file); stated purpose: disaster relief and rehabilitation; trustees: 3 named individuals; risk category: High (NPO — correctly classified per KYC norms); registered address: urban Metro city; GST exemption certificate on file (80G).

**Baseline (months 1–12):** Occasional cheque credits from known donors (₹5,000–₹50,000 each); occasional debits to vendors for event logistics (catering, tarpaulins, transport). Consistent with a small charitable trust. No large transactions.

**Alert period (days T+1 to T+8):**

| Day | Transaction | Amount | Mode | Counterparty |
|---|---|---|---|---|
| T+1 | Credit | ₹1,50,000 | Cash (over counter) | Walk-in donor (no PAN disclosed) |
| T+1 | Credit | ₹2,00,000 | Cash (over counter) | Walk-in donor (no PAN disclosed) |
| T+2 | Credit | ₹1,80,000 | Cash (over counter) | Walk-in donor (no PAN disclosed) |
| T+3 | Credit | ₹2,50,000 | Cash (over counter) | Walk-in donor (no PAN disclosed) |
| T+4 | Credit | ₹1,20,000 | Cash (over counter) | Walk-in donor (no PAN disclosed) |
| T+4 | Credit | ₹2,00,000 | Cash (over counter) | Walk-in donor (no PAN disclosed) |
| T+5 | Credit | ₹1,80,000 | Cash (over counter) | Walk-in donor (no PAN disclosed) |
| T+6 | Credit | ₹1,50,000 | Cash (over counter) | Walk-in donor (no PAN disclosed) |
| T+7 | Credit | ₹2,20,000 | Cash (over counter) | Walk-in donor (no PAN disclosed) |
| T+8 | Credit | ₹1,50,000 | Cash (over counter) | Walk-in donor (no PAN disclosed) |
| T+8 | Credit | ₹80,000 | Cash (over counter) | Walk-in donor (no PAN disclosed) |
| T+8 | Credit | ₹70,000 | Cash (over counter) | Walk-in donor (no PAN disclosed) |

Total cash credits over 8 days: ₹19,50,000 (₹19.5 lakh). No single deposit exceeds ₹2.5L. All cash, all walk-in donors, none identifying by PAN.

| Day | Transaction | Amount | Mode | Counterparty |
|---|---|---|---|---|
| T+9 | Debit | ₹2,20,000 | UPI | Mobile handle "Ramesh_help" |
| T+9 | Debit | ₹1,80,000 | UPI | Mobile handle "Aid_worker_2" |
| T+9 | Debit | ₹2,50,000 | UPI | Mobile handle "NK_foundation" |
| T+9 | Debit | ₹1,90,000 | UPI | Mobile handle "Field_coord_1" |
| T+9 | Debit | ₹2,10,000 | UPI | Mobile handle "Suresh_relief" |
| T+10 | Debit | ₹2,00,000 | UPI | Mobile handle "Ram_trust" |
| T+10 | Debit | ₹1,70,000 | UPI | Mobile handle "AidCoord_3" |
| T+10 | Debit | ₹2,20,000 | UPI | Mobile handle "Field_lead_J" |

Total debits days T+9–T+10: ₹16,40,000. None of these mobile handles appear in the trust's KYC, vendor list, or prior transaction history as known beneficiaries.

**Ingested signals:** None from external databases. The large cash inflows triggered CTR evaluation and NTR obligation review.

**CTR obligation:** Monthly cash total ₹19.5L > ₹10L → CTR must be filed (corpus: CTR-001). STR warranted independently.
**NTR obligation:** NPO receiving large cash amounts → NTR may be required (corpus: NTR-001; threshold NEEDS-VERIFICATION — DG-16).

**Case record in the seed (`ddp/seed_data.py`, 2026-10-28):** the 12 credits and 8 debits above; T+1 is 18 Aug 2026.

---

### 2. Reasoning Chain

```
RFI-010 (NPO misuse / TF risk) [NEEDS-VERIFICATION]
  → Registered trust receives ₹19.5L in anonymous cash donations over 8 days
    with no PAN identification of donors. Immediately redistributes ₹16.4L to
    8 unknown mobile UPI handles with no documented connection to the trust's
    stated relief activities. This pattern is the canonical TF-via-NPO red flag.
  → corpus: RFI-010

POE Factor 1 — Business profile (POE-002)
  → The trust's stated purpose is disaster relief. The redistribution of ₹16.4L
    to 8 anonymous UPI handles, all with informal names, on days T+9 and T+10
    does not match the trust's 12-month prior pattern of cheque payments to
    event vendors. No disaster event or relief activity is documented in this
    period.

POE Factor 6 — Beneficiary (POE-007)
  → The 8 debit beneficiaries are unknown to the RE, not in the trust's prior
    vendor records, and identified only by informal UPI handles. No field-worker
    contracts, volunteer rosters, or beneficiary lists have been provided.

POE Factor 7 — Transaction frequency (POE-008)
  → 12 cash deposits in 8 days; 8 UPI disbursements on days 9–10. This is a
    complete departure from the trust's 12-month baseline of occasional cheque
    credits and vendor payments.

CTR + NTR dual obligations:
  → CTR mandatory: ₹19.5L cash in calendar month [corpus: CTR-001].
  → NTR likely mandatory: NPO account receiving large transactions [corpus: NTR-001;
    exact threshold DG-16 — NEEDS-VERIFICATION].
  → STR independent of both [corpus: CTR-003 by analogy: dual filing required].

Statutory basis:
  → PMLA 2002 s.12(1)(b) [corpus: SB-002]: suspicion formed.
  → STR deadline 7 working days [corpus: STR-002].
```

**Alternative explanation considered:** Legitimate emergency fundraiser for a specific disaster event (earthquake, flood) with rapid disbursement to field workers. Rejected: (a) no disaster event has been identified for this period; (b) the trust's 12-month history shows no capacity for ₹19.5L fundraising or rapid deployment; (c) legitimate disaster-relief disbursements are typically to known vendors, NGO partner accounts, or named individuals with contracts — not to anonymous mobile handles; (d) none of the donor PAN details were collected, which itself violates I-T Act requirements for 80G trusts above a specified threshold.

---

### 3. Draft Ground of Suspicion

Seva Prakash Welfare Trust (CUST-06), a registered trust with stated purpose of disaster relief, received twelve cash deposits totalling ₹19,50,000 over eight days (T+1 to T+8) — all through walk-in cash deposits at the bank counter, with no PAN identification of donors. The trust's 12-month transaction baseline consisted of occasional cheque credits from known donors and cheque payments to event vendors; the ₹19.5L cash inflow represents 39× the largest prior monthly inflow.

On the two days immediately following the deposits (T+9 and T+10), ₹16,40,000 was transferred via UPI to eight mobile handles — none of which appear in the trust's KYC record, prior vendor list, or documented programme activities. No disbursement supporting documentation (field-worker contracts, beneficiary lists, relief programme records) has been provided. No disaster event or relief programme activity has been identified for this period.

This pattern — anonymous cash donations aggregated through an NPO account and rapidly redistributed to anonymous mobile beneficiaries — is the canonical misuse-of-NPO pattern for layering or TF purposes (RFI-010). The transactions also trigger CTR filing obligations (₹19.5L cash in the calendar month, corpus: CTR-001) and likely NTR obligations (NPO receiving large cash, corpus: NTR-001).

Suspicion is formed under PMLA 2002 s.12(1)(b) on the basis of: (a) NPO misuse pattern — anonymous cash in, immediate anonymous UPI redistribution (RFI-010); (b) complete departure from 12-month baseline (POE Factor 7); (c) eight unknown beneficiaries with no documented relief-programme connection (POE Factor 6); and (d) transaction pattern inconsistent with the trust's stated charitable activity (POE Factor 1). CTR and NTR are being filed in parallel.

---

### 5. Templated-Narrative Check

- Uses generic phrases without specifics: **PASS** — trust name, amounts, 8-day deposit period, 8 UPI handles, 12-month baseline cited
- Does not cite specific amounts/dates: **PASS**
- Does not name specific red-flag indicators: **PASS** — RFI-010 named
- Does not explain contradiction with stated profile: **PASS** — 39× prior monthly inflow; no disaster event documented
- Does not address relevant PO evaluation factors: **PASS** — Factors 1, 6, 7 addressed
- Beneficiary relationship not discussed: **PASS** — 8 handles, none in KYC records
- Geography risk not discussed: **N/A** — domestic
- KYC inconsistency not discussed: **PASS** — no programme documents, no donor PAN collection noted
- Could apply to any customer without modification: **PASS** — trust name, specific amounts, specific pattern
- Substantially identical to a previous STR: **N/A**

**Result: 0 fails.**

---

### 7. Human Review

```
status: FINAL
reviewer: —
date: —
decision: —
correction_notes: —
domain_rule_extracted: —
```
