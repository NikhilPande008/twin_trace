# Scenario Library — Index
**Version:** 1.0
**Phase:** 1 — Domain Gold Standard
**Status:** 15 scenarios FINAL (reviewed and corrected 2026-09-12)
**Last updated:** 2026-09-12

---

## Coverage matrix

| # | File | Title | Disposition | Key RFIs | Key POE factors | Special rule tested |
|---|---|---|---|---|---|---|
| 00 | 00-schema-example.md | Schema example | CONTESTED | RFI-001, RFI-005 | 2, 4, 6 | Schema illustration only |
| 01 | 01-salaried-mule-passthrough.md | Salaried mule pass-through + I4C signal | **FILE** | RFI-001, RFI-005 | 2, 4, 6 | Core pass-through + flagged counterparty |
| 02 | 02-cash-structuring-linked-accounts.md | Cash structuring across 3 linked savings accounts | **FILE** | RFI-002 | 2, 4, 8, 9 | CTR-threshold structuring + dual obligation |
| 03 | 03-dormant-account-reactivation.md | Dormant retiree account → ₹85L cash | **CONTESTED** | RFI-003 | 2, 4, 5, 11 | Documentation-gap decision tree |
| 04 | 04-pep-corporate-credits.md | State PWD officer receives ₹47.7L from contractors | **FILE** | RFI-009, RFI-006 | 1, 4, 5 | PEP EDD + regulatory sector conflict |
| 05 | 05-cross-border-fatf-jurisdiction.md | IT exporter routes SWIFT via DPRK-linked correspondent to UAE free-zone entity | **FILE** | RFI-008 | 1, 5, 10 | CBTR + DPRK correspondent chain; UAE NOT grey-listed (June 2024) |
| 06 | 06-npo-cash-redistribution.md | NGO collects ₹19.5L cash → immediate UPI redistribution | **FILE** | RFI-010 | 1, 5, 6, 7 | NTR + CTR + STR triple obligation |
| 07 | 07-seasonal-agri-trader.md | Kharif season cash deposits — documented seasonal pattern | **CLOSE-NO-FILE** | — | 1, 2, 4, 8 | Documented innocent alternative; not every CTR warrants STR |
| 08 | 08-property-sale-proceeds.md | ₹75L credit from law firm — registered sale + Form 16B | **CLOSE-NO-FILE** | — | 2, 4, 5 | Primary-source documentation fully explains transaction |
| 09 | 09-same-device-network-mule.md | 7 accounts sharing one device fingerprint | **FILE** | RFI-004, RFI-001 | 2, 4, 10, 11 | Device identity linkage (highly anomalous, not impossible); cross-account suspicion |
| 10 | 10-beneficiary-concentration.md | 5 unrelated accounts → same UPI handle (I4C flagged) | **FILE** | RFI-007, RFI-001, RFI-005 | 2, 5, 9 | Cross-account layering; beneficiary concentration |
| 11 | 11-salary-account-consulting-income.md | Salary account + ₹4L/month undisclosed "consulting fees" | **CONTESTED** | RFI-006 | 1, 4, 5, 11 | KYC update as intermediate step; DEFERRED disposition state |
| 12 | 12-attempted-swift-blocked.md | Two blocked SWIFT attempts; second re-routes to same beneficiary | **FILE** | RFI-008 | 1, 4, 10 | STR-003 attempted transactions; re-routing as amplifier |
| 13 | 13-liquid-mf-layering.md | ₹1.2Cr cycled through liquid MF with 3–5 day holding | **CONTESTED** | RFI-001 (adapted) | 2, 4, 5, 9 | MF-as-layering-step; no economic rationale |
| 14 | 14-kyc-mismatch-nri-remittances.md | ₹30.9L Singapore remittances; unreachable customer; stale KYC | **CONTESTED** | RFI-006 | 2, 4, 5, 10, 11 | KYC staleness as suspicion modifier |
| 15 | 15-cooperative-society-officer.md | Coop society Treasurer diverts maintenance to personal account | **FILE** | RFI-001, RFI-006 | 1, 2, 4, 6 | Fiduciary-diversion; timing-pattern evidence; PMLA predicate |

---

## Disposition summary

| Disposition | Count | Scenario IDs |
|---|---|---|
| FILE | 9 | 01, 02, 04, 05, 06, 09, 10, 12, 15 |
| CLOSE-NO-FILE | 2 | 07, 08 |
| CONTESTED | 4 | 03, 11, 13, 14 |
| **Total** | **15** | |

---

## RFI coverage

| RFI | Covered in scenarios |
|---|---|
| RFI-001 (pass-through) | 01, 02, 09, 10, 13, 15 |
| RFI-002 (structuring) | 02 |
| RFI-003 (dormant reactivation) | 03 |
| RFI-004 (same device / identity linkage) | 09 |
| RFI-005 (flagged counterparty) | 01, 10 |
| RFI-006 (salary/income inconsistency) | 04, 11, 14, 15 |
| RFI-007 (beneficiary concentration) | 10 |
| RFI-008 (FATF geography) | 05, 12 |
| RFI-009 (PEP inconsistency) | 04 |
| RFI-010 (NPO misuse) | 06 |

All 10 RFIs covered at least once.

---

## POE factor coverage

| Factor | Covered in scenarios |
|---|---|
| POE-002 (Factor 1 — Business profile) | 04, 05, 06, 07, 11, 12, 15 |
| POE-003 (Factor 2 — Transaction history) | 01, 02, 03, 07, 08, 09, 10, 14, 15 |
| POE-005 (Factor 4 — Income level) | 01, 02, 03, 04, 07, 08, 09, 11, 13, 14, 15 |
| POE-006 (Factor 5 — Source of income) | 03, 04, 05, 08, 10, 11, 13, 14 |
| POE-007 (Factor 6 — Beneficiary) | 01, 06, 15 |
| POE-008 (Factor 7 — Transaction frequency) | 06 |
| POE-009 (Factor 8 — Transaction size) | 02, 07 |
| POE-010 (Factor 9 — Transaction complexity) | 02, 10, 13 |
| POE-011 (Factor 10 — Geographies) | 05, 09, 12, 14 |
| POE-012 (Factor 11 — KYC availability) | 03, 09, 11, 14 |

All 11 POE factors (POE-002 through POE-012) covered. Note: POE-004 (Customer Risk Profile, Factor 3) is not directly cited in any scenario — it is implicit in risk-category assessments but not foregrounded as a suspicion basis.

---

## Corpus rules tested

| Rule | Scenarios |
|---|---|
| STR-001 (trigger: suspicion not amount) | 07, 08 (CLOSE-NO-FILE validates the rule by showing what doesn't trigger it) |
| STR-002 (7 WD deadline) | 03, 11, 14 (deadline pressure in DEFERRED scenarios) |
| STR-003 (attempted transactions) | 12 |
| CTR-001 / CTR-003 (CTR + dual obligation) | 02, 06 |
| NTR-001 | 06 |
| CBTR-001 | 05 |
| INS-001 (not-filed rationale) | 07, 08 (CLOSE-NO-FILE closure rationale quality) |
| INS-002 (authorised staff / SLA) | 01, 09, 12 |
| INS-003 (alert-to-STR ratio) | 07 (closing a legitimate alert is the healthy ratio contribution) |
| INS-004 (templated STR quality) | All FILE scenarios (each GoS is non-templated) |
| SB-002 (PMLA s.12(1)(b)) | All FILE scenarios |
| SB-003 (tipping off) | 01, 04 |

---

## Review workflow

1. Nikhil reviews each scenario against their domain knowledge
2. Mark `status: reviewed` on scenarios that pass without changes
3. Mark `status: corrected` on scenarios requiring factual corrections; document changes in `correction_notes`
4. If a general rule is derived from a correction, add it to `domain_rule_extracted` and update the relevant corpus YAML entry
5. Mark `status: FINAL` once the scenario is approved for use in product evaluation
6. CONTESTED scenarios: the human PO makes a disposition choice and records it in the Human Review block
