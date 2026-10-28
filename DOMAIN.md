# DOMAIN.md — Indian AML / FIU-IND Regulatory Reference

**Maintenance rule:** Every domain assertion here carries a confidence tag:
- `[PRIMARY-SOURCED]` — directly verifiable against fiuindia.gov.in or the cited statutory text
- `[SECONDARY]` — from a reputable secondary source (RBI circular, FATF guidance, published legal commentary); cite it
- `[UNVERIFIED]` — believed to be correct but not yet verified against a primary source; DO NOT use in generated output without flagging
- `[SECONDARY—verify]` — believed correct but explicitly queued for primary-source confirmation; tracked as a gap in §9
- `[HUMAN]` — ruled by human domain review (analytic or workflow judgment), logged with date. A [HUMAN] ruling does NOT substitute for a primary source on citation-level facts — those remain `[SECONDARY—verify]` until sourced

**Never add a domain assertion without a tag. Never promote a tag without checking the source.**

---

## 1. Reporting Obligations under PMLA

### 1.1 Suspicious Transaction Report (STR)
- Filing trigger: suspicion, not threshold; includes attempted transactions `[PRIMARY-SOURCED — PMLA 2002 s.12; FIU-IND Reporting Format Guide v2.2]`
- Filing deadline: **7 working days** from the date of forming suspicion. Trigger = **suspicion-formation**, NOT the transaction date or the alert date; record both the alert timestamp and the suspicion-formed timestamp (the gap is inspectable). `[HUMAN — trigger principle, review 2026-09-18]` `[SECONDARY—verify — exact "7 working days" text in PML (Maintenance of Records) Rules; DG-20]`
- Monetary threshold: **none** — an STR must be filed whenever suspicion exists, regardless of amount `[PRIMARY-SOURCED — PMLA 2002 s.12(1)(b); FIU-IND FAQs]`
- Tipping-off: strictly prohibited — the subject must not be informed that an STR has been or may be filed. A source-of-funds enquiry under ongoing EDD is permissible and does NOT constitute tipping-off; what is prohibited is disclosing that a report is being made. `[HUMAN — EDD/tipping-off boundary, review 2026-09-18]` `[SECONDARY—verify — precise citation may be PMLA s.12(2)/s.12A(3) + PML Rules r.8(6) rather than s.12A alone; DG-22]`
- Attempted transactions: must be reported even if the transaction was not completed `[PRIMARY-SOURCED — FIU-IND Reporting Format Guide v2.2]`

### 1.2 Cash Transaction Report (CTR)
- Threshold: cash transactions exceeding **₹10 lakh** (individually or in aggregate for a month, including linked accounts) `[PRIMARY-SOURCED — FIU-IND Reporting Format Guide v2.2]` ⚠️ *Exact "integrally connected transactions" / monthly-aggregation wording `[SECONDARY—verify — DG-21]`*
- Filing deadline: **15th of the following month** `[PRIMARY-SOURCED — FIU-IND Reporting Format Guide v2.2]`

### 1.3 Other Report Types
- **CCR** (Counterfeit Currency Report): on detection of counterfeit currency `[PRIMARY-SOURCED — FIU-IND Reporting Format Guide v2.2]`
- **NTR** (Non-Profit Organisation Transaction Report): transactions involving NPOs above specified thresholds `[PRIMARY-SOURCED — FIU-IND Reporting Format Guide v2.2]`
- **CBTR** (Cross Border Wire Transfer Report): indicative threshold ₹5 lakh per transaction `[PRIMARY-SOURCED — FIU-IND Reporting Format Guide v2.2]` ⚠️ *Verify exact current threshold — may have been revised*
- Records retention: **5 years** from date of transaction (10 years for STR-related records) `[PRIMARY-SOURCED — PMLA 2002 s.12(1)(c)]` ⚠️ *Verify 10-year STR retention — [UNVERIFIED]*

---

## 2. FINGate 2.0 — The Live Reporting Portal

- FINGate 2.0 is the successor to FINnet; all RE reporting is now through this portal `[PRIMARY-SOURCED — fiuindia.gov.in]`
- FIU-IND configures mandatory fields per RE based on that RE's **report-quality history** — report quality is institutionally tracked and consequential (poor quality = more mandatory fields, additional scrutiny) `[PRIMARY-SOURCED — fiuindia.gov.in/FINGate documentation]` ⚠️ *Specific mechanism of field configuration needs verification*

### 2.1 STR Structure — FINGate 2.0 / FINnet Format
The STR has three mandatory parts (non-negotiable — mirrors FINGate schema):

| Part | Contents |
|---|---|
| (a) KYC Profile | Customer identification, PAN/Aadhaar linkage, address, occupation, risk category, relationship history |
| (b) Transaction Details | Account number(s), transaction dates/amounts/types, counterparty details, channel (branch/online/ATM) |
| (c) Ground of Suspicion | The PO's specific, non-templated narrative explaining WHY this transaction/pattern arouses suspicion |

`[PRIMARY-SOURCED — FINnet Reporting Format PDF; fiuindia.gov.in/files/Downloads/Downloads.html]`

---

## 3. The Principal Officer (PO) — Role and Suspicion Evaluation

### 3.1 Who the PO is
- The PO is the designated senior officer at a Reporting Entity (RE) responsible for AML compliance, STR filing, and regulatory interface with FIU-IND `[PRIMARY-SOURCED — PMLA 2002; RBI Master Direction on KYC]`
- Filing decisions must be made by **authorised staff within SLA** — FIU-IND inspections check this `[PRIMARY-SOURCED — FIU-IND inspection guidelines]` ⚠️ *Specific SLA values need verification*

### 3.2 PO Suspicion-Evaluation Factors
These are the lenses through which a PO evaluates whether to form suspicion. They double as semantic view dimensions in Phase 2.

| # | Factor | Description |
|---|---|---|
| 1 | Business profile | Does the customer's stated business explain the transaction pattern? |
| 2 | Transaction history | Is this consistent with the customer's historical activity at this RE? |
| 3 | Customer risk profile | What risk category was assigned at onboarding / last review? |
| 4 | Income level | Does the amount transacted align with stated income? |
| 5 | Source of income | Is the stated source of income consistent with the transaction? |
| 6 | Beneficiary | Who is the recipient? Is the beneficiary relationship explained? |
| 7 | Transaction frequency | Is the frequency unusual for this customer segment? |
| 8 | Transaction size | Is the size unusual for this customer segment / business type? |
| 9 | Transaction complexity | Is the structure unnecessarily complex (layering indicator)? |
| 10 | Geographies | Do the jurisdictions involved carry elevated risk (FATF list, RBI-specified)? |
| 11 | KYC availability | Are the required KYC documents present, current, and consistent? |

`[SECONDARY—verify — the 11-factor enumeration is NOT confirmed against a primary FIU-IND source. The closest located enumerated framework is IFSCA AML/CFT guidance, which lists 12 factors, not an FIU-IND "11-factor" list. Reconcile provenance before presenting as an FIU-IND framework; scope by regulatory perimeter. DG-19]`

### 3.3 Investigation / EDD Trail and the Tipping-Off Boundary

Between the alert and the disposition, the RE conducts — or consciously declines — enhanced due
diligence. This intermediate step is itself FIU-IND-inspectable and MUST be recorded.

- **Permissible under ongoing EDD:** source-of-funds queries, document / KYC-refresh requests,
  account & history review, branch enquiries. `[HUMAN — review 2026-09-18]`
- **Prohibited (tipping-off):** disclosing to the subject that an STR has been or may be filed.
  `[SECONDARY—verify — citation; DG-22]`
- **The boundary:** "explain the source of these funds" = permissible; any signal that a report is
  being made = prohibited. For clear-cut patterns, immediate filing without extended EDD is
  acceptable — but the record must then carry an explicit **"no EDD undertaken because…"**
  rationale. `[HUMAN]`
- **SLA implication:** suspicion-formation (not the alert) starts the 7-working-day clock; record
  both timestamps and treat the alert→suspicion gap as inspectable. `[HUMAN]` (see §1.1; DG-20)

Scenario schema: captured in the required **§2A Investigation / EDD Trail** section of every
scenario (see `scenarios/SCHEMA.md`).

---

## 4. FIU-IND Inspection Focus Areas

What inspectors actually check (design the product around these):

1. **Not-filing rationale documented** — inspectors look specifically at alert cases that were NOT filed; the absence of a documented rationale is a red flag `[PRIMARY-SOURCED — FIU-IND inspection guidance]` ⚠️ *Specific inspection checklist items need primary-source verification*
2. **Authorised staff within SLA** — was the PO (or delegated officer) the decision-maker, and was the decision made within 7 working days of suspicion formation? `[PRIMARY-SOURCED — PMLA 2002 s.12]`
3. **Alert-to-STR ratio** — the ratio must be plausible for the RE's business profile; both an implausibly low ratio (suppression) and an implausibly high ratio (mechanical filing without genuine suspicion) attract scrutiny `[SECONDARY — published FIU-IND inspection reports; regulatory commentary]` ⚠️ *Verify specific ratio benchmarks used — [UNVERIFIED]*
4. **Generic/templated STRs** — FIU-IND specifically flags STRs where the Ground of Suspicion is a copy-paste template rather than a specific narrative about this customer's pattern `[PRIMARY-SOURCED — FIU-IND quality feedback to REs]` ⚠️ *Need to verify exact language from primary source*

---

## 5. Mule-Account Context (Current, High-Relevance)

- RBI MuleHunter.AI: ML model for mule detection operated by RBI `[SECONDARY — RBI press releases; media coverage]` ⚠️ *Exact operational status needs verification*
- DPIP (Digital Payment Intelligence Platform): RBI-operated platform for sharing fraud signals across the ecosystem `[SECONDARY — RBI announcements]` ⚠️ *Verify current operational status*
- I4C Suspect Registry: Indian Cyber Crime Coordination Centre suspect account database `[SECONDARY — MHA/I4C announcements]`
- SC directive (Aug 2026): Supreme Court directed RBI to circulate a mule-account SOP `[SECONDARY — media reports; court order not directly verified]` ⚠️ *[UNVERIFIED] — verify against court order*
- MHA mandate: All banks to integrate MuleHunter.AI by Dec 2026 `[SECONDARY — media reports]` ⚠️ *[UNVERIFIED] — verify against MHA circular*

**Product boundary:** This product does NOT claim to detect mule accounts. It ingests signals from the above systems and supports disposition + FIU-IND reporting. This boundary is both a technical and regulatory constraint.

---

## 6. Red-Flag Indicators — FIU-IND Published List

⚠️ **IMPORTANT:** The FIU-IND publishes specific red-flag indicator lists. The entries below are `[UNVERIFIED]` until mapped to the exact FIU-IND document.

Common mule-account red-flag patterns (for scenario drafting — MARK UNVERIFIED UNTIL SOURCED):

| # | Indicator | Category |
|---|---|---|
| RFI-01 | Multiple credits followed by immediate near-total debit (pass-through pattern) | Velocity / Structure |
| RFI-02 | Sub-threshold cash deposits across linked accounts (structuring) | Structure / CTR avoidance |
| RFI-03 | Account dormant >6 months → sudden high-value activity | Anomaly |
| RFI-04 | Same mobile number / device ID across multiple accounts at the same RE | Identity / Linkage |
| RFI-05 | Credit from known suspect account (I4C / DPIP match) | Signal-based |
| RFI-06 | Salary account with credits inconsistent with employer profile | Income inconsistency |
| RFI-07 | Beneficiary concentration — all debits to same counterparty across otherwise unrelated accounts | Layering |
| RFI-08 | Cross-border wire to FATF high-risk or non-cooperative jurisdiction | Geography |
| RFI-09 | PEP customer with transaction pattern inconsistent with public-function income | PEP |
| RFI-10 | NPO receiving large cash donations, redistributing immediately | NPO misuse |

`[UNVERIFIED — map each to FIU-IND Typology Reports or Master Direction before using in generated output]`

---

## 7. What Makes a Ground of Suspicion "Generic/Templated" — Checklist

FIU-IND penalises templated STRs. Before any generated Ground of Suspicion is considered done,
check it against this list:

### Templated-Narrative Red Flags (fails if any box is checked):
- [ ] Uses generic phrases like "transactions appear suspicious" without specifics
- [ ] Does not cite the specific transaction amounts, dates, or patterns observed
- [ ] Does not name the specific red-flag indicator(s) triggered
- [ ] Does not explain how the transaction contradicts the customer's stated business/income/profile
- [ ] Does not address each PO evaluation factor that is relevant to this case
- [ ] Beneficiary relationship is not discussed (where relevant)
- [ ] Geography risk is not discussed (where cross-border is involved)
- [ ] KYC inconsistency is not discussed (where KYC gaps exist)
- [ ] Is substantially identical to a previously filed STR (copy-paste)
- [ ] Could apply to any customer at this RE without modification

### What a Good Ground of Suspicion Includes:
- Specific customer identifier (account number, PAN, name — anonymised in scenarios)
- Specific transaction(s): date, amount, counterparty, channel
- The specific contradiction: stated profile vs. observed pattern
- The red-flag indicator(s) triggered, by name
- The PO evaluation factors that formed the basis of suspicion
- Why alternative explanations were considered and rejected (or why none was available)
- The regulatory/statutory basis for filing (PMLA provision, FIU-IND indicator)

`[SECONDARY — synthesised from FIU-IND quality feedback and published AML guidance]` ⚠️ *Verify each item against primary FIU-IND source*

---

## 8. Statutory Basis Quick Reference

| Provision | Content |
|---|---|
| PMLA 2002 s.12(1)(b) | Obligation to file STR |
| PMLA 2002 s.12A | Tipping-off prohibition |
| PMLA 2002 s.12(1)(c) | Records retention |
| RBI Master Direction on KYC (current) | KYC obligations for banks |
| FATF Recommendations | International ML/TF standards (India: FATF member) |

`[PRIMARY-SOURCED for PMLA sections; SECONDARY for FATF]` ⚠️ *RBI Master Direction version needs pinning*

---

## 9. Domain Gaps — Running List

Items where the domain is underspecified or unverified. Each gap is a risk to the product's
defensibility. Add new gaps as they are discovered; remove only when sourced.

| # | Gap | Risk | Status |
|---|---|---|---|
| DG-01 | CBTR threshold (₹5 lakh indicative) — may have been revised | Medium — wrong threshold in output | UNVERIFIED |
| DG-02 | STR-related records retention period (10 years?) | Low — product doesn't surface retention in output | UNVERIFIED |
| DG-03 | Specific FINGate 2.0 mandatory field configuration mechanism | Medium — product describes field structure | UNVERIFIED |
| DG-04 | Alert-to-STR ratio benchmarks used in inspections | HIGH — product surfaces ratio view | UNVERIFIED |
| DG-05 | SC mule SOP directive — exact date and order text | Low — contextual, not in output | UNVERIFIED |
| DG-06 | MHA MuleHunter integration mandate — exact circular | Low — contextual | UNVERIFIED |
| DG-07 | FIU-IND published red-flag indicator list (exact document + version) | HIGH — product cites indicators in STR | UNVERIFIED |
| DG-08 | FIU-IND inspection SLA for PO decisions | Medium — product validates SLA compliance | UNVERIFIED |
| DG-09 | Templated-narrative checklist — primary-source confirmation | HIGH — core product feature | UNVERIFIED |
| DG-10 | DPIP and MuleHunter.AI current operational status | Medium — product mocks ingestion from these | SECONDARY only |
| DG-19 | PO evaluation factors — provenance of the 11-factor enumeration; reconcile against IFSCA AML/CFT guidance (12 factors) and locate the FIU-IND/RBI equivalent | HIGH — product presents these as an FIU-IND framework | SECONDARY—verify |
| DG-20 | STR 7-working-day deadline — exact rule text (PML (Maintenance of Records) Rules); confirm trigger = suspicion-formation | HIGH — product computes SLA from this | SECONDARY—verify |
| DG-21 | ₹10L "integrally connected transactions" / monthly-aggregation mechanics — exact wording | Medium — surfaced in structuring narratives | SECONDARY—verify |
| DG-22 | Tipping-off — precise statutory citation (s.12A alone vs s.12(2)/s.12A(3)/PML Rules r.8(6)) and the permissible-EDD boundary | Medium — surfaced in EDD/investigation trail | SECONDARY—verify |
