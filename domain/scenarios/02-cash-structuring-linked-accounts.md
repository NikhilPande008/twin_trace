---
id: "02"
title: "Cash structuring below CTR threshold across three linked savings accounts"
status: FINAL
disposition: FILE
rules_cited: [STR-001, STR-002, CTR-001, CTR-003, RFI-002, POE-005, POE-009, POE-010, INS-001]
---

### 1. Synthetic Pattern

**Accounts (all at the same bank, three different branches in the same city):**

| Account | Customer | Branch | Opened | KYC |
|---|---|---|---|---|
| ACCT-02-A | CUST-02A | Branch 1, Andheri | T−45 | Daily labourer, ₹10,000/month, Low risk |
| ACCT-02-B | CUST-02B | Branch 2, Kurla | T−30 | Housewife, no declared income, Low risk |
| ACCT-02-C | CUST-02C | Branch 3, Dadar | T−10 | Student, no declared income, Low risk |

All three accounts opened within 45 days. CUST-02A, CUST-02B, and CUST-02C share the same residential address on their KYC (though this was not flagged at account opening because the three accounts were at different branches).

**Transaction pattern (days T+1 to T+15):**

All three accounts receive daily cash deposits over counter for 15 consecutive days:

| Account | Daily deposit | 15-day total |
|---|---|---|
| ACCT-02-A | ₹9,500 | ₹1,42,500 |
| ACCT-02-B | ₹9,500 | ₹1,42,500 |
| ACCT-02-C | ₹9,000 | ₹1,35,000 |

**Day T+16:** All three accounts transfer their full balance by NEFT to a single current account (ACCT-02-TARGET) at a different bank. Aggregate transferred: ₹4,18,500.

**Alert trigger:** Bank's AML system flags ACCT-02-A on the last deposit day when the cumulative monthly cash total is about to reach ₹1,42,500. Cross-account linkage check (address match) reveals the three linked accounts.

**Ingested signals:** None from external sources. Internal linkage detection only.

**Note:** No single account crosses the ₹10 lakh CTR threshold in this calendar month. Aggregate across three accounts: ₹4,20,000 — also below ₹10 lakh. However the structuring pattern (sub-threshold, daily, multiple linked accounts, same-day aggregation) is the alert basis.

**Case record in the seed (`ddp/seed_data.py`, 2026-10-28):** 45 daily cash credits (15 days × three accounts) and three NEFT debits on T+16 to ACCT-02-TARGET of ₹1,42,000, ₹1,42,000 and ₹1,34,500 (₹4,18,500). ASSUMED: the per-account split of the T+16 transfer (each account kept a small balance). Dates: deposits 4–18 Aug 2026.

---

### 2. Reasoning Chain

```
RFI-002 (structuring / CTR avoidance) [NEEDS-VERIFICATION — no primary FIU-IND citation]
  → Daily deposits of ₹9,000–₹9,500 for exactly 15 consecutive days, all below the
    ₹10,000 round-number threshold, across three accounts opened within 45 days at
    the same bank. The structure appears designed to stay well below the ₹10L CTR
    monthly aggregate. Structuring is both an RFI and a predicate offence under PMLA.
  → corpus: RFI-002

CTR dual-filing consideration (corpus: CTR-001, CTR-003):
  → No single account's monthly cash total exceeds ₹10L. No CTR obligation is
    triggered individually. But the aggregate pattern across linked accounts
    (per CTR-001: "including linked accounts") needs PO evaluation — if the three
    accounts are treated as linked, aggregate = ₹4.20L; still below ₹10L this month.
    If deposits continue next month, CTR threshold may be crossed. Monitor.

POE Factor 4 — Income level (POE-005)
  → CUST-02A: ₹10,000/month declared; ₹1,42,500 cash in 15 days = 14× monthly income.
    CUST-02B: housewife, no income; ₹1,42,500 cash with no source explained.
    CUST-02C: student, no income; ₹1,35,000 cash with no source explained.

POE Factor 8 — Transaction size (POE-009)
  → Daily ₹9,500 deposits are anomalous for all three KYC profiles. No declared
    business or income source explains this volume.

POE Factor 9 — Transaction complexity (POE-010)
  → Three accounts, three branches, same-day aggregation on day 16. The structure
    is unnecessarily complex for any legitimate cash accumulation purpose. A single
    account would suffice for legitimate use; the multi-account structure serves
    only to fragment the cash trail.

POE Factor 2 — Transaction history (POE-003)
  → All three accounts are recently opened; there is no prior legitimate transaction
    history. First activity is the structuring pattern itself.

Statutory basis:
  → PMLA 2002 s.12(1)(b) [corpus: SB-002]: suspicion formed — structured deposits
    across linked accounts with no income basis, followed by immediate aggregation.
  → Note: structuring is also a predicate offence under PMLA (Schedule to the Act);
    this is ML of the proceeds of structuring itself, not merely evidence of ML.
```

**Alternative explanation considered:** Legitimate family pooling of savings (e.g., chit fund contribution, property purchase instalment). Rejected: the regularity (exactly ₹9,000–₹9,500 daily, same amount each day), the identical timing across three accounts at different branches, and the immediate day-16 aggregation to a single external current account are inconsistent with organic family savings behaviour. The address identity across all three KYC profiles was not disclosed to any branch at account opening.

---

### 2A. Investigation / EDD Trail

| Step | Date | Action | Outcome |
|---|---|---|---|
| EDD-1 | T+15 | On the linkage alert, RE ran a cross-branch review and confirmed the shared residential address across ACCT-02-A/B/C KYC records. | Linkage confirmed internally; not disclosed to the customers. |
| EDD-2 | T+16 | Branch raised a routine source-of-funds query on ACCT-02-A's cash deposits, framed as ongoing due diligence with no reference to any report. | No documentary explanation produced; depositor stated only "family savings." |
| — | T+17 | PO judged that further enquiry across the three linked accounts risked tipping-off given the coordinated pattern, and that suspicion was already sufficiently formed. | Proceeded to disposition without further EDD. |

**Tipping-off boundary:** The source-of-funds query (EDD-2) stayed within permissible ongoing due diligence and did not disclose that a report was contemplated; no further enquiry was made once suspicion was formed. `[HUMAN — source-of-funds enquiry is permissible EDD; disclosing the STR is prohibited]` `[SECONDARY—verify — exact tipping-off citation may be PMLA s.12(2)/s.12A(3) + PML Rules r.8(6), not s.12A alone; DG-22]`

**Suspicion formed on:** T+17 — distinct from the last-deposit date (T+15) and the alert date (T+15). This timestamp starts the 7-working-day SLA clock; the alert→suspicion gap (2 days) is itself inspectable. `[HUMAN — trigger is suspicion-formation]` `[SECONDARY—verify — "7 working days" text in PML (Maintenance of Records) Rules; DG-20]`

---

### 3. Draft Ground of Suspicion

`[HUMAN — Q2] Narrative lead:` the suspicion is carried primarily by the **coordination signature** — three accounts opened within 45 days, a shared residential address concealed at onboarding (different branches), and a synchronized day-16 exit to a single external account — not by cash volume alone. Pooled family cash is the common innocent story; the coordination is what defeats it. On the next pass, open the narrative on the coordination pattern and treat deposit volume as corroborating.

Three savings accounts (ACCT-02-A, ACCT-02-B, ACCT-02-C) held at three different branches of this RE — by CUST-02A (daily labourer, ₹10,000/month declared income), CUST-02B (housewife, no declared income), and CUST-02C (student, no declared income) — were identified as linked: all three KYC records disclose the same residential address, though accounts were opened at separate branches over a 45-day window without any branch being aware of the others.

Over 15 consecutive days (T+1 to T+15), all three accounts received daily cash deposits over counter of ₹9,000–₹9,500. No single daily deposit exceeded ₹9,500; each account received fifteen deposits, ₹4,20,000 across the three accounts. On day T+16, all three accounts simultaneously transferred their full balances by NEFT to a single current account (ACCT-02-TARGET) at a different RE, with aggregate funds transferred of approximately ₹4,18,500.

No declared income source or legitimate business purpose accounts for the cash deposits: CUST-02A's declared income of ₹10,000/month is 7% of the 15-day cash deposit; CUST-02B and CUST-02C have no declared income. The multi-account, multi-branch structure with identical daily deposit amounts and a same-day aggregation event on day 16 is consistent with structuring to avoid transaction monitoring thresholds (RFI-002, corpus) and is unnecessarily complex for any legitimate purpose (POE Factor 9).

Suspicion is formed under PMLA 2002 s.12(1)(b) on the basis of: (a) structured cash deposits across linked accounts (RFI-002); (b) income inconsistency across all three account holders (POE Factor 4); (c) excessive structural complexity with no legitimate purpose (POE Factor 9); and (d) immediate aggregation to a single external account on the day after the deposit series ends. Note also that structuring is a predicate offence under the PMLA Schedule.

---

### 5. Templated-Narrative Check

- Uses generic phrases without specifics: **PASS** — account references, amounts, 15-day period, day-16 aggregation all specific
- Does not cite specific amounts/dates: **PASS**
- Does not name specific red-flag indicators: **PASS** — RFI-002 named
- Does not explain contradiction with stated profile: **PASS** — income vs. deposit volume for all three customers
- Does not address relevant PO evaluation factors: **PASS** — Factors 2, 4, 8, 9 addressed
- Beneficiary relationship not discussed: **PASS** — same-address linkage and external beneficiary account noted
- Geography risk not discussed: **N/A** — domestic
- KYC inconsistency not discussed: **PASS** — address-match concealment noted
- Could apply to any customer without modification: **PASS** — three named accounts with specific facts
- Substantially identical to a previous STR: **N/A**

**Result: 0 fails.**

---

### 7. Human Review

```
status: FINAL
reviewer: human-PO-proxy (review-gate batch)
date: 2026-09-18
decision: FILE — confirmed (clear call, not CONTESTED — Q1)
correction_notes: "Added §2A Investigation/EDD Trail (schema change from Q6). Recorded review-gate rulings (§8). Added Q2 narrative-lead note to §3. SLA clock set to suspicion-formation timestamp T+17 (Q4). Prior: POE corpus ID misreferences corrected in body text and rules_cited frontmatter."
domain_rule_extracted: "Backfilled to DOMAIN.md: (1) SLA clock starts on suspicion-formation, record alert→suspicion gap; (2) Investigation/EDD trail is a required, inspectable step between alert and disposition; (3) tipping-off boundary — source-of-funds EDD permissible, STR disclosure prohibited; (4) PO 11-factor enumeration is unverified (DG-19). Citation items marked [SECONDARY—verify]."
```

---

### 8. Review-Gate Rulings (review batch, 2026-09-18)

`[HUMAN]` = analytic / workflow judgment from human domain review. `[SECONDARY—verify]` = citation
queued for primary-source confirmation (a [HUMAN] ruling does not source a citation-level fact).

- **Q1 — Disposition:** FILE confirmed; a clear call, not CONTESTED. Keep scenario 02 as the
  anchor/clear case; do not spend contested-ness budget here — invest it in scenarios where two
  competent POs genuinely disagree. `[HUMAN — MEDIUM-HIGH]`
- **Q2 — Lead fact:** Suspicion is carried primarily by the coordination signature (coordinated
  opening + concealed shared address + synchronized day-16 exit), not cash volume. Narrative
  should lead there (note added to §3). `[HUMAN — MEDIUM-HIGH]`
- **Q3 — Narrative positioning:** The draft reads analytic/textbook by design, and that is the
  product's pitch — FIU-IND's standing complaint is that filed STRs are templated, so the target
  is "better than what is actually filed," not imitation of real filings. State this explicitly in
  the demo rather than chasing a "filed" texture. `[HUMAN]` `[SECONDARY—verify — FIU-IND
  quality-feedback language on templated STRs; DG-09]`
- **Q4 — SLA trigger:** The 7-working-day clock starts on suspicion-formation (§2A "suspicion
  formed on" = T+17), not the deposit or alert date. Record both alert and suspicion timestamps;
  the gap is inspectable. `[HUMAN — trigger principle]` `[SECONDARY—verify — "7 working days"
  text, PML (Maintenance of Records) Rules; DG-20]`
- **Q5 — Primary-source gaps (queued):** (a) ₹10L "integrally connected" monthly-aggregation
  wording (DG-21); (b) FIU-IND red-flag indicator list — the RFI-02 structuring entry, never
  opened, **highest priority** (DG-07); (c) 7-working-day rule text (DG-20); (d)
  attempted-transaction reportability — real but MARGINAL here (completed deposits), do not lean
  on it. `[SECONDARY—verify ×4]`
- **Q6 — Investigation/EDD trail:** Schema gap confirmed and fixed — new required §2A added to
  scenarios/SCHEMA.md and this file. EDD source-of-funds enquiry is permissible ongoing due
  diligence; disclosing the STR is tipping-off. For clear-cut structuring, immediate filing is
  acceptable but the record must carry the EDD trail or a "no EDD because…" rationale. `[HUMAN —
  boundary principle]` `[SECONDARY—verify — tipping-off citation; DG-22]`
