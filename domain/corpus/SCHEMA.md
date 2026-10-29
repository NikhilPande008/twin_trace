# Regulatory Corpus — Schema Specification
**Version:** 1.0
**Snapshot date:** 2026-09-11
**Corpus maintainer:** Nikhil Pande

---

## Design principles

1. **Every fact carries a source or it doesn't go in.** No assertion without `primary_source`.
2. **Dated snapshot, not live authority.** All entries carry `snapshot_date`. A stale regulatory fact presented as current is a liability.
3. **Claim-audit discipline.** Every entry is tagged `evidence_level`: `PROVEN` / `ASSUMED` / `NEEDS-VERIFICATION`. See definitions below.
4. **Synthesis ≠ source.** `my_synthesis` is the builder's PO-lens interpretation; `rule` is the raw regulatory statement. They are distinct fields and must never be conflated.
5. **Version-controlled and portable.** YAML files, one per domain area, git-tracked. JSON export for downstream use.

---

## Field specification

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | ✓ | Unique rule ID. Format: `{CATEGORY_PREFIX}-{NNN}`. E.g. `STR-001`, `RFI-001`, `INS-001`. Immutable once assigned. |
| `rule` | string | ✓ | The regulatory fact/rule, stated as precisely as the source allows. Quote verbatim where feasible. |
| `category` | enum | ✓ | Top-level domain area. See Categories table below. |
| `subcategory` | string | ✗ | Finer-grain classification within category. Free text. |
| `applies_to` | list[enum] | ✓ | Which Reporting Entity (RE) types this rule applies to. |
| `primary_source.document` | string | ✓ | Full document name + version/date. E.g. `"PMLA 2002, Section 12(1)(b)"`. |
| `primary_source.url` | string | ✓ | URL to the source. May be a base page URL if a direct-section URL is unavailable. Never invented. |
| `primary_source.url_verified` | bool | ✓ | `true` **only** when the URL has been manually confirmed live and pointing to the right document. Default `false`. |
| `primary_source.section` | string | ✗ | Section / clause / paragraph reference within the document. |
| `primary_source.accessed_date` | date | ✗ | ISO 8601 date the URL was last accessed and confirmed. Null = not yet accessed. |
| `effective_date` | date\|null | ✓ | Date the rule came into force. ISO 8601. Use `null` if unknown — do NOT guess. |
| `evidence_level` | enum | ✓ | `PROVEN` / `ASSUMED` / `NEEDS-VERIFICATION`. |
| `my_synthesis` | string | ✗ | The PO-lens interpretation of this rule for disposition decisions. Not a source. |
| `last_verified` | date\|null | ✗ | Date this entry was last checked against the primary source. Null = never verified by a person. |
| `snapshot_date` | date | ✓ | "As of" date. Set when entry is created or updated. ISO 8601. |
| `gap_notes` | string | ✗ | Open questions, uncertainty, or verification tasks specific to this entry. |
| `related_rules` | list[string] | ✗ | IDs of related corpus entries. |

---

## Categories (enum)

| Value | ID prefix | Description |
|---|---|---|
| `REPORTING_OBLIGATION` | `STR-`, `CTR-`, `CCR-`, `NTR-`, `CBTR-` | When and how to file each report type |
| `REPORT_STRUCTURE` | `RS-` | The schema/format fields of a specific report type |
| `PO_EVALUATION` | `POE-` | The PO's suspicion-evaluation framework and factors |
| `RED_FLAG_INDICATOR` | `RFI-` | Specific transaction patterns that trigger or support suspicion |
| `INSPECTION_FOCUS` | `INS-` | Areas FIU-IND inspectors scrutinise during on-site inspections |
| `STATUTORY_BASIS` | `SB-` | PMLA / RBI / FATF statutory references |
| `RECORD_RETENTION` | `RR-` | How long and in what form records must be retained |
| `TIPPING_OFF` | `TO-` | Tipping-off prohibition (PML Rules 2005 Rule 8(6); PMLA s.12(2)) |
| `MULE_ACCOUNT_CONTEXT` | `MAC-` | Regulatory context around mule accounts; secondary sources only |

---

## Applies-to values (enum)

| Value | Description |
|---|---|
| `all_reporting_entities` | All REs defined under PMLA Schedule (broadest scope) |
| `banking_companies` | Scheduled commercial banks, cooperative banks, payments banks, SFBs |
| `financial_institutions` | NBFCs, HFCs, and other financial institutions |
| `intermediaries` | SEBI-registered market intermediaries |
| `insurance_companies` | Insurers and insurance intermediaries |
| `payment_system_operators` | Prepaid instrument issuers, payment aggregators, payment gateways |

---

## Evidence levels

| Level | Meaning | Usage rule |
|---|---|---|
| `PROVEN` | The rule is stated in the cited primary source with high fidelity; the URL is expected to be confirmable (even if `url_verified` is still false until manually checked). The underlying regulatory fact is not in dispute. | Safe to surface in generated output as a citation, subject to the `url_verified` caveat. |
| `ASSUMED` | The rule is widely accepted in the domain and consistent with the cited source but has not been independently verified against the current live document text. | Surface in output with caveat; prioritise for verification before product v1. |
| `NEEDS-VERIFICATION` | Believed to be correct but flagged as having a material risk of being outdated, misremembered, or with an incomplete source reference. | **Do NOT surface in generated output without an explicit disclaimer.** Treat as a gap. Add to GAPS.md. |

---

## Versioning conventions

- Each YAML file is a domain-area document. Git tracks per-line changes across versions.
- When a rule changes (regulatory amendment), do NOT edit the `rule` field in place — add a note in `gap_notes`, update `effective_date` and `last_verified`, and update `snapshot_date`.
- If a rule is superseded, add a `superseded_by` field pointing to the new rule ID.
- The `snapshot_date` on every entry is the "as of" date for that entry's contents. A corpus entry with `snapshot_date: 2026-09-11` was correct as of that date; it may be stale at a later date.

---

---

## Example entry

```yaml
id: STR-001
rule: >
  A Reporting Entity must file a Suspicious Transaction Report with FIU-IND whenever
  a transaction gives rise to reasonable grounds of suspicion that it involves proceeds
  of an offence or is related to money laundering or terrorist financing, regardless
  of the amount involved.
category: REPORTING_OBLIGATION
subcategory: STR_TRIGGER
applies_to:
  - all_reporting_entities
primary_source:
  document: "Prevention of Money-Laundering Act, 2002 — Section 12(1)(b)"
  url: "https://www.indiacode.nic.in/handle/123456789/2205"
  url_verified: false
  section: "Section 12(1)(b)"
  accessed_date: null
effective_date: null   # PMLA in-force date — NEEDS-VERIFICATION
evidence_level: PROVEN
my_synthesis: >
  The STR trigger is suspicion, not amount. A PO who declines to file
  because "the amount is small" is non-compliant. This is the single most
  fundamental rule in the AML regime.
last_verified: null
snapshot_date: "2026-09-11"
gap_notes: "Verify exact PMLA in-force date; confirm India Code URL is live."
related_rules:
  - STR-002
  - STR-003
```
