---
id: "21"
title: "Conflicting transaction evidence — partial documentation, borderline case"
status: FINAL
disposition: CONTESTED
rules_cited: [STR-001, STR-002, POE-002, POE-005, POE-006, POE-012, INS-001]
failure_mode: conflicting_evidence
---

### 1. Synthetic Pattern

**Account:** Current account, private sector bank, semi-urban branch
**Customer KYC (CUST-21):** Occupation: freelance consultant (IT); declared annual income: ₹12L;
risk category: Medium; KYC: PAN-linked, Aadhaar verified, address re-verified 14 months ago.

**Alert period (credits over 60 days):**

| Day | Type | Amount (₹) | Counterparty | Documentation |
|---|---|---|---|---|
| T+1 | Credit (NEFT) | 4,50,000 | TechCorp-A (Pune) | Invoice on file (Invoice #TCA-2026-089) |
| T+12 | Credit (NEFT) | 3,80,000 | TechCorp-B (Bengaluru) | Invoice on file (Invoice #TCB-2026-033) |
| T+24 | Credit (NEFT) | 2,90,000 | PersonalX (not a company) | No documentation |
| T+35 | Credit (NEFT) | 5,60,000 | TechCorp-A | Invoice claims services not matching prior contract scope |
| T+48 | Credit (NEFT) | 3,10,000 | Consulting-LLC-Q | LLC registered 2 weeks before credit; principal=PersonalX |
| T+55 | Debit (RTGS) | 8,50,000 | Property-Reg-Office | Declared: property purchase deposit |

**Pattern analysis:**
- T+1, T+12: Clean invoiced income, consistent with declared IT consulting work
- T+24: ₹2.9L from individual with no documented relationship to any known client
- T+35: ₹5.6L from TechCorp-A but for "scope not matching prior engagement" per invoice review
- T+48: ₹3.1L from 2-week-old LLC whose principal is the same as the T+24 individual
- T+55: ₹8.5L debit to property registration — registered sale not confirmed on file

**Total credits over 60 days: ₹19,90,000** (~1.66× annual declared income in 60 days)
Ratio of documented:undocumented = 8,30,000:11,60,000 (58% of credits not adequately documented)

---

### 2. Reasoning Chain

```
Evidence supporting suspicion (FILE indicators):
  → T+24 credit from unknown individual (POE-006 — source of income) — NO documentation
  → T+48 credit from 2-week-old LLC (PersonalX front) — structuring indicator
  → Invoice scope mismatch on T+35 credit from TechCorp-A — invoice may be fabricated
  → T+55 property debit: possible placement (layering funds into property)

Evidence against suspicion (mitigating):
  → T+1 and T+12 credits are clean, properly invoiced, consistent with declared occupation
  → Customer is a known IT freelancer — large irregular income is plausible in this sector
  → Property purchase is a documented use of funds (if sale deed can be obtained)
  → Credit volume over 60 days (₹20L) is high but not extreme for an IT consultant

Assessment: POE-002, POE-005 partially clear; POE-006, POE-010 triggered; POE-012 clear.
Evidence is conflicting — not a clean FILE or NOT_FILE.
```

---

### 3. Expected Disposition

**Disposition: CONTESTED**

The product must:
1. Flag the conflicting evidence in the assessment
2. NOT produce a blanket FILE recommendation given clean credits are mixed with suspicious ones
3. Request additional documentation before advising disposition:
   - Source of T+24 ₹2.9L from PersonalX
   - Full corporate registration and ownership of Consulting-LLC-Q
   - Property sale deed confirming T+55 debit
   - Explanation of scope change in T+35 TechCorp-A invoice

**Not-filed rationale (if NOT_FILE chosen):** Would require documented resolution of all four gaps above.

---

### 4. Human Review

**Reviewer:** [PO identity withheld]
**Review notes:** This is a genuinely borderline case. Two clean invoiced credits, two suspect
credits, one structure through a fresh LLC, and a property purchase. Escalate for additional
documentation request before deciding.

---

### 5. Eval Harness Configuration

```yaml
eval_id: "SCN-21"
failure_mode: "conflicting_evidence"
expected_recommendation: "CONTESTED"
expected_triggered_factors: ["POE-006", "POE-010"]
expected_clear_factors: ["POE-002", "POE-012"]
must_request_documentation: true
must_not_produce_clean_gos: true
```
