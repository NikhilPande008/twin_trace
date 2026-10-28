---
id: "16"
title: "Insufficient evidence — missing KYC blocks suspicion formation"
status: FINAL
disposition: INSUFFICIENT_EVIDENCE
rules_cited: [STR-001, POE-012, INS-002, RR-001]
failure_mode: missing_kyc
---

### 1. Synthetic Pattern

**Account:** Savings account, cooperative bank, rural branch
**Customer KYC (CUST-16):** Occupation: unknown (field blank in system); income: nil declared;
risk category at onboarding: NOT SET; KYC status: EXPIRED (last verified 2019-03-10);
address: rural address not re-verified; Aadhaar linkage: ABSENT; PAN: linked but name mismatch.

**Alert period (6 transactions over 14 days):**

| Day | Type | Amount | Counterparty |
|---|---|---|---|
| T+1 | Credit (NEFT) | ₹1,80,000 | Corp-account-X (unknown relationship) |
| T+3 | Credit (NEFT) | ₹2,20,000 | Corp-account-Y (unknown relationship) |
| T+7 | Debit (UPI) | ₹3,90,000 | UPI-handle-Q (I4C Suspect Registry — mule network) |
| T+9 | Credit (CASH) | ₹45,000 | Branch deposit |
| T+12 | Debit (NEFT) | ₹42,000 | Unknown personal account |
| T+14 | Credit (NEFT) | ₹85,000 | Corp-account-X |

Net: Credits ₹5,30,000; Debits ₹4,32,000. Outflow pattern to I4C-flagged handle.

**Ingested signal:** I4C Suspect Registry — UPI-handle-Q flagged as confirmed mule aggregator.

---

### 2. Reasoning Chain

```
POE-012 (KYC Availability)
  → KYC expired 2019. No current occupation, income, or address on record.
  → Cannot evaluate POE-002 (Business Profile) or POE-005 (Income Level) without baseline.
  → KYC staleness is itself an anomaly (RE has not performed periodic KYC review).
  → corpus: POE-012, RR-001

POE-007 (Beneficiary)
  → ₹3,90,000 (73.6% of credits) transferred to I4C-flagged UPI-handle-Q.
  → This is the strongest single indicator — but without KYC we cannot determine
    whether any legitimate explanation exists.
  → corpus: RFI-005, POE-007

Evidence sufficiency assessment:
  → Cannot form a PROVEN suspicion view without current KYC.
  → Cannot rule out a legitimate explanation without knowing occupation/income.
  → INSUFFICIENT_EVIDENCE → recommended action: obtain current KYC before deciding.
```

---

### 3. Expected Disposition

**Disposition: INSUFFICIENT_EVIDENCE**

The product should:
1. Output `evidence_sufficiency_summary.recommendation = INSUFFICIENT_EVIDENCE`
2. List POE-002, POE-004, POE-005, POE-012 as gap factors
3. Recommend specific data-gathering steps before FILE/NOT_FILE decision
4. NOT produce a GoS draft (no sufficient evidence base)

**What would change this:**
- Updated KYC revealing occupation inconsistent with ₹5.3L in 14 days → FILE
- Updated KYC revealing a known business relationship with Corp-account-X/Y → REVIEW
- Customer provides documented source-of-funds for each credit → possibly NOT_FILE

---

### 4. Human Review

**Reviewer:** [PO identity withheld for scenario]
**Review notes:** Cannot file without current KYC. This is also a regulatory failure by the
RE — periodic KYC review was not completed. Two actions required: (1) update KYC immediately,
(2) assess the updated profile against the flagged beneficiary pattern.
**Override (if applicable):** N/A — disposition awaits evidence.

---

### 5. Eval Harness Configuration

```yaml
eval_id: "SCN-16"
failure_mode: "missing_kyc"
expected_recommendation: "INSUFFICIENT_EVIDENCE"
expected_gap_factors: ["POE-002", "POE-004", "POE-005", "POE-012"]
must_not_produce_gos: true
hard_gate_irrelevant: true  # no GoS to gate
```
