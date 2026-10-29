---
id: "14"
title: "Stale KYC, unreachable customer, unexplained Singapore inward remittances — contested"
status: FINAL
disposition: CONTESTED
rules_cited: [STR-001, RFI-006, POE-003, POE-005, POE-006, POE-011, POE-012, SB-004, INS-001]
---

### 1. Synthetic Pattern

**Account:** Savings account, private sector bank, Tier-2 city branch
**Customer KYC (CUST-14):** Occupation: retired professional; declared income: ₹30,000/month (pension + rental); risk category: Low; age: 62; KYC last updated 2 years ago; Aadhaar + PAN linked; address: residential, Tier-2 city.

**Baseline (months 1–36):** Monthly pension credit ₹22,000 from government. Monthly rental income credit ₹8,000 NEFT from a known tenant. Household expenses. No international transactions. Consistent Low-risk profile.

**Alert period (months 37–38):**

| Month | Transaction | Amount | Counterparty |
|---|---|---|---|
| Month 37 | Inward SWIFT (NRE-style, though account is NRO) | ₹8,20,000 | Sender: "V Patel" — DBS Bank Singapore |
| Month 37 | Inward SWIFT | ₹6,40,000 | Sender: "V Patel" — same |
| Month 38 | Inward SWIFT | ₹8,80,000 | Sender: "V Patel" — DBS Bank Singapore |
| Month 38 | Inward SWIFT | ₹7,50,000 | Sender: "V Patel" — same |

Total inward remittances over 2 months: ₹30,90,000 (₹30.9 lakh). This is against a 36-month baseline of ₹30,000/month domestic income.

**Follow-up attempts:**
- Bank sends an account activity letter to KYC address → returned undelivered ("addressee unknown at this address")
- Bank calls KYC mobile number → not reachable; voicemail in an unrecognised language
- Bank emails KYC email address → bounce (account closed)
- Relationship manager notes the KYC address on file is 2 years old; CUST-14 may have moved

**No response from the customer. KYC is effectively stale and unverifiable.**

**Case record in the seed (`ddp/seed_data.py`, 2026-10-28):** the four inward SWIFT credits (July–August 2026) and two electricity auto-debits (₹2,400). Pension and rent credits are not in the case record. ASSUMED: the auto-debits and all dates.

---

### 2. Reasoning Chain

```
RFI-006 (income inconsistency) [NEEDS-VERIFICATION]
  → ₹30.9L inward from Singapore over 2 months vs. ₹30K/month declared income.
    Even if CUST-14 has a Singapore NRI family member, the scale requires
    explanation. No prior international activity in 36 months.
  → corpus: RFI-006

POE Factor 12 — KYC availability (POE-012)
  → KYC is 2 years old. The address is undeliverable; phone is unreachable; email
    is bounced. The RE cannot contact the account holder. For a Low-risk account
    now receiving large inward remittances, the inability to verify the customer's
    current identity and address is a material compliance gap.
  → corpus: POE-012; SB-004 (KYC obligations under RBI MD on KYC)

POE Factor 2 — Transaction history (POE-003)
  → 36-month domestic-only pattern. ₹30.9L in 2 months from Singapore is a
    complete departure with no prior history of NRI connections.

POE Factor 5 — Source of income (POE-006)
  → The sender (V Patel, DBS Singapore) could be CUST-14's adult child working
    in Singapore (extremely common in India), a business counterparty, or an
    unknown party. Without customer contact, source of income cannot be assessed.

POE Factor 11 — Geographies (POE-011)
  → Singapore is not on the FATF list and is a well-regulated financial centre.
    Singapore itself is not a risk factor; the risk here is KYC staleness, not
    jurisdiction. This factor weighs toward CLOSE (no geographic risk), not FILE.
```

**CONTESTED — two defensible PO readings:**

**Reading A — FILE STR:**
- Unreachable customer with stale KYC receiving ₹30.9L from an undisclosed international source
- The account holder cannot be verified at the KYC address; for all the RE knows, the account is being operated by a third party
- The total inability to contact CUST-14 after multiple attempts — in a customer who previously had no international activity — is a red flag in itself
- Filing protects the RE: if CUST-14 is a victim of account takeover, the RE has documented its suspicion

**Reading B — CLOSE-NO-FILE (after enhanced KYC effort):**
- Singapore inward remittances from "V Patel" to a 62-year-old Indian resident are most likely NRI family support or a child's financial support to an elderly parent — this is extremely common in the Indian diaspora context
- Singapore is a FATF-compliant, well-regulated jurisdiction; DBS Bank Singapore is a tier-1 institution
- ₹30.9L = ~₹15L/month is not implausible as family support to an elderly parent from a Singapore-based child with a professional income
- The correct response is enhanced KYC outreach, not an STR — the RE should try harder to reach the customer (via known nominees, alternate contacts, branch visit) before filing
- Filing an STR on what is likely a law-abiding retired person because the bank's contact information is stale is a disproportionate response

**The crux:** Customer uncontactability is the decisive variable. The product should distinguish between:
- Uncontactable because the bank's details are stale (KYC compliance failure, but not ML) → enhanced outreach
- Uncontactable because the customer is being sheltered by a ML operator → genuine account takeover suspicion

Without more information, this cannot be resolved from the transaction data alone.

---

### 4. Draft Closure Rationale (conditional — if contact established)

If CUST-14 is reached through alternative means (nominee contact, branch visit, courier to alternate address) and confirms: (a) the sender (V Patel) is their son/relative in Singapore; (b) the remittances are family financial support; and (c) the KYC address has changed (which the customer then updates), the closure rationale would be:

Inward remittances from V Patel, Singapore confirmed as family financial support from CUST-14's [relationship]. Singapore is a FATF-compliant jurisdiction; DBS Bank Singapore is a regulated institution. Source of funds (salary/business income in Singapore) is consistent with the sender's profile. KYC updated to new address and contact details. No ML pattern. Alert closed.

---

### 5. Templated-Narrative Check

(Reading A — FILE version)

- Uses generic phrases without specifics: **PASS** — ₹30.9L, Singapore, DBS Bank, V Patel, 3 failed contact attempts
- Does not explain contradiction with profile: **PASS** — 36-month domestic baseline; no prior international history
- Does not address relevant PO factors: **PASS** — Factors 3, 5, 11, 12 addressed
- Geography risk not discussed: **PASS** — Singapore noted as low-risk (unusual; most GoS discuss risk; here the absence of geographic risk is itself a finding)

---

### 6. Contestedness Note

This scenario tests a specific product design question: how does the product handle the case where the suspicious element is **KYC staleness + customer uncontactability**, not the transaction pattern itself?

The transaction pattern (NRI remittances from Singapore) is almost certainly innocent. The suspicion arises from the procedural failure (uncontactable customer) combined with the departure from baseline.

**Product design implication:** The system should flag this as a KYC-compliance issue first, an AML issue second. The recommended action is enhanced KYC outreach, not an immediate STR — with a clear deadline (within 5 working days of alarm) after which FILE becomes the default.

**Human decision required:** Choose the resolution path: (A) FILE because uncontactable after 3 attempts, (B) enhanced outreach with deferred disposition, (C) keep as CONTESTED. Recommended: (B) as the realistic PO decision.

---

### 7. Human Review

```
status: corrected
reviewer: —
date: —
decision: —
correction_notes: "POE corpus ID misreferences corrected in body text and rules_cited frontmatter."
domain_rule_extracted: "KYC staleness amplifies ML risk from otherwise innocent-looking
transactions. An RE's inability to contact a customer at KYC-registered details, when
combined with a material change in transaction profile, is an independent suspicious
indicator under POE Factor 12 — even where the transaction itself may be innocent.
The product should model KYC-staleness as a suspicion modifier, not a binary factor.
(corpus: POE-012; SB-004)"
```
