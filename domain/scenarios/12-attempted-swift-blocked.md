---
id: "12"
title: "Attempted SWIFT to watchlisted beneficiary — blocked twice, STR on attempted transactions"
status: FINAL
disposition: FILE
rules_cited: [STR-001, STR-002, STR-003, RFI-008, POE-001, POE-002, POE-011, SB-002, INS-002]
---

### 1. Synthetic Pattern

**Account:** Savings account, private sector bank, urban branch
**Customer KYC (CUST-12):** Occupation: small business owner (import of electronic goods); declared income: ₹4,50,000/year; risk category: Medium; GST-registered; KYC updated 2 years ago.

**Baseline (months 1–18):** Modest account activity. NEFT payments to domestic suppliers. Occasional inward RTGS from customers. No prior international wire transfer history. Account primarily used for domestic business settlement.

**Alert events:**

| Event | Date | Type | Amount | Beneficiary | Outcome |
|---|---|---|---|---|---|
| Attempt 1 | T+1 | Outward SWIFT | USD 18,000 (≈₹15L) | Zhao Trading Co., Shenzhen, China — account at [Bank A, Shenzhen] | BLOCKED by bank's compliance system (internal watchlist hit: [Bank A, Shenzhen] is flagged in the bank's correspondent risk database) |
| Attempt 2 | T+4 | Outward SWIFT | USD 18,000 (≈₹15L) | Zhao Trading Co., Shenzhen, China — same beneficiary, different correspondent bank routing (via [Bank B, Hong Kong]) | BLOCKED again (same beneficiary flagged) |

**Additional facts:**
- CUST-12 has no prior international wire transfer history in 18 months.
- The beneficiary (Zhao Trading Co.) is not a previously known counterparty of CUST-12.
- The stated purpose on both SWIFT messages: "Advance payment for import of electronic goods."
- Declared import business exists and is GST-registered, but the volume of this transaction (USD 18,000 = ~₹15L) is significantly larger than CUST-12's declared annual income of ₹4.5L.
- CUST-12 attempted to re-route on day T+4 using a different correspondent bank after the first block — indicating awareness of the first block and an attempt to circumvent it.

**STR obligation under STR-003:** Both transactions were attempted but not completed. The attempted-transaction rule (corpus: STR-003) applies: STR is required even though no funds were transferred.

---

### 2. Reasoning Chain

```
STR-003 (attempted transactions) [PROVEN]
  → Both SWIFT transfers were attempted and blocked. PMLA and FIU-IND guidance
    require STR filing for attempted transactions where suspicion criteria are met.
    The fact that no funds left the account does not extinguish the STR obligation.
  → corpus: STR-003

RFI-008 (cross-border to high-risk counterparty / correspondent)
  → Attempt 1: beneficiary bank flagged in internal correspondent risk database.
    China is not FATF-listed, but the specific correspondent [Bank A] carries
    an internal risk designation. The re-routing attempt via Hong Kong on T+4
    is itself a suspicion amplifier: it demonstrates awareness of the first block
    and deliberate circumvention.
  → corpus: RFI-008

POE Factor 1 — Business profile (POE-002)
  → CUST-12 is a declared importer of electronic goods. Advance payment to a
    Chinese trading company is ostensibly consistent with the stated business.
    However: (a) no prior such payment in 18-month history; (b) USD 18,000 =
    ₹15L against declared annual income of ₹4.5L (the transaction value is
    3.3× annual income); (c) the counterparty bank is flagged in the bank's
    own risk system. The business profile is consistent with the stated purpose
    but not with the transaction scale or counterparty risk.

POE Factor 10 — Geographies (POE-011)
  → China is not on the FATF list but the specific correspondent bank [Bank A]
    carries a designated risk. The re-routing attempt via Hong Kong adds a
    second jurisdiction. The pattern of "try one route → blocked → try another
    route" is unusual for a legitimate commercial import payment.

Re-routing attempt as amplifier:
  → The attempt on T+4 with a different correspondent is not a coincidence or
    administrative error. CUST-12 was aware the first SWIFT was blocked (banks
    notify the initiating customer of a block). The re-routing attempt, using a
    different correspondent to the same blocked beneficiary, suggests the
    transaction is intended to succeed regardless of compliance controls.
    This materially strengthens the suspicion basis.

Statutory basis:
  → PMLA 2002 s.12(1)(b) [corpus: SB-002]: suspicion formed on attempted transactions.
  → STR-003 [corpus]: STR required even though no funds transferred.
  → 7-working-day clock begins from the date of the first attempt (T+1) [corpus: STR-002].
```

**Alternative explanation considered:** Legitimate import advance payment to a Chinese goods supplier. The re-routing attempt was because CUST-12 didn't understand why the first transfer was blocked (administrative confusion). Rejected: a customer told their SWIFT was blocked due to a compliance flag would not normally re-attempt the same payment to the same blocked beneficiary via a different route four days later. The re-routing behaviour is the decisive factor — it is inconsistent with innocent intent.

---

### 3. Draft Ground of Suspicion

Account holder CUST-12, a declared importer of electronic goods (GST-registered, declared income ₹4,50,000/year), attempted two outward SWIFT transfers on [T+1] and [T+4] — both for USD 18,000 (≈₹15L) to Zhao Trading Co., Shenzhen, China — stating "advance payment for import of electronic goods." Both attempts were blocked by this RE's compliance system: the first because the named correspondent bank [Bank A, Shenzhen] appears on the RE's internal correspondent risk register; the second because the same beneficiary was flagged.

Neither transaction was completed. Both constitute attempted transactions reportable under PMLA 2002 s.12(1)(b) and the FIU-IND requirement to file STRs for attempted transactions (corpus: STR-003).

The following circumstances form the basis for suspicion: (a) the first block was communicated to CUST-12; (b) four days later, CUST-12 re-attempted the identical transfer to the same blocked beneficiary using an alternative correspondent routing via Hong Kong, demonstrating awareness of the first block and a deliberate attempt to circumvent the compliance control; (c) USD 18,000 (₹15L) represents 3.3× CUST-12's declared annual income of ₹4.5L, with no prior international wire transfer history in 18 months; (d) Zhao Trading Co. is not a known counterparty in CUST-12's transaction history.

The re-routing behaviour on T+4 — specifically, the use of a different correspondent bank to reach the same blocked beneficiary — is inconsistent with a legitimate import payment where an administrative block would normally prompt a phone call to the bank, not an alternate-route re-attempt. This behaviour materially strengthens the suspicion that the transfer was intended for a purpose that warranted circumventing the compliance block.

Suspicion is formed under PMLA 2002 s.12(1)(b) for both attempted transactions on the basis of: (a) attempted transfers to a flagged-correspondent-linked beneficiary (RFI-008); (b) deliberate circumvention attempt after first block; (c) transaction size 3.3× annual declared income (POE Factor 4); and (d) no prior counterparty relationship (POE Factor 1). No funds were transferred; both STRs cover attempted transactions.

---

### 5. Templated-Narrative Check

- Uses generic phrases without specifics: **PASS** — USD 18,000 × 2, dates T+1 and T+4, Zhao Trading Co., Shenzhen, re-routing specifics
- Does not cite specific amounts/dates: **PASS**
- Does not name specific red-flag indicators: **PASS** — RFI-008 named; attempted-transaction rule (STR-003) cited
- Does not explain contradiction with stated profile: **PASS** — 3.3× annual income; no prior international wire history
- Does not address relevant PO evaluation factors: **PASS** — Factors 1, 4, 10 addressed
- Beneficiary relationship not discussed: **PASS** — no prior counterparty relationship noted
- Geography risk not discussed: **PASS** — correspondent bank risk flag; Hong Kong re-routing cited
- KYC inconsistency not discussed: **N/A** — KYC complete; the issue is transaction scale and behaviour
- Could apply to any customer without modification: **PASS** — CUST-12, specific amounts, specific re-routing behaviour
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
domain_rule_extracted: "Re-routing an attempted transaction to the same blocked beneficiary
via a different correspondent is a material suspicion amplifier — it demonstrates deliberate
circumvention intent. This should be captured as a first-class signal in the product's
alert-enrichment layer. (corpus: STR-003; RFI-008)"
```
