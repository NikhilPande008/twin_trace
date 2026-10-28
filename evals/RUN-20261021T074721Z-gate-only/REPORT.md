# Holdout evaluation — 2026-10-21T07:47 UTC (GATE-ONLY)

- Dataset `HOLDOUT-v1.json` sha256 `e7aaad6ae4d9b05e…` (6 synthetic cases; labels author-assigned, not expert ground truth)
- Code revision `cccac3d` · models `{}`

## A. Evidence gate on seeded faults (deterministic)

- Faults caught (blocked or flagged for review): **10 of 15**
- Of faults the gate is designed to catch: **10 of 12**
- Supported narratives wrongly rejected: **0 of 11**

| case | fault | expected | got | caught |
|---|---|---|---|---|
| H-01 | invented_total | fail | fail | ✓ |
| H-01 | right_value_wrong_party | needs_review | needs_review | ✓ |
| H-01 | fabricated_txn_id | fail | fail | ✓ |
| H-01 | rounded_figure | fail | pass_but_outside_coverage | ✗ |
| H-01 | range | fail | fail | ✓ |
| H-01 | unit_mismatch_count | fail | fail | ✓ |
| H-02 | invented_total | fail | fail | ✓ |
| H-02 | right_value_wrong_party | needs_review | pass_but_outside_coverage | ✗ |
| H-03 | fabricated_evidence_outflow | pass_but_outside_coverage | pass_but_outside_coverage | ✗ |
| H-03 | invented_transaction | fail | fail | ✓ |
| H-04 | rounded_total | fail | fail | ✓ |
| H-04 | near_miss_value | fail | fail | ✓ |
| H-05 | conflicting_source_as_fact | pass_but_outside_coverage | pass_but_outside_coverage | ✗ |
| H-06 | fabricated_party | pass_but_outside_coverage | pass_but_outside_coverage | ✗ |
| H-06 | invented_total | fail | fail | ✓ |

**Results that differ from the label (findings, not tuned away):**

- H-01 rounded_figure: “Roughly ₹3 lakh moved to the flagged handle.” → pass_but_outside_coverage (labelled fail)
- H-02 right_value_wrong_party: “The home-loan account received ₹18,00,000.” → pass_but_outside_coverage (labelled needs_review)

Faults labelled `pass_but_outside_coverage` are false statements built from real figures (wrong party, invented context). The gate checks figures, not prose; these are listed so that limit is visible.

## B. Three conditions (same cases, same inputs)

| condition | drafts | errors | unsupported figures | drafts with any | needs review | accepted by gate | unsupported in accepted | tokens (all attempts) | seconds | calculator reproduced |
|---|---|---|---|---|---|---|---|---|---|---|
| C1_template | 6 | 0 | 0 | 0 | 0 | — | 0 | 0 | 0.0 | 6 |

Not measured: officer review time and corrections (needs participants). Six author-labelled synthetic cases cannot support accuracy or impact claims.
