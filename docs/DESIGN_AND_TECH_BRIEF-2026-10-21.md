# Twin Trace — Design and Technical Implementation Brief

> **Repository note (added 2026-10-21):** stored verbatim as supplied in session. It is an input,
> not a spec. Only a cut-down subset is adopted: TASKS.md Week 4c (T7.1–T7.4) and DECISIONS.md
> 2026-10-21 "Adopt a cut-down subset of the design and technical implementation brief". Some
> findings in §2 were already fixed before it was stored: `run_to_draft` failure propagation, and
> Tavily failure vs zero-hit outcomes (see HANDOFF.md §5e).

**Prepared:** 21 October 2026  
**Repository:** `/Users/nikhil/Hackathons/twin-trace`  
**Status:** Proposed implementation plan for team agreement. No application changes made by this brief.  
**Purpose:** Make the project's potential impact and distinctive idea demonstrable through a trustworthy user journey and enforceable technical behavior.

## 1. Product outcome and scope

Enable an officer to inspect an alert, understand the supporting and conflicting evidence, prepare a rationale, and record a decision whose supporting material can be reconstructed later.

The central product principle is: **The model may propose an explanation; the application must check the evidence used to support it.** This is a design goal, not a statement that the current implementation enforces every factual claim.

Make these three outcomes visible:

1. **Traceable figures:** a reviewer can follow an amount to its calculation and source transactions.
2. **Challengeable conclusions:** a reviewer can see which modeled assumptions change the signal result, alongside evidence the sensitivity analysis cannot evaluate.
3. **Reconstructable decisions:** a reviewer can retrieve the exact inputs, rationale, validations, and versions used at recording time.

Preserve Streamlit, SQLite, the existing calculator, bounded investigator, corpus retrieval, and ledger. Add narrowly scoped services and views rather than replacing the architecture. Do not add autonomous regulatory filing or customer messaging.

## 2. Evidence baseline and corrections to earlier assessments

The prior audit executed 80 passing pytest tests, 24 passing checks in the original evaluation harness, 23 passing checks and one skip in the second harness, and the calculator demonstration through its module entry point. These are historical audit observations; rerun after changes.

The committed live report describes 16 synthetic alerts, 12/12 agreement on clear cases, and ten rejected agent submissions. These are recorded results, not independently repeated live calls in this audit. Ten rejections do not establish ten prevented harmful decisions or ten distinct hallucinations.

The current source recheck identifies issues that must qualify the earlier positive assessment:

| Finding | Evidence location | Consequence |
|---|---|---|
| UI shows hard/policy gate failures, but recording checks only officer ID and rationale length; backend recorder does not rerun evidence validation | `app.py::_decision_rail`, `ddp/skills.py::alert_disposition_recorder` | A warning is not an enforced recording barrier |
| Monetary validator recognizes a restricted rupee syntax, permits approximately 1% differences, and computes credit/debit totals outside the calculator | `ddp/skills.py::validate_gos_evidence` | “Every rupee proven” overstates current coverage |
| Pipeline can continue after dependency failures and returns `blocked=False` after later gate failures | `ddp/pipeline.py::run_to_draft` | Callers can misinterpret a failed run as usable |
| Assessment exceptions are converted into fallback factor records; evaluation runner labels a non-throwing call valid | `ddp/skills.py::suspicion_evaluator`, `scripts/run_live_eval.py` | Reported schema success may include fallback outputs; inspect raw evidence before repeating the 16/16 claim |
| Compute records contain hashes and output, but not the complete original input payload; reconstruction uses current transactions/parameters | `ddp/compute/runner.py`, `app.py::_reconstruct_view` | Hashes detect differences but do not recover missing historical inputs |
| Agent validates numerical membership and supplied citation IDs, not full semantic support for each statement | `ddp/agent.py::_tool_submit_assessment` | A correct number can still be attached to an incorrect assertion |
| Adverse-media search derives tokens from profile descriptions; errors and zero hits both become empty results | `ddp/evidence/tavily.py` | Irrelevant results or failed screening can appear reassuring |
| Sandbox selection omits the key in the inspected construction path | `ddp/bootstrap.py::build`, `ddp/compute/runner.py::backend_from_name` | An implemented backend is not an operational integration |

Treat repository plans and PROVEN labels as claims requiring supporting tests or run artifacts. The earlier audit's claim that a README command for `demo_caught_it.py` was wrong was too broad: the inspected README did not list that command. Direct script invocation failed, while module invocation passed; document the supported module command.

## 3. Proposed user journey

**Queue → inspect evidence → challenge assumptions → draft/review → validate current text → confirm decision → reconstruct.**

### D1. Evidence-first case workspace — P1

**Owner:** Design/frontend. **Estimate:** 6–10 engineering hours. **Depends on:** shared case/validation state contracts below.

- Start with case identity, observed pattern, missing information, and available source evidence.
- Put drafting and decision actions after evidence review in reading and keyboard order. On wide screens, a secondary column may hold supporting material; on narrow screens, stack evidence, sensitivity analysis, draft, then decision controls.
- Keep the current separate investigator and assessment capabilities, but explain their roles. Default to one recommended assessment route; show alternate analysis under an optional section to prevent redundant calls and conflicting unexplained recommendations.
- Separate source facts, model interpretation, product heuristics, and officer conclusions with text labels. Do not rely on color alone.
- Replace ambiguous model/provider checkmarks with `Configured`, `Last call succeeded`, or `Unavailable`, including timestamp where applicable.
- Display synthetic-data status near the case title. Avoid a product name implying regulatory endorsement.

**Acceptance:** A first-time reviewer can locate the source evidence, uncertainty, and next action without running an AI call. At 390px, 768px, and 1440px, primary controls remain reachable; figures are readable; keyboard navigation follows the logical workflow. Test the narrow layout with the sidebar both open and closed before diagnosing a layout defect from a cropped screenshot.

### D2. Inspectable claims — P1

**Owner:** Frontend + backend. **Estimate:** 6–10h. **Depends on:** T1/T2.

For each structured monetary claim show its value, meaning, source, and validation state. Expand to reveal supporting transaction IDs, deterministic derivation, calculation run, and exact units. Keep hashes in technical details; default to an explanation an officer can use.

Use distinct labels: `Verified calculation`, `Source assertion`, `Assumed rule`, `Unverified external source`, `Unsupported claim`. A verified calculation means it matches the recorded inputs; it does not establish that those inputs are true.

**Acceptance:** Selecting a total reveals the exact source rows and calculation. A wrong amount, wrong unit, or incompatible citation cannot display as verified. Editing the draft immediately invalidates its previous validation badge.

### D3. Decision sensitivity view — P1

**Owner:** Design + backend. **Estimate:** 4–6h. **Depends on:** existing stress engine; T5 for stronger examples.

Present: the modeled signal result; the assumption changed; the resulting signal change; the evidence needed to verify that assumption; and what the analysis does not cover. Show search budget exhaustion and incomplete coverage explicitly.

Say `This change lowers the modeled signal level`, not `This proves you should close the case`. Existing minimal flip sets are minimal within the implemented hypothesis search and budget. A proposed reopen trigger is advisory until reviewed; do not imply monitoring or automatic reopening exists.

**Acceptance:** ALERT-01 and ALERT-16 illustrate different reasoning with source-linked explanations. A narrative-dependent case explains why the calculator cannot establish its disposition. No LOW signal is presented as proof of innocence.

### D4. Recording and reconstruction — P0/P1

**Owner:** Frontend + backend. **Estimate:** 5–8h. **Depends on:** T1/T3.

- Rename `FILE STR` to an accurate local action such as `Record decision to file`; distinguish intent from an externally completed filing.
- Before saving, show exact rationale, disposition, officer identifier, validation results, acknowledged uncertainties, and any external filing reference.
- Label a missing reference as pending; do not represent a placeholder as an actual regulator receipt.
- Show a confirmation step. Prevent duplicate records from repeated clicks.
- Present the recorded decision as a read-only snapshot with source evidence and a reproduction action. State that an entered officer ID is self-asserted unless authentication exists.

**Acceptance:** Stale validation cannot authorize a changed draft. Repeated submission creates one decision. A historical decision remains inspectable after operational source data changes. Recording a decision never claims to transmit a regulatory report.

## 4. Technical work packages

### T1. Enforce validation at the recording boundary — P0

**Owner:** Backend. **Estimate:** 8–12h.

Introduce one recording service used by all UI/API entry points. Revalidate the final rationale against the selected case and exact evidence snapshot immediately before committing. Bind validation to draft hash, case ID, input hash, policy version, and calculator run ID. Reject stale, mismatched, missing, or failed hard validation.

Keep hard factual failures distinct from uncertainty and advisory model judgments. A human can disagree with an AI recommendation and explain why; that does not authorize an unsupported amount. An unvalidated draft or deferral note may be retained with an explicit non-final status, but must never appear as a validated final decision.

Do not blindly turn the existing regex policy gate into a universal blocker: it currently treats internal report references as possible tipping-off language. Define policy scope by output audience and have domain policy reviewed. Keep unsupported legal claims out of UI explanations until verified.

Make ledger append, status transition, and validation linkage transactional. Generate an idempotency key for the reviewed draft and action. Store validation outcomes and any human override of advisory recommendations.

**Tests:** Direct recorder calls with unsupported money fail; valid text edited after validation fails; another alert's compute run fails; policy checks cover manually written drafts; double-click/retry does not duplicate; transaction failure leaves no partial decision. All must run offline.

### T2. Strengthen claim validation — P0

**Owner:** Backend/AI. **Estimate:** 8–14h.

- Normalize supported monetary forms (`₹`, `Rs.`, INR, Indian commas, decimal lakh/crore notation) into exact decimal/minor-unit values. Define supported formats explicitly and flag unparsed monetary expressions.
- Eliminate silent approximate matching for verified claims. If display rounding is allowed, record an explicit rounding rule and preserve the exact underlying amount.
- Require aggregate claims to reference a recorded calculator fact. Do not recreate unproven totals inside the validator.
- Bind claims to meaning, unit, source IDs, and calculation run; matching any number anywhere in a case is insufficient.
- Validate factor-ID uniqueness/completeness and citation existence. Schema-valid arrays with duplicated factors must fail semantic validation.
- Reject empty or non-substantive agent rationales; require the needed evidence retrieval. Apply policy checks to accepted agent assessments as well as drafted narratives.

Prefer a small structured claim list plus readable prose to an unbounded natural-language fact-checking project. Classify free-text assertions outside deterministic coverage as needing human review. Never claim complete factual verification from regex or numeric membership alone.

**Tests:** Equivalent supported currency formats normalize consistently; invented lakh values fail; right value/wrong beneficiary and right value/wrong unit do not verify; invented citations fail; duplicate factors fail; unsupported prose is visibly outside verified coverage.

### T3. Preserve a reconstructable decision package — P1

**Owner:** Backend. **Estimate:** 6–10h.

Store canonical calculation inputs and parameters with their hashes, plus program version/source artifact reference, output, corpus entries used, final rationale, claim map, validation results, evidence references, model-call metadata, and the officer's decision. Preserve source snapshots; mutable operational rows are not historical evidence.

For synthetic demo data, a versioned local package is sufficient. Do not export credentials, raw hidden reasoning, or unrelated records. Add a package manifest and offline verifier. Call it tamper-evident and explain the trust boundary: a hash chain in the same mutable database is not independent authenticity proof.

Update reproduction to use saved inputs and verify **input, code, and output hashes**. If the required program version is unavailable, say reproduction is unavailable rather than asserting success from current code.

**Tests:** Changing operational data does not change the exported historical package; altered package content fails verification; input mismatch cannot show success; clean-process verification works without an API key.

### T4. Make failures and model usage explicit — P0/P1

**Owner:** Backend/AI. **Estimate:** 6–10h.

- Use common step states: not run, running, succeeded, failed, blocked, skipped. Keep legitimate abstention distinct from provider failure.
- Stop dependent pipeline steps after a failed prerequisite. Propagate blocked status to callers. A failed quality check means unavailable/review required, not a passing score.
- Record every model attempt, repair, and provider failure. Aggregate tokens and elapsed time across attempts; do not retain only the final call. Save requested/reported model and finish reason.
- Diagnose complex-case output exhaustion using recorded finish reason and output length. Compare prompt shortening and token allowance before changing model tiers; select a tier through measured quality/latency tradeoffs.
- Bound elapsed time and tool-call count as well as agent rounds. Handle tool exceptions with structured error results; preserve partial evidence and avoid duplicate external calls when retrying.
- Connect agent run/evidence references to a decision when used. Mark advisory runs that were not used.

**Acceptance:** Fault injection for timeout, 429, malformed JSON, truncation, and calculator failure produces accurate visible states. A reviewer can retry an appropriate failed step without losing the draft. No automatic fallback is claimed unless implemented and exercised.

### T5. Demonstrate value with a reliable evaluation — P1

**Owner:** AI/evaluation. **Estimate:** 8–12h, excluding external review turnaround.

Fix the evaluation runner first: inspect structured validation and fallback status, not just whether the call threw. Report successful model output, repaired output, legitimate abstention, fallback, and failure separately. Save sanitized raw outputs and validation verdicts needed to audit those classifications.

Use the existing scenarios as development tests. Add a small frozen holdout set with transaction-level evidence, explicit expected outcomes, ambiguity notes, and label provenance. Do not call author-assigned labels expert ground truth. Include supported amounts used in false assertions, fabricated evidence, conflicting sources, sparse data, and benign cases resembling suspicious ones.

Compare three conditions using the same cases and input information:

1. Structured manual template plus deterministic calculator.
2. Same model producing a draft without the project's validation controls (evaluation only).
3. Full application with validation and decision review.

Measure unsupported claims per draft, gate catch rate on deliberately seeded faults, false rejection rate on supported claims, reviewer corrections, end-to-end latency, all-attempt token use, and whether evidence reconstruction succeeds. Measure review time only with actual participants; do not substitute model latency for officer time saved.

**Acceptance:** A malformed response cannot increase schema-success counts. Reports include denominator, dataset version, code revision, model versions, raw evidence, and failure breakdown. Contested cases have a separate analysis. Any claimed improvement is measured against the stated baseline, with sample-size limitations.

### T6. Make external evidence useful and interpretable — P1 if Tavily is retained in the demo

**Owner:** Backend + design. **Estimate:** 4–8h.

Replace first-word extraction from a customer profile with explicit synthetic entity identity fields or a clearly labeled topic search. Require entity-match review before treating a news item as case evidence. Display query, provider, retrieval date, source URL, and match uncertainty.

Return distinct outcomes for unconfigured, failed, successful zero hits, and successful hits. Do not interpret zero hits as exoneration. Treat source text as untrusted throughout model and tool flows; include adversarial snippets in tests. Regulator search results remain pointers until verified and incorporated through a reviewed corpus update.

**Acceptance:** A synthetic entity search yields an auditable runtime trace or an explicit failure. Wrong-entity results cannot silently enter the verified claim set. The final evaluation must actually inject the Tavily adapter if it claims to test Tavily integration.

### T7. Deployment and optional infrastructure — P0/P2

**Owner:** Release/backend. **Estimate:** 4–8h for deployment verification; sandbox proof is optional and separately timeboxed.

Pin a tested dependency set and Python version. Test a fresh environment and persistent storage behavior. For a public synthetic demo, isolate visitor sessions/cases, limit expensive calls, and ensure one visitor cannot rewrite another visitor's working state. Verify restart behavior and give judges a clear no-key/offline limitation if relevant.

Use the existing Token Factory runtime integration as the required platform path. Add sandbox execution only after T1–T5 are stable: pass credentials correctly through backend construction, implement an actual timeout, run the same inputs locally/remotely, and compare canonical outputs with a recorded remote run reference. A sandbox proves execution isolation, not factual truth or regulatory correctness.

**Acceptance:** Clean install and hosted main journey work; provider secrets stay server-side; session isolation is exercised; persisted decisions survive a normal restart. Sandbox claims appear only after an actual successful probe.

## 5. Delivery order and scope cuts

Estimates above are planning estimates for focused engineering hours, not commitments. Tasks overlap; do not add every row and assume the full list fits the remaining window.

| Milestone | Required work | Exit condition |
|---|---|---|
| 1. Trust boundary | T1, core T2, failure propagation in T4 | Unsupported/stale drafts cannot become validated final decisions |
| 2. Demonstrable workflow | D1–D4, T3 | Reviewer can inspect, challenge, record, and reconstruct one complete case |
| 3. Credible evidence | T5, remaining T4, T6 if shown | Results distinguish success/fallback/failure and support the demonstrated claims |
| 4. Release rehearsal | T7, documentation, video | Fresh install and hosted walkthrough produce the documented result |

Work can proceed in parallel within the team after agreeing on validation and snapshot contracts: frontend owns D1–D4, backend owns T1–T3, evaluation owns T5, and release owns T7. Integrate a thin end-to-end case before polishing every panel.

Suggested budget envelopes: **minimum 24–36 team-hours** for enforced recording, supported monetary parsing, corrected evaluation classification, a readable primary journey, and release verification; **recommended 48–72 team-hours** adds historical packages, richer claim linkage, holdout comparisons, and external-evidence clarity; **ambitious 80–110 team-hours** adds broader adversarial testing, practitioner feedback, and verified sandbox execution. These scenarios reduce scope within work packages; they do not imply all listed work is completed in the minimum plan.

Drop optional sandbox work, model-based policy expansion, extra dashboards, and visual embellishments first. Preserve enforced validation, accurate failure states, evidence reconstruction for the demo case, and honest evaluation.

The deadline previously verified was **30 October 2026 at 22:30 IST**. Confirm the current deadline on the [official rules](https://nebiusglobalaihackathon.devpost.com/rules) before scheduling release, and reserve the final day for rehearsal and submission contingencies. No new deadline verification was performed for this brief.

## 6. Required documentation and evidence

Every implemented work package must include its source changes, targeted regression evidence, limitations, and a documentation update. Suggested files in the implementation repository:

| Document | Required contents |
|---|---|
| `docs/DESIGN_AND_TECH_IMPLEMENTATION.md` | Accepted scope, owners, decisions, dependency order, completion status |
| `docs/VALIDATION_CONTRACT.md` | Claim types, supported formats, hard failures versus advisory uncertainty, stale-state handling, policy audience |
| `docs/DECISION_PACKAGE.md` | Snapshot schema, trust boundaries, versioning, export and offline verification instructions |
| `docs/USER_JOURNEY.md` | Queue-to-reconstruction flow, responsive screenshots, empty/loading/error states, accessibility checks |
| `evals/README.md` | Dataset split, label provenance, baseline definitions, commands, metric definitions |
| `evals/RUN-<timestamp>/` | Dataset/config hashes, revision, sanitized outputs, validation results, metrics and failure analysis |
| `docs/CLAIMS_REGISTER.md` | Each public claim, supporting run/test, exact scope, limitations, approval owner |
| `docs/DEMO_RUNBOOK.md` | Three-minute sequence, expected outputs, failure handling, links and reset procedure |

Use this completion record for every task:

```markdown
### <Task ID>: <Title>
- Owner:
- Status: planned / in progress / implemented / verified / deferred
- Revision or PR:
- Behavior before and after:
- Acceptance criteria checked:
- Test/run artifact:
- Screenshots, if UI changed:
- Known limits and unresolved issues:
- Public claims now supported:
```

Keep README, architecture notes, handoff notes, and claims register consistent. Remove stale “stubbed” labels after verification and stale “proven” labels when their scope is not supported. A configuration file is not proof of hosting; schema validity is not decision accuracy; successful hashing is not semantic correctness.

## 7. Final demonstration and acceptance

Use ALERT-01 and ALERT-16 as development anchors, then show at least one held-out example. The demonstration should establish these observable behaviors:

1. The reviewer sees a case and source transactions before any conclusion.
2. A plausible unsupported monetary claim is rejected at the actual recording boundary.
3. A supported replacement links to the exact calculation and transactions.
4. Sensitivity analysis explains a modeled change and its coverage limits.
5. The human records a reviewed local decision with a pending/actual external filing state clearly distinguished.
6. Another reviewer opens the historical package and verifies its recorded inputs and calculations.

**Release gate:** No unresolved bypass of hard validation; no stale READY state after edits; no fallback counted as model success; no current-input substitution labeled historical reproduction; no simulated external call presented as live. Proposed acceptance conditions become achieved results only after the team records the corresponding evidence.

## 8. First implementation session

1. Agree on T1's recording contract and the distinction between final decisions and unvalidated notes. Reproduce the warning-only recording path in a disposable test database.
2. Add regression tests for recording bypass, edited drafts, alternate currency notation, and fallback misclassification. Implement the smallest fixes that make those tests pass.
3. Connect one evidence-first case view to the enforced service, then record a short walkthrough before expanding the implementation scope.
