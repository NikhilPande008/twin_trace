# Design and technical implementation — status

Tracks `docs/DESIGN_AND_TECH_BRIEF-2026-10-21.md` against what was built on 2026-10-21. Owner
for every item: the human (Nikhil), with the coding assistant implementing. "Verified" means a
test or a recorded run demonstrates it. Everything is synthetic-data only.

## Scope and order

Built in dependency order: T1 → T2 → T3 → T4 → T6 → T7 → D1/D2/D4 → D3 → T5 → documents. The
cut-down subset (T7.1–T7.4 in TASKS.md) came first; the rest of the brief followed at the
human's request.

Constraints met along the way: `requirements.txt`, `.gitignore`, `.github/workflows/ci.yml`,
`ddp/seed_data.py`, the domain corpus and scenarios, and the design docs are read-only. No work
required changing them. Pins live in `constraints.txt`; holdout data lives in `evals/holdout/`.
CI runs only five named scripts, so the new test files run under `pytest` locally but **not
in CI** until `ci.yml` is updated (human).

## Completion records

### T1: Enforce validation at the recording boundary
- Status: **verified** (offline)
- Revision: `75518f0`, `f51c09c`
- Before → after: recording checked the officer ID and rationale length only → the recorder
  re-validates the exact text against this alert's transactions and the cited run (which must
  exist, belong to the alert and match its output hash). It refuses stale validation and
  customer-disclosure language. It records once (idempotency key in hashed metadata plus a
  unique index), and writes the ledger row and status in one transaction.
- Tests: `tests/test_recording_gate.py`
- Limits: policy patterns other than customer disclosure stay advisory (open question).
  Unvalidated deferral notes are not supported: every disposition passes the gate.
- Claims supported: "an unsupported figure cannot be recorded"; "repeat submission records once".

### T2: Strengthen claim validation
- Status: **verified** (offline)
- Revision: `deabdc1`, `90c0d26`, `103d008`
- Before → after: `₹<digits>` only, ±1%, validator-computed totals → exact parsing of ₹ / Rs. /
  INR / lakh / crore; no tolerance; totals must be calculator facts; unreadable figures fail;
  claim map with five statuses; factors and checklist items exactly once; unknown transaction
  citations flagged; agent must read the case, give a substantive rationale citing a fact or
  transaction, and avoid customer disclosure.
- Tests: `test_money_gate.py`, `test_claims_and_validation.py`, `test_agent.py`
- Limits: values, not meaning; literal counterparty matching (holdout H-01, H-02 misses).

### T3: Reconstructable decision package
- Status: **verified** (offline)
- Revision: `f351643`
- Before → after: reproduction used current transactions and current code → runs save their
  canonical input; program versions are archived by hash; reproduction uses only recorded data
  and says *unavailable* otherwise; single-file package plus offline verifier; the UI offers the
  download.
- Tests: `tests/test_package.py` (altered package fails; operational changes do not alter it)
- Limits: tamper-evident only; corpus copied at export time. See `DECISION_PACKAGE.md`.

### T4: Failures and model usage explicit
- Status: **verified** (offline, fault injection)
- Revision: `2da67cc`, `e221492`
- Before → after: only the last call was recorded; the pipeline continued after failures → every
  attempt is kept with finish reason, output length and transport errors; errors are classified;
  tokens and latency are summed across retries; truncation is flagged; the pipeline fails
  closed; the agent has tool-call and wall-clock budgets, structured tool errors, a trace ID
  linked to the decision, and no repeated external calls.
- Tests: `tests/test_fault_injection.py`, `tests/test_pipeline_fail_closed.py`
- Limits: no retry button per step in the UI (retry means re-running the section).

### T5: Reliable evaluation
- Status: **implemented; live results recorded on 2026-10-21** (see `CLAIMS_REGISTER.md`)
- Revision: `c47f7d1`, `cccac3d`, `ac0b1e0`
- Before → after: fallbacks were counted as valid; no holdout; no baseline → outcome classes;
  6-case frozen holdout with label provenance; gate catch / false-rejection measurement; three
  conditions; per-run config with dataset hash and git revision.
- Limits: labels are author-assigned; six cases support no general claim; review time not measured.

### T6: External evidence
- Status: **verified** (offline plus live probe)
- Revision: `984982d`, `3daa19c`
- Before → after: profile first-word queries, failures shown as "no results" → typology topic
  search (no case data leaves the bank); outcome statuses; hits labelled *not about this
  customer*; adversarial-snippet tests; `run_live_eval --tavily` injects the adapter.
- Limits: no entity screening by design (synthetic names could match real people).

### T7: Deployment
- Status: **partly verified**
- Revision: `858a387`, `bedac43`
- Verified: a clean Python 3.11 install with `constraints.txt` passes the full gate; demo mode
  isolates sessions and caps model calls; a decision survives a restart on the file database.
- Not verified: the Docker image build (no Docker daemon here), a hosted deployment, sandbox
  execution.

### D1: Evidence-first workspace
- Status: **verified** in the running app (375 / 768 / desktop)
- Revision: `f7ae829`
- Header with synthetic badge and *Not yet known*; evidence column first; kind labels; service
  status (Configured / last call succeeded or failed / Unavailable); neutral product name;
  sidebar collapses on narrow screens.
- Screenshots: `docs/screenshots/`
- Limits: no screen-reader or keyboard-only pass; no usability session.

### D2: Inspectable claims
- Status: **verified** in the running app
- Revision: `f7ae829`
- Live figure panel on the current text, with statuses, fact IDs, derivations, source rows and
  run ID; sentences outside coverage listed; stale model badge.

### D3: Sensitivity view
- Status: **verified** in the running app (ALERT-01)
- Revision: `55d66a4`
- Modeled level wording; assumption → level → evidence to verify; budget shown; advisory reopen
  conditions; *does not cover* list.

### D4: Recording and reconstruction
- Status: **verified** in the running app (confirm and cancel; refusal path; ledger unchanged)
- Revision: `75518f0`, `f7ae829`, `f351643`
- Confirmation step; *pending* STR reference; self-asserted officer ID; *already recorded*;
  package download.
- Limits: a successful *Confirm and record* was not exercised in the browser, to keep the real
  ledger clean. It is covered by the recorder tests.

### §6 documents
`VALIDATION_CONTRACT.md`, `DECISION_PACKAGE.md`, `USER_JOURNEY.md`, `CLAIMS_REGISTER.md`,
`DEMO_RUNBOOK.md`, `evals/README.md`, and this file.
