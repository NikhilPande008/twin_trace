# Regulatory Corpus — Gap List
**As of:** 2026-09-17
**Rule:** Never remove a gap without a primary-source verification. Promote the
corpus entry from `NEEDS-VERIFICATION` → `ASSUMED` → `PROVEN` as verification proceeds.

---

## Priority tiers

| Tier | Criteria | Product impact |
|---|---|---|
| P0 | Product surfaces this fact in generated output; wrong value = wrong compliance advice | Do not use in product until resolved |
| P1 | Product references this in UI/dashboard; wrong value = bad UX but not harmful advice | Use with explicit disclaimer |
| P2 | Contextual / background; wrong value has low direct user impact | Note as approximate |

---

## Active gaps

| Gap ID | Description | Tier | Corpus entries affected | Status |
|---|---|---|---|---|
| DG-01 | **CBTR threshold.** The ₹5 lakh per-transaction figure may have been revised in a 2024–2026 FIU-IND circular. The correct threshold may be different. | P0 | CBTR-001 | UNVERIFIED |
| DG-02 | **STR-related records retention.** Whether STR records must be retained beyond the 5-year PMLA floor (the 10-year figure cited in some guidance) needs statutory confirmation. | P2 | RR-002 | UNVERIFIED |
| DG-03 | **FINGate 2.0 mandatory field configuration.** FIU-IND reportedly configures mandatory fields per RE based on report-quality history. The exact mechanism is not confirmed. | P1 | STR-006 | UNVERIFIED |
| DG-04 | **Alert-to-STR ratio benchmarks.** Whether FIU-IND publishes specific ratio ranges used in inspections, or evaluates contextually, needs primary-source confirmation. | P0 | INS-003 | UNVERIFIED |
| DG-05 | **SC mule SOP directive (Aug 2026).** Supreme Court allegedly directed RBI to circulate a mule-account SOP. Exact date and order text unverified. | P2 | MAC-001 (to be added) | UNVERIFIED |
| DG-06 | **MHA MuleHunter integration mandate.** The Dec 2026 deadline for banks to integrate MuleHunter.AI is cited from media reports. Exact MHA circular unlocated. | P2 | MAC-002 (to be added) | UNVERIFIED |
| DG-07 | **FIU-IND red-flag indicator list (exact document + version).** RFI-001 through RFI-010 are industry-standard AML patterns, but the exact FIU-IND typology report(s) that enumerate them need to be identified. | P0 | RFI-001 through RFI-010 | UNVERIFIED |
| DG-08 | **FIU-IND inspection SLA for PO decisions.** Whether the 7-working-day STR deadline is also the inspection benchmark for "within SLA" decisions needs primary-source confirmation. | P1 | INS-002 | UNVERIFIED |
| DG-09 | **Templated-narrative checklist — primary source.** The checklist in DOMAIN.md and the INS-004 entry is synthesised from domain knowledge. A verbatim FIU-IND citation (annual report, quality feedback circular) would be stronger. | P0 | INS-004 | UNVERIFIED |
| DG-10 | **DPIP and MuleHunter.AI current operational status.** Whether these systems are live and accepting bank connections as of Sep 2026 needs confirmation. | P1 | RFI-004, RFI-005 | SECONDARY only |
| DG-11 | **PMLA 2002 exact in-force date.** The Act received Presidential assent in Jan 2003; the exact date it came into force (often cited as July 2005 or January 2006) needs to be confirmed. | P2 | SB-001, SB-002, STR-001, STR-004, RR-001 | UNVERIFIED |
| DG-12 | **FINGate 2.0 portal URL and field list.** The exact URL of the FINGate 2.0 portal (is it fingateservices.in? a fiuindia.gov.in subdomain?) and the complete field mapping for each report type. | P1 | STR-006, RS-001, RS-002, RS-003, RS-004 | UNVERIFIED |
| DG-13 | **FIU-IND not-filed rationale requirement — primary citation.** A specific FIU-IND inspection circular or annual report that explicitly states the requirement to document not-file rationales. | P0 | INS-001 | UNVERIFIED |
| DG-14 | **URL verification — all corpus entries.** Every `url_verified: false` entry across all 8 rule files. None have been manually confirmed live. | P1 | All entries | UNVERIFIED |
| DG-15 | **CCR deadline.** Whether CCR is filed on the same 15-day monthly cycle as CTR, or is event-triggered, is not specified in the current corpus. | P1 | CCR-001 | UNVERIFIED |
| DG-16 | **NTR exact threshold and NPO definition.** The rupee amount and/or frequency criteria that trigger NTR filing, and the exact definition of "NPO" in PMLA context. | P0 | NTR-001 | UNVERIFIED |
| DG-17 | **RBI KYC Master Direction current version.** The URL `rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=11566` may not point to the latest consolidated version. Verify current amendment date. | P1 | SB-004, POE-012, RFI-009 | UNVERIFIED |
| DG-18 | **2023 PMLA amendment impact.** The Prevention of Money-Laundering (Amendment) Act 2023 made changes to the definition of proceeds of crime and RE scope. The exact changes and effective dates need to be mapped. | P1 | SB-001, SB-002 | UNVERIFIED |
| DG-19 | **POE-001 "11-factor list" primary source.** Whether the FIU-IND Reporting Format Guide v2.2 enumerates exactly 11 suspicion-evaluation factors verbatim, or whether the product's framework is a synthesis from multiple guidance documents. Until confirmed, the UI must label this as a "product-compiled structured assessment framework" and must NOT claim it is a mandated FIU-IND list. | P0 | POE-001, suspicion_evaluator prompt | UNVERIFIED |

---

## Resolved gaps

*(None yet — this corpus is at v1.0. Move entries here when primary-source verified.)*

---

## How to close a gap

1. Access the primary source URL (or locate the correct URL if the listed one is wrong)
2. Find the specific provision, section, or passage
3. Update the corpus YAML entry:
   - Change `evidence_level` to `ASSUMED` or `PROVEN` as appropriate
   - Set `primary_source.url` to the verified URL
   - Set `primary_source.url_verified: true`
   - Set `primary_source.accessed_date` to today's date
   - Set `last_verified` to today's date
   - Clear or update `gap_notes`
   - Update `snapshot_date` to today's date
4. Move the gap ID from Active to Resolved in this file, noting the resolution date and source
5. Update `SNAPSHOT.md` to adjust the PROVEN/ASSUMED/NEEDS-VERIFICATION counts
