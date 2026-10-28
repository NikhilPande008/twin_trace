---
id: "08"
title: "IT professional receives ₹75L — documented property sale proceeds"
status: FINAL
disposition: CLOSE-NO-FILE
rules_cited: [STR-001, POE-003, POE-005, POE-006, INS-001]
---

### 1. Synthetic Pattern

**Account:** Savings account, private sector bank, urban branch
**Customer KYC (CUST-08):** Occupation: senior software engineer; employer: MNC (NEFT salary visible); declared income: ₹1,85,000/month (CTC basis); risk category: Low; KYC updated 14 months ago; Aadhaar + PAN linked; home address: Bengaluru.

**Baseline (months 1–36):** Regular salary credits ₹1,78,000–₹1,90,000/month. SIP investments (₹50,000/month, NEFT to AMC). EMI debit for home loan (₹65,000/month). Household expenses. Occasional large debits for travel or electronics (₹30K–₹1.5L range). Clean, predictable mid-income professional pattern.

**Alert month (month 37):**
- Day T+1: Credit of ₹75,00,000 (₹75 lakh) via RTGS from "DSK Law Associates — Client Account" (law firm)
- No prior large credits in 36-month history
- Alert triggered: automated flag on RTGS > ₹50L to savings account

**Customer response (within 3 working days of alert):**
CUST-08 visits the branch with a relationship manager appointment, anticipating the bank's inquiry. Documents provided:

1. Registered sale deed for apartment at Koramangala, Bengaluru: dated T−14; sub-registrar's office stamp and document number; sale price ₹82L
2. Form 16B (TDS certificate on property purchase) issued by the buyer: TDS deducted ₹7.5L (1% on ₹75L net sale consideration after deduction of outstanding home loan closure)
3. Home loan closure letter from bank: loan of ₹68L closed from property sale proceeds on T−5; the ₹75L credit represents the net sale consideration after the RE's own loan was pre-paid at T−5
4. Capital gains computation sheet (CA-prepared): long-term capital gain declared; Section 54 exemption application noted (reinvestment intent)

**Linked accounts:** The outstanding home loan on the sold property was with a different product (home loan account) at the same RE. The home loan was closed on T−5 from the sale proceeds (₹68L direct disbursement from buyer to this RE's home loan account, separate RTGS — this does not appear in the savings account).

---

### 2. Reasoning Chain

```
Alert trigger: automated rule on RTGS credit > ₹50L
  → This is a system-generated alert, not a suspicion-based one.

STR evaluation — does suspicion exist?

POE Factor 2 — Transaction history (POE-003)
  → 36-month clean history of a salaried professional. ₹75L is a one-off credit
    of a character (property sale proceeds via law firm client account) that is
    a normal lifecycle event for a mid-career professional. No recurring pattern.

POE Factor 4 — Income level (POE-005)
  → ₹75L = 40.5 months of net take-home. This is entirely consistent with urban
    residential property appreciation over a holding period. The sale deed
    confirms the gross sale price was ₹82L; the net credit (₹75L) is the
    remainder after the buyer's TDS deduction.

POE Factor 5 — Source of income (POE-006)
  → Source is the registered sale of a residential flat, documented by:
    (a) registered sale deed with sub-registrar office number
    (b) Form 16B issued by the buyer — government-issued TDS certificate
    (c) home loan closure letter from the RE's own records
    (d) CA-prepared capital gains computation
    All four documents are primary-source or independently verifiable.

Documentation assessment:
  → This is the closest a private-individual transaction can come to full
    documentary proof. The Form 16B is issued by the buyer (not the seller)
    and is backed by TDS deposition with the government. The sale deed is a
    registered government document. The home loan closure is in the RE's own
    records. No document was produced by CUST-08 alone.
```

**Conclusion:** Suspicion is not formed. The credit is the documented net proceeds of a registered residential property sale. Every element of the transaction is supported by primary-source or independently verifiable documentation. The alert was triggered by a threshold rule; the STR test requires suspicion, which is absent here [corpus: STR-001].

---

### 4. Draft Closure Rationale

Alert triggered by automated RTGS monitoring (credit > ₹50L). STR evaluation conducted by the undersigned PO.

The ₹75,00,000 credit on [T+1] from DSK Law Associates (Client Account) represents the net sale consideration for a residential flat in Koramangala, Bengaluru, sold by CUST-08 under a registered sale deed dated [T−14] (sub-registrar document no. [X]). Documentation verified:

(a) **Registered sale deed:** Gross sale price ₹82,00,000; document registered at [sub-registrar's office]; stamp and registration number confirmed.

(b) **Form 16B (buyer TDS certificate):** TDS of ₹7,50,000 (approx. 1% on ₹75L net consideration) deducted and deposited by the buyer. Government-issued; independently verifiable through TRACES.

(c) **Home loan closure:** CUST-08's outstanding home loan with this RE (account [X]) was closed from the sale proceeds on [T−5]; closure letter on file. The ₹75L credit represents the net proceeds after the direct home-loan repayment of ₹68L (which did not pass through the savings account).

(d) **Capital gains computation:** CA-prepared; long-term capital gain declared; Section 54 reinvestment exemption noted. ITR amendment intended.

CUST-08's 36-month transaction history is consistent with a salaried IT professional; no other anomalies. The property sale is a one-time lifecycle event with full documentation.

Suspicion not formed. Alert closed. All documents retained per PMLA s.12(1)(c) [corpus: RR-001].

---

### 5. Templated-Narrative Check

(Closure rationale specific to CUST-08)

- Rationale is generic / could apply to any customer: **PASS** — Koramangala address, specific document references, home loan account reference
- Does not explain the source of funds: **PASS** — four distinct documents cited, each independently verifiable
- Does not address why no suspicion: **PASS** — POE Factors 3, 4, 5 addressed; documentation quality assessed

**Result: Closure rationale is defensible.**

---

### 7. Human Review

```
status: corrected
reviewer: —
date: —
decision: —
correction_notes: "POE corpus ID misreferences corrected in body text and rules_cited frontmatter."
domain_rule_extracted: "Form 16B (buyer TDS certificate) + registered sale deed + RE's own
loan-closure record constitutes near-conclusive documentation for a property-sale credit.
No STR obligation arises where the source of funds is fully documented from primary-source
and government-issued instruments. The PO must still document the evaluation in the ledger.
(corpus: STR-001; INS-001)"
```
