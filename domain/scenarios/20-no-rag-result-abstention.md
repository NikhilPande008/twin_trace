---
id: "20"
title: "No-RAG-result abstention — query returns zero corpus results"
status: FINAL
disposition: CONTESTED
rules_cited: []
failure_mode: no_rag_result
---

### 1. Scenario Description

This scenario tests the product's behaviour when a regulatory query returns **zero corpus
results** — from the BM25 corpus index or keyword fallback.

**Trigger condition:** A PO asks a regulatory question about a topic not covered in the
current corpus (PROVEN=15, ASSUMED=21 rows, snapshot 2026-09-17).

**Example query that triggers zero results:**
> "What are the PMLA obligations for virtual asset service providers (VASPs)?"

The current corpus does not contain any VASP-specific rules. This is a valid regulatory
perimeter gap — VASPs were brought under PMLA in 2023 but the corpus has not been
extended to cover them.

---

### 2. Expected Product Behaviour

**Must do:**
1. Return an empty results set (zero rules)
2. Display a message indicating no corpus results were found
3. State explicitly: "No matching rules found in the current corpus snapshot (2026-09-17).
   This may indicate a regulatory-perimeter gap. Do not proceed on the assumption that
   the absence of a corpus rule means no obligation exists."
4. Suggest the PO consult the primary source (FIU-IND / IndiaCode / RBI website)

**Must NOT do:**
1. Hallucinate a corpus rule that does not exist
2. Assert "no obligation applies" because no rule was returned
3. Return a NEEDS-VERIFICATION rule as a substitute (NV rules are excluded)

---

### 3. Disposition

**Disposition: CONTESTED** — the alert itself may be valid, but the product cannot provide
regulatory guidance for VASP-specific obligations. The PO must escalate to specialist
compliance counsel.

---

### 4. Human Review

**Reviewer:** [PO identity withheld]
**Review notes:** Zero corpus results is not "no obligation." This case needs specialist input.

---

### 5. Eval Harness Configuration

```yaml
eval_id: "SCN-20"
failure_mode: "no_rag_result"
trigger_query: "What are the PMLA obligations for virtual asset service providers?"
expected_result_count: 0
expected_behaviour:
  must_not_hallucinate_rule: true
  must_not_assert_no_obligation: true
  must_display_empty_result_message: true
  must_suggest_primary_source: true
```
