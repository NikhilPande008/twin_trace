---
id: "17"
title: "Confirmation-bias trap — I4C signal on legitimate migrant remittance"
status: FINAL
disposition: NOT_FILE
rules_cited: [STR-001, RFI-005, POE-002, POE-003, POE-006, INS-001]
failure_mode: confirmation_bias
---

### 1. Synthetic Pattern

**Account:** Savings account, nationalised bank, metropolitan branch
**Customer KYC (CUST-17):** Occupation: IT professional (software engineer); declared income:
₹1,20,000/month; risk category: Low; KYC complete (Aadhaar + PAN + Form 60); account open 4 years.

**Signal trigger:** The system flagged this account because a NEFT received from counterparty
account ACCT-NRI-001 shares a routing hop with an I4C-flagged mobile handle two degrees away.

**Alert period (credits over 45 days):**

| Day | Type | Amount | Counterparty | Explanation |
|---|---|---|---|---|
| T+1 | Credit (NEFT) | ₹1,22,000 | Employer-Corp-A | Monthly salary |
| T+14 | Credit (NEFT) | ₹3,50,000 | ACCT-NRI-001 | Brother's NRI account (Singapore) |
| T+28 | Credit (NEFT) | ₹1,20,500 | Employer-Corp-A | Monthly salary |
| T+30 | Debit (IMPS) | ₹3,47,000 | Loan-servicer-B | Home loan EMI payment |

Net: Credits ₹7,92,500; Debits ₹3,47,000.

**Customer-provided documentation:**
- ACCT-NRI-001: brother's ICICI NRI account statement showing source as Singapore savings
- Home loan sanction letter from Bank-B showing EMI schedule matching T+30 debit
- Form 15CA for inward remittance from Singapore (foreign tax compliance)

---

### 2. Reasoning Chain

```
POE-002 (Business Profile)
  → IT professional; salary-scale credit from known employer; 4-year relationship.
  → Transaction is consistent with profile. CLEAR.

POE-003 (Transaction History)
  → Prior 48 months: regular salary credits only. One-time large inward remittance from
    NRI sibling is a minor departure but entirely documented. CLEAR.

POE-005 (Income Level)
  → Combined salary + remittance = ₹4.7L over 30 days. ₹3.5L of that is the NRI transfer.
  → ₹3.5L from NRI sibling explained by Form 15CA and NRI account statement. NOT anomalous.

POE-006 (Source of Income)
  → NRI sibling remittance fully documented. Not an unknown source. CLEAR.

POE-007 (Beneficiary)
  → ₹3.47L debit goes to registered loan servicer, matching documented home loan.
    Not an I4C-flagged handle. CLEAR.

I4C Suspect Registry link (RFI-005)
  → The "link" is two hops through the routing network, not a direct counterparty flag.
  → Indirect routing association is not evidence of suspicious activity; the I4C flag
    is on a handle unrelated to this account's transactions.

Assessment: All 11 POE factors CLEAR or insufficient_data only on geography (no concern).
Recommendation: NOT FILE.
```

---

### 3. Expected Disposition

**Disposition: NOT_FILE**

The AI model may be anchored by the I4C signal and produce a high triggered count if it
over-weights the indirect routing association. The PO must exercise independent judgment:
the documentation fully explains the pattern.

**Confirmation-bias trap:** A system that FILES on every alert with an I4C indirect link
would over-file on legitimate NRI remittances — a known false-positive category. This
scenario tests whether the product correctly gates on the indirect-link vs. direct-counterparty
distinction.

**Not-filed rationale (mandatory in DECISION_LEDGER):**
Credits comprise salary (documented employer, consistent with KYC) and a single NRI transfer
from customer's sibling (Form 15CA, NRI account statement, and home loan confirmation
evidence on file). The I4C association is indirect (two routing hops) and does not touch
any of this account's direct counterparties. No genuine suspicion is established.

---

### 4. Human Review

**Reviewer:** [PO identity withheld]
**Review notes:** Classic over-triggering case. The routing-hop I4C linkage is system noise.
The customer's documents are strong. NOT_FILE with detailed rationale recorded.

---

### 5. Eval Harness Configuration

```yaml
eval_id: "SCN-17"
failure_mode: "confirmation_bias"
expected_recommendation: "NOT_FILE"
expected_assessment_pattern:
  triggered_count_max: 1
  must_be_clear: ["POE-002", "POE-003", "POE-006", "POE-007"]
hard_gate_irrelevant: false
```
