# Validation contract

What the product checks, where, and what each result means. Code is the source of truth; this
file explains it. Status labels follow CLAUDE.md §4.

## 1. Monetary figures (`ddp/money.py`, `validate_gos_evidence`) — PROVEN offline

**Supported forms**, each parsed to one exact value in rupees:

| Form | Examples |
|---|---|
| Prefix | `₹3,25,000` · `₹ 325000` · `Rs. 3,25,000` · `Rs.28K` · `INR 3250000` · `₹32.5 lakh` · `Rs 1.2 Cr` |
| Bare lakh/crore | `32.5 lakh` · `3 lakhs` · `1.2 crore` |
| Suffix | `3250000 INR` · `3,25,000 rupees` · `5,000/-` |

Commas may be Indian or western. Multipliers: K / thousand = 10³, L / lakh / lac = 10⁵,
Cr / crore = 10⁷.

**Hard failures** (the draft cannot be READY, and cannot be recorded):

- a figure that is not exactly a single transaction amount of this alert or an INR fact of the
  cited calculator run (no tolerance, no rounding)
- a figure that cannot be read as one exact value: a range (`₹3-4 lakh`), a currency marker with
  no number (`₹ thirty lakh`)
- a transaction ID that is not in this alert
- a total the calculator did not produce (the validator never adds up transactions itself)

**Not supported:** amounts written in words, other currencies. These fail as unreadable or are
not recognised; see limits.

## 2. Claim statuses (`ddp/claims.py`) — PROVEN offline

| Status | Meaning |
|---|---|
| Verified calculation | equals an INR fact of the calculator run; fact IDs, derivation and source rows shown |
| Source transaction | equals a single transaction amount; transaction IDs shown |
| Needs review | equals a transaction amount, but the sentence names a different counterparty |
| Unsupported claim | matches nothing |
| Unreadable figure | not one exact value |

"Verified" means the figure matches the recorded inputs. It does not mean the inputs are true,
and it does not check the rest of the sentence. Sentences with no checked figure are listed as
**outside deterministic coverage** for the officer to review.

## 3. Hard failure vs advisory

| Check | Effect |
|---|---|
| Figures and transaction IDs (§1) | **Hard**: blocks READY; recorder refuses |
| Customer-disclosure language (`tipping_off_customer`) | **Hard** at recording and for agent submissions |
| Other policy patterns (`tipping_off_str`, `tipping_off_disclosure`, accusation, PII) | **Advisory** at recording (shown, stored in `validation.policy_advisory`). `tipping_off_str` blocks filing references in FIU-bound text; whether it should is an open question (DECISIONS.md) |
| Needs-review figures, sentences outside coverage | **Advisory**: the confirmation step asks the officer to acknowledge them |
| Model quality checklist (score, READY/NEEDS_REVISION) | **Advisory**, model-based; fails closed on unparseable output |
| AI recommendation vs officer disposition | **Advisory**: the officer may disagree and say why (`override_reason`) |

A human can disagree with the model. A human cannot record an unsupported figure.

## 4. Stale state

- The recorder always re-validates the exact text it records. A stale UI cannot authorise bad
  figures.
- If the caller passes `validated_draft_sha256` and the text has changed since, recording is
  refused ("text changed after it was checked").
- The UI's figure panel is recomputed on every change of the text. The model quality badge is
  marked **NOT RE-CHECKED** as soon as the text differs from what was checked.
- Each ledger row stores `validation`: draft hash, transaction-input hash, compute run, gate
  version, policy advisories, time.

## 5. Policy audience

A Ground of Suspicion is addressed to FIU-IND. Referencing a filing there is not tipping-off;
telling the customer is (PMLA s.12A, corpus SB-003). So `tipping_off_customer` is the hard
check, and filing-reference patterns stay advisory at recording. Domain review of this split
is pending (human).

## 6. Structured model output (`ddp/structured.py`) — PROVEN offline

Schema-valid is not enough: each POE factor and each checklist item must appear exactly once.
A factor citing a transaction not in the case is flagged (`unknown_txn_ids`) and that citation
is dropped. One repair retry; a second failure gives placeholder records marked `fallback`,
never counted as success.

## 7. Known limits

- Values, not meaning: a figure that equals a real fact passes even if the sentence attributes it
  to the wrong thing (holdout H-01: "₹3 lakh moved to the flagged handle" equals the credit
  total, not the outflow).
- Counterparty matching is a literal phrase match (holdout H-02 missed "the home-loan account"
  vs "Own home-loan account").
- No check of prose without figures, of dates beyond a window warning, or of legal reasoning.
