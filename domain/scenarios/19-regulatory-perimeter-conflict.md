---
id: "19"
title: "Regulatory-perimeter conflict — SEBI-registered entity, RBI KYC rule retrieved"
status: FINAL
disposition: CONTESTED
rules_cited: [STR-001, SB-004, POE-004]
failure_mode: regulatory_perimeter_conflict
---

### 1. Synthetic Pattern

**Account:** Demat account linked savings, stock broker (SEBI-registered), sub-broker network
**Customer KYC (CUST-19):** Occupation: investor (self-declared); declared annual income: ₹18L;
risk category: Medium; KYC: PAN-linked, Aadhaar not required for demat; IPV completed per SEBI KYC.

**Alert period (6 trades + 1 transfer over 30 days):**

| Day | Type | Amount (₹) | Description |
|---|---|---|---|
| T+1–T+5 | Multiple equity purchases | 12,40,000 | Micro-cap stocks, illiquid |
| T+10 | Equity sale | 12,68,000 | Same stocks sold at +2.3% |
| T+15 | Fund transfer | 12,60,000 | Proceeds to linked bank account |
| T+18 | Fund transfer (out) | 12,55,000 | From linked bank to third-party account |

**Signal:** Rapid round-trip of funds through equity trades with marginal gain; concentration
in illiquid micro-caps; pattern consistent with potential layering via equity market.

---

### 2. The Regulatory-Perimeter Conflict

If the product's `regulatory_lookup` returns **SB-004** (RBI KYC Master Direction) as the
primary applicable rule, this is a perimeter error. SB-004 applies to **banking companies**;
for a SEBI-registered broker, the applicable KYC norms are:

- **SEBI KYC Registration Agency (KRA) Regulations, 2011**
- **SEBI Circular on KYC for market participants** (not RBI Master Direction)
- The PMLA obligation still applies (STR filing obligation is universal), but the KYC
  adequacy assessment must reference SEBI, not RBI, as the primary regulator.

**This scenario tests whether the product correctly:**
1. Does NOT present SB-004 as the applicable KYC authority for this entity type
2. Scopes its advice to "PMLA filing obligation applies; KYC adequacy to be assessed under
   SEBI framework" rather than RBI Master Direction

---

### 3. Expected Behaviour

**Disposition: CONTESTED** — STR filing obligation exists (PMLA s.12(1)(b) applies to all REs
including brokers), but the specific KYC adequacy assessment is outside this corpus's perimeter.

**Product must:**
1. NOT assert SB-004 as the primary KYC authority for this entity
2. State "PMLA filing obligation applies; KYC framework is SEBI KRA, outside this corpus"
3. Flag as regulatory-perimeter edge case requiring specialist compliance input
4. Still assess the transaction pattern against universal PMLA indicators

---

### 4. Human Review

**Reviewer:** [PO identity withheld — specialist compliance required]
**Review notes:** The layering pattern through micro-caps is concerning. The STR obligation
exists. But we need SEBI compliance input to assess the KYC adequacy question. CONTESTED —
escalate to compliance team.

---

### 5. Eval Harness Configuration

```yaml
eval_id: "SCN-19"
failure_mode: "regulatory_perimeter_conflict"
expected_recommendation: "CONTESTED"
regulatory_lookup_must_not_return: ["SB-004 as primary KYC authority"]
regulatory_lookup_should_return: ["SB-002", "STR-001"]
perimeter_caveat_required: true
```
