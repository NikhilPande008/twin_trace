---
id: "09"
title: "Seven accounts linked by same mobile device ID — coordinated network mule"
status: FINAL
disposition: FILE
rules_cited: [STR-001, STR-002, RFI-004, RFI-001, POE-003, POE-005, POE-011, POE-012, INS-001, INS-002]
---

### 1. Synthetic Pattern

**Bank:** Private sector bank, single city branch (all 7 accounts opened at the same branch)
**Detection source:** Bank's internal fraud analytics system identifies that 7 savings accounts were activated on mobile banking using the same device fingerprint (device ID: [DEVICE-X]).

**Account summary:**

| Account | Customer | KYC occupation | KYC income | KYC address | Opened |
|---|---|---|---|---|---|
| ACCT-09-1 | CUST-09-A | Factory worker | ₹12K/month | 14 Shivaji Nagar | T−44 |
| ACCT-09-2 | CUST-09-B | Auto driver | ₹15K/month | 14 Shivaji Nagar | T−40 |
| ACCT-09-3 | CUST-09-C | Housewife | nil | 22 Gandhi Road | T−35 |
| ACCT-09-4 | CUST-09-D | Student | nil | 22 Gandhi Road | T−30 |
| ACCT-09-5 | CUST-09-E | Daily labourer | ₹10K/month | 14 Shivaji Nagar | T−22 |
| ACCT-09-6 | CUST-09-F | Retired | ₹8K/month (pension) | 31 MG Road | T−15 |
| ACCT-09-7 | CUST-09-G | Vegetable vendor | ₹10K/month | 14 Shivaji Nagar | T−8 |

All 7 accounts: different names, different Aadhaar numbers, different PAN numbers. However: CUST-09-A, B, E, G share address "14 Shivaji Nagar." CUST-09-C, D share "22 Gandhi Road." Only CUST-09-F has a distinct address.

**Transaction pattern (all 7 accounts, days T+1 to T+15):**

All 7 accounts become active simultaneously on T+1. Over 15 days:

- **Credits:** Each account receives 3–5 UPI credits from different unknown mobile handles (different payers each time, no overlap across accounts). Amounts per credit: ₹50,000–₹1,40,000 (28 credits in all).
- **Debits:** Every account transfers 90–98% of received funds to the same UPI handle: [HANDLE-DEST].

Total inflows (7 accounts): ₹27,30,000 over 15 days.
Total to [HANDLE-DEST]: ₹25,80,000 (94.5%).

**Ingested signals:** [HANDLE-DEST] is not flagged in I4C or DPIP as of alert date.

**Case record in the seed (`ddp/seed_data.py`, 2026-10-28):** 28 UPI credits (3–5 per account) from distinct unknown handles, ₹27,30,000 in all, and seven debits to HANDLE-DEST, one per account, each 90–98% of that account's credits, ₹25,80,000 in all. The seed has one case record (CUST-09); the account is not a ledger column. ASSUMED: individual amounts and dates (19 Aug – 2 Sep 2026). The earlier per-account range (₹30,000–₹80,000) could not reach ₹27,30,000 and was replaced by a per-credit range.

---

### 2. Reasoning Chain

```
RFI-004 (same device ID across multiple accounts) [NEEDS-VERIFICATION]
  → 7 distinct KYC identities (different names, Aadhaar, PAN) all using the same
    mobile device [DEVICE-X] for mobile banking activation. This is highly anomalous:
    while device IDs can theoretically be shared within a household or spoofed, 7
    distinct KYC identities across multiple addresses and a consistent pass-through
    pattern cannot be explained by innocent device sharing. The use of a single device
    across 7 accounts is strong evidence of coordinated account creation by a single
    controller.
  → corpus: RFI-004

RFI-001 (pass-through pattern) [NEEDS-VERIFICATION]
  → Each of the 7 accounts functions as a pure transit: credits arrive from
    multiple sources, 90–98% of funds immediately flow to [HANDLE-DEST].
    No account retains a meaningful balance or uses the account for any
    personal banking purpose.
  → corpus: RFI-001

POE Factor 12 — KYC availability (POE-012)
  → The device-identity mismatch contradicts the KYC records: 7 people cannot
    legitimately share one device. The KYC documents (Aadhaar, PAN) may be
    genuine but are being used by an orchestrator who controls the device.
    The KYC data is present but its authenticity is undermined by the device
    evidence.

POE Factor 2 — Transaction history (POE-003)
  → All 7 accounts are newly opened; all activate and begin transacting
    simultaneously on T+1. There is no prior legitimate baseline; the
    accounts were opened for the pass-through purpose.

POE Factor 4 — Income level (POE-005)
  → Declared incomes: ₹8K–₹15K/month (or nil for housewife/student).
    Each account handles ₹30K–₹80K in 15 days — 2–8× declared monthly income.
    Across all 7: ₹27.3L from individuals with combined declared income of ~₹65K/month.

Address linkage:
  → 5 of 7 accounts share 2 addresses (4 at Shivaji Nagar, 2 at Gandhi Road).
    This linkage was not flagged at account opening (accounts were opened
    individually). A cross-account review reveals the network.

Statutory basis:
  → PMLA 2002 s.12(1)(b) [corpus: SB-002]: suspicion formed for all 7 accounts.
  → The device-ID evidence supports treating this as a coordinated ML operation.
  → STR for all 7 accounts: one STR per account or group STR — confirm with FIU-IND
    FINGate 2.0 guidance on related-account STRs [NEEDS-VERIFICATION — DG-12].
```

**Alternative explanation considered:** Shared device within a household (family members sharing one smartphone for banking). Rejected: 7 accounts across 3 different addresses, 5 distinct family groups, all activating on the same day, all exhibiting an identical pass-through pattern to the same destination handle. A shared-device household would not exhibit this level of cross-address coordination and identical transaction pattern.

---

### 3. Draft Ground of Suspicion

Seven savings accounts at this RE (ACCT-09-1 through ACCT-09-7), opened across a 44-day window at the same branch, were identified as linked through a common mobile device fingerprint ([DEVICE-X]) used to activate mobile banking on all seven accounts. The seven account holders present different names, Aadhaar numbers, PAN numbers, and (for five accounts) two shared addresses, while one holder has a distinct address.

All seven accounts became transaction-active simultaneously on [T+1]. Over the following 15 days, each account received 3–5 UPI credits from different unknown mobile handles (with no overlap of creditors across accounts), totalling ₹27,30,000 in aggregate. In each account, 90–98% of received funds were immediately transferred to a single common UPI handle ([HANDLE-DEST]) — the same destination across all seven accounts. Net funds received by [HANDLE-DEST] from these seven accounts: ₹25,80,000.

The use of a single device fingerprint across seven accounts with distinct KYC identities contradicts legitimate banking use and indicates coordinated control of these accounts by a single orchestrator (RFI-004). Each individual account's credit-then-near-total-debit pattern is consistent with mule pass-through behaviour (RFI-001). The declared incomes of the seven holders (low monthly wages or pension, or nil) cannot account for the ₹27.3L aggregate flow (POE Factor 4). The shared-address linkage (5 of 7 accounts at 2 addresses) was not identified at account opening.

Suspicion is formed under PMLA 2002 s.12(1)(b) for all seven accounts on the basis of: (a) single-device identity linkage across 7 KYC identities (RFI-004); (b) coordinated pass-through pattern, single common beneficiary (RFI-001); (c) income inconsistency across all holders (POE Factor 4); and (d) KYC authenticity undermined by device evidence (POE Factor 12). STRs are being filed for all seven accounts.

---

### 5. Templated-Narrative Check

- Uses generic phrases without specifics: **PASS** — device ID, 7 account references, ₹27.3L total, [HANDLE-DEST] as common beneficiary
- Does not cite specific amounts/dates: **PASS**
- Does not name specific red-flag indicators: **PASS** — RFI-004, RFI-001 named
- Does not explain contradiction with stated profile: **PASS** — income inconsistency across all 7; device-KYC mismatch
- Does not address relevant PO evaluation factors: **PASS** — Factors 3, 4, 12 addressed
- Beneficiary relationship not discussed: **PASS** — [HANDLE-DEST] as single common destination across 7 unrelated accounts
- Geography risk not discussed: **N/A** — domestic
- KYC inconsistency not discussed: **PASS** — device evidence contradicts KYC legitimacy
- Could apply to any customer without modification: **PASS** — 7 named accounts, specific device ID, specific pattern
- Substantially identical to a previous STR: **N/A**

**Result: 0 fails.**

---

### 7. Human Review

```
status: corrected
reviewer: —
date: —
decision: —
correction_notes: "Domain content: 'not possible under legitimate use' softened to 'highly anomalous' — device IDs can theoretically be spoofed or shared; the impossibility language was too strong. POE corpus ID misreferences corrected (Income Level POE-004→POE-005) in body text and frontmatter."
domain_rule_extracted: "Device-fingerprint evidence can override KYC document legitimacy:
even where individual KYC documents (Aadhaar, PAN) appear genuine, coordinated
device-based activation is an independent ML indicator. Confirm whether FINGate 2.0
supports group STR filing for linked accounts or requires individual STRs. (DG-12)"
```
