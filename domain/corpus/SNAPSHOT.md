# Regulatory Corpus — Snapshot Metadata
**Version:** 1.0.0
**Snapshot date:** 2026-10-29 (sources re-verified; first snapshot 2026-09-11)
**Corpus maintainer:** Nikhil Pande
**Product:** FIU-IND AML Decision-Defensibility Copilot
**Hackathon:** Nebius × NVIDIA Global AI Hackathon 2026 (build window Sep–Oct 2026)

---

## Status summary

| File | Entries | PROVEN | ASSUMED | NEEDS-VERIFICATION |
|---|---|---|---|---|
| rules/01-str-reporting-obligations.yaml | 6 | 5 | 1 | 0 |
| rules/02-ctr-reporting-obligations.yaml | 3 | 2 | 1 | 0 |
| rules/03-other-report-types.yaml | 3 | 3 | 0 | 0 |
| rules/04-record-retention.yaml | 2 | 1 | 0 | 1 |
| rules/05-finnet-str-structure.yaml | 16 | 4 | 11 | 1 |
| rules/06-red-flag-indicators.yaml | 10 | 0 | 1 | 9 |
| rules/07-inspection-focus.yaml | 4 | 1 | 2 | 1 |
| rules/08-statutory-basis.yaml | 5 | 3 | 1 | 1 |
| **TOTAL** | **49** | **17** | **21** | **11** |

---

## Corpus coverage declaration

This corpus covers:
- [x] FINnet / FINGate 2.0 STR 3-part structure
- [x] STR filing trigger, deadline, monetary threshold, tipping-off
- [x] CTR threshold and deadline
- [x] CCR, NTR, CBTR (thresholds sourced to PML Rules 3(1)(E) and 3(1)(BA), 2026-10-29; NPO definition open)
- [x] Record retention obligations
- [x] PO suspicion-evaluation factors (11 factors)
- [x] FIU-IND red-flag indicators (10 patterns — 9 NEEDS-VERIFICATION, RFI-009 ASSUMED; need mapping to exact FIU-IND typology doc)
- [x] FIU-IND inspection focus areas (4 areas)
- [x] Statutory basis quick reference

Not yet in corpus:
- [ ] FINGate 2.0 portal technical field-by-field mapping (requires direct FINGate access)
- [ ] Exact alert-to-STR ratio benchmarks used in inspections
- [ ] DPIP / MuleHunter.AI integration technical specs
- [ ] RBI Master Direction on KYC — field-level detail

---

## Disclaimer

> **This corpus is a DATED SNAPSHOT as of 2026-10-29. It is a research reference for
> product development, not legal or regulatory authority. Every entry marked
> NEEDS-VERIFICATION must be confirmed against the current live primary source before
> use in any compliance output. Regulatory requirements change; this file does not
> update automatically.**

---

## Change log

- **2026-10-29 — source review (approved by the human).** 46 of 49 entries now point to primary
  documents fetched and read on 2026-10-29: the PMLA and PML Rules texts, FIU-IND FAQs, the
  Reporting Format Guide v2.2 and Reporting Format Introduction v1.14, the FINGate 2.0 manual, the
  RBI KYC Master Direction and FIU-IND compliance orders. Thresholds and deadlines are now cited to
  the PML Rules (Rules 3 and 8). SB-003 and STR-004 corrected: tipping-off rests on Rule 8(6) and
  PMLA s.12(2), not s.12A. RR-001 section corrected to s.12(3). POE factors relabelled
  product-compiled (no FIU-IND list found). Evidence levels unchanged; counts above unchanged.

- **2026-10-29 — promotions (approved by the human).** CBTR-001 NEEDS-VERIFICATION → PROVEN and
  NTR-001 ASSUMED → PROVEN (rule text aligned to PML Rules 3(1)(E) / 3(1)(BA) and 8(1)); RFI-009
  NEEDS-VERIFICATION → ASSUMED (PEP due diligence in the RBI KYC MD). Counts: 17 / 21 / 11.

## Verification queue

See `GAPS.md` for the full gap list. Priority verifications:

1. All `url_verified: false` entries — confirm each URL is live
2. `RFI-001` through `RFI-010` — map each to the exact FIU-IND typology document
3. Alert-to-STR ratio benchmarks (DG-04) — locate primary inspection report
4. CBTR exact threshold (DG-01)
5. PMLA exact in-force date
