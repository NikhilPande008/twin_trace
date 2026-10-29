# Impact: what is sourced, what is reasoning, what is not established

Researched 2026-10-21. Each claim is labelled **SOURCED** (a public page says it; link and what was
checked given), **REASONING** (this project's inference, not data) or **NOT ESTABLISHED** (looked for,
not found). Nothing here is a measured result of this product; those are in
[CLAIMS_REGISTER.md](CLAIMS_REGISTER.md) and the in-app *Measured Results* page.

## 1. The scale of the decision workload

| Claim | Status | Source and what it says |
|---|---|---|
| FIU-IND received **4,33,761 STRs in FY 2021-22**. | SOURCED (primary; dated, newer figures not found) | FIU-IND Annual Report 2021-22, §3.2.1 "Receipt of STRs", p. 20: "In FY 2021-22, 4,33,761 STRs were received." |
| FIU-IND treats STR **quality** as an engagement issue with reporting entities. | SOURCED (primary) | Same section: "The net number of STRs filed reflects the engagement with REs to strike a balance between quantity and quality of STRs filed. FIU-India has routinely issued guidelines to REs aimed at improving the quality of STRs reported." |
| Indians lost **₹22,845.7 crore to cyber fraud in 2024**, against ₹7,465.1 crore in 2023. | SOURCED (secondary report of an official reply; verify against the Lok Sabha record) | Scroll.in, 23 Jul 2025, reporting a written Lok Sabha reply by the Minister of State for Home Affairs. |
| **22.6 lakh** cybercrime incidents were registered on the national portal in 2024 (up 42% on 2023). | SOURCED (same article) | As above. |
| Over **24 lakh "Layer 1" mule accounts** had been shared with participating entities through I4C's Suspect Registry, and investigators were identifying about **4,000 mule accounts a day**. | SOURCED (same article; the daily rate is attributed to the Home Ministry) | As above. |

Not used: other mule-account and prevented-loss figures found in explainers differ from the above and
were not reconciled, so they are left out.

## 1b. What FIU-IND has penalised banks for (SOURCED, read 2026-10-28)

Seven Section 13 PMLA orders against banks and payments banks were read page by page on
2026-10-28. Each published summary carries FIU-IND's own disclaimer that it is representational
and is not a precedent. The findings are coded in
[`domain/enforcement/fiu_orders.yaml`](../domain/enforcement/fiu_orders.yaml), and the failure
taxonomy with what Twin Trace does about each failure is in
[`failures.yaml`](../domain/enforcement/failures.yaml). Orders read:
Union Bank of India 13/2024 and 01/2025, Axis Bank 09/2024, Paytm Payments Bank 07/2024, Fino
Payments Bank 01/2024, HSBC 19/2022 and Punjab National Bank 8/2019.

| Failure (coded from the orders) | Orders citing it, of 7 | Twin Trace |
|---|---|---|
| No effective internal mechanism to detect and report suspicious transactions | 6 | PARTIAL: alert generation is upstream; the ledger records how each alert was handled |
| Suspicious transactions not reported, or late or inaccurate | 6 | PARTIAL: defensible drafts; the officer decides and files |
| Ongoing or enhanced due diligence not done | 5 | GAP |
| **Alerts closed improperly, cursorily or without application of mind** | **3** (UBI 2024, Axis 2024, HSBC 2022) | **ADDRESSED**: a rationale is required, figures are gated, the stress test names the facts a closure rests on, and closures are re-checked when those facts change |
| Incorrect or disorganised figures or data supplied to FIU-IND | 3 (PNB 2019, HSBC 2022, Axis 2024) | ADDRESSED: calculator of record, decision package export |
| Threshold reports missing or wrong | 2 | GAP |
| Many alerts on one account, each closed cursorily | 1 (UBI 2024, a direction) | ADDRESSED: earlier closures on the same customer are counted and shown |
| Alerts not closed within a reasonable period | 1 (Axis 2024) | PARTIAL: SLA clock from suspicion formed |

What this establishes and what it does not:

- **SOURCED:** FIU-IND has penalised banks for how alerts were closed, not only for reports that
  were never filed. The Axis order cites failure to close alerts "based on application of mind",
  the UBI order observes alerts "closed with minimal justification", and the HSBC order charges
  improper closure of alerts under PMLR 7(3).
- **Honest scope:** the failures cited most often (the internal mechanism, unreported transactions,
  due diligence) are mostly upstream of Twin Trace. The product addresses the closure and figures
  failures directly; it does not address most of what was penalised.
- **NOT ESTABLISHED:** how common any failure is across Indian banks. Seven orders support no
  rate. This also does not settle gap DG-13 (a primary citation that a not-filed rationale must be
  documented): the orders penalise improper closure, but no circular stating the documentation
  requirement was found.

The [inspector question bank](../domain/enforcement/inspector_questions.yaml) turns these
failures into questions a recorded decision must answer from its own record. Each question carries
the orders it comes from.

## 2. Why that matters for this product (REASONING)

- Every alert that reaches a Principal Officer needs a decision that can be explained later. At the
  volumes above, the part that scales badly is the written reasoning and its numbers.
- Language models state arithmetic with confidence and get it wrong. In this repository's own
  holdout, the same model without controls put at least one unsupported figure into **6 of 6**
  drafts, and the full product's drafter still did in **3 of 6**; the gate kept all 3 out of the
  accepted drafts (`evals/RUN-20261021T080109Z-live/`, six synthetic cases, author-labelled, so
  this is evidence that the gate is necessary, not a measure of real-world error rates).
- The product targets that one failure and the records around it. It does not detect mule accounts;
  I4C, DPIP and bank systems do that. It starts where an alert has already fired.

## 3. NOT ESTABLISHED

- **That FIU-IND specifically penalises templated or copy-pasted narratives.** Searched for on
  2026-10-21; no FIU-IND source found. The annual report says only that quality is an engagement
  issue (above). The 10-point anti-templating checklist is therefore described everywhere as a
  *product-compiled heuristic* (gap DG-09), never as an FIU-IND standard. The drafting prompt
  inherited from the baseline still contains the sentence "FIU-IND specifically flags generic,
  templated, or copy-paste narratives"; it is a model instruction, not a public claim, but treat
  it as unverified.
- **Any saving of officer time, any reduction in filing errors in practice, any adoption.** No
  officer study has been run. Do not state one.
- **Current STR volume.** Only FY 2021-22 was found. Newer annual reports were not located.
- **Any deadline or regulation change dated December 2026**, mentioned in earlier internal
  notes. No source was found; it is not used.

## 4. Where the same pattern could apply (direction, not delivered)

The mechanism is general: *a model drafts, but every number in a document that someone signs must
trace to a source row or a hashed, re-runnable calculation, checked again at the moment of
recording, with the decision written to a tamper-evident log.* Other places with a signed,
figure-bearing narrative include insurance fraud referrals, audit workpapers and tax
representations. None of that is built or tested here; it is a statement about the design, not a
market claim.

## 5. Sources (checked 2026-10-21)

- FIU-IND, Annual Report 2021-22: <https://fiuindia.gov.in/pdfs/downloads/AnnualReport2021_22.pdf>
- Scroll.in, "Indians lost Rs 22,845 crore to cyber fraud in 2024, a 206% rise from previous year:
  Centre": <https://scroll.in/latest/1084796/indians-lost-rs-22845-crore-to-cyber-fraud-in-2024-a-206-rise-from-previous-year-centre>
