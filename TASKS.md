# TASKS.md — build plan to submission

The deadline is **Fri 30 Oct 2026, 22:30 IST**. The internal target is **Wed 28 Oct**, and
feature freeze is **Fri 23 Oct**.

`[ ]` open · `[x]` done · `[~]` in progress · **(H)** = human-only step (accounts, keys, legal,
recording).

## Week 0 — split and port (Sep 27) ✅
- [x] T0.0 Separate repo; baseline import commit + tag; platform-neutral port; offline gate green

## Week 1 — Sep 27 → Oct 3: go live on Nebius, de-risk the sandbox
- [ ] T0.1 **(H)** Claim the $25 Token Factory credit (code NEBIUS-DEVPOST-GLOBAL26), join the Builders Program for the second $25, and apply to the AI Builder Program.
- [ ] T0.2 **(H)** Create `.env` from `.env.example` with `NEBIUS_API_KEY`
- [ ] T0.3 **(H)** Choose a licence (Apache-2.0 or MIT) → add `LICENSE`, make the GitHub repo public. Record the outcome in DECISIONS.md.
- [x] T0.4 `python -m scripts.check_models --ping`. All 3 tiers OK. URL api.tokenfactory.nebius.com confirmed. Reasoning token budget finding noted. DECISIONS.md updated 2026-10-21.
- [x] T1.1 Live-run 11-factor assessment. evals/REPORT-2026-10-21-live.md. *Correction 2026-10-21 (T7.3): the runner counted fallbacks as valid; likely 14/16 (ALERT-01, ALERT-04 fell back). Rerun before quoting.*
- [x] T1.2 Live-run GoS drafting: hard gate passes on grounded drafts, catches forced-wrong totals. F-DECLARED-INCOME fact added. max_tokens raised to 4096 for structured calls.
- [ ] T1.3 **Sandbox backend.** Read the Token Factory Sandboxes docs (overview, CLI `run`, API "spawn a new container instance") and implement `NebiusSandboxBackend.execute()`: upload the program, run it with the input on stdin, and return (stdout, sandbox run ID). Keep the local backend as fallback. Done when a real `BACKEND_RUN_REF` is in COMPUTE_RUNS and `reproduce()` matches across local and sandbox.
  - Note: snapshots are filesystem-only; beta forbids personal/sensitive data (ours is synthetic); networking is on by default (turn it off for this program if the API allows).
- [ ] T1.4 Add the multi-account structuring case: extend ALERT-02 seed transactions to daily cash rows per linked account (synthetic), so the monthly-aggregation facts are exercised on real seed data rather than just tests.

## Week 2 — Oct 4 → Oct 10: adverse media (Tavily) and the "caught it" moment
- [x] T2.1 Tavily adverse-media screening step for the subject and counterparties. Store the query, URLs, snippets and retrieval time as evidence; nothing is sent to the customer. **Live 2026-10-21** (`evals/TAVILY-PROBE-2026-10-21.md`); failures recorded as distinct statuses.
- [x] T2.2 Treat adverse-media hits as evidence rows with provenance in the Disposition Panel and the ledger.
- [x] T2.3 Demo case: the model's own arithmetic vs the calculator of record. Show a draft that states a wrong aggregate being blocked, then the corrected draft citing F-… facts. This is the video's opening beat.
- [ ] T2.4 UI: fact-citation chips inline in the GoS preview (hover → derivation + txn IDs). *(cut list — plain citation line already exists)*

## Week 3 — Oct 11 → Oct 17: policy gate and evaluation
- [x] T3.1 Nemotron Content Safety (custom policy) gate — DeterministicPolicyGate (regex, always-on) PROVEN; NemotronContentSafetyGate STUBBED (falls back to deterministic). Live model → pending T0.4.
- [x] T3.2 Eval harness v2 over the 21 scenarios: gate catch rates, abstention precision, calculator gate end-to-end, evidence store round-trip. 23/26 offline; 3 SKIP (live model). Committed 2026-09-28.
- [x] T3.3 Ledger "reconstruct decision" view: from a DECISION_ID, show the compute run (reproduce button), model calls and the corpus rules cited.
- [x] T3.4 Make `str_quality_checker` fail closed on unparseable model output.

## Week 4 — Oct 18 → Oct 23: product polish and deploy (FREEZE Fri Oct 23)
- [x] T4.1 Investigator-flow UI polish: adverse-media panel, policy gate verdict, reconstruct view, token usage tracker on Dashboard.
- [x] T4.2 Hosted demo config: `.streamlit/config.toml` with theme + security settings; seeded synthetic data via `scripts/seed_db.py`.
- [x] T4.3 README final: architecture, exactly where Token Factory and Nemotron are used and why, the "significantly updated" section (from CHANGES_SINCE_BASELINE.md), eval results with dates, and limitations.

## Week 4b — Oct 20: differentiators (added this session; offline parts done)
- [x] T6.1 Decision Stress Test (`ddp/stress/`, UI section, tests)
- [ ] T6.2 Agentic investigator — offline done; **live run on ALERT-01/16 with Nemotron Super** (needs key). Check tool-call argument format and the `""` → `{}` normalisation on the real endpoint.
- [x] T6.3 Regulator-only Tavily — live 2026-10-21: 5 rbi.org.in hits; case-identifier refusal sends nothing.
- [x] T6.4 Structured output v2 (object wrappers + local validation + json_schema fallback)
- [ ] T6.5 `python -m scripts.run_live_eval` live → commit `evals/REPORT-<date>-live.md`; only then quote numbers
- [ ] T6.6 Richer seed transactions for FILE alerts with one summary row (ALERT-05/06/09/12/15) so the calculator and stress test see the pattern — needs a domain check by the human (synthetic only)

## Week 4c — Oct 21 → Oct 23: trust boundary (cut-down from the 2026-10-21 design brief)
Priority: **P0** = blocks the core claim, do before freeze · **P1** = do before freeze if P0 done ·
**P2** = small, only if time. Do them in this order. See DECISIONS.md 2026-10-21 "design brief".
- [x] T7.1 **P0** Close the currency-format bypass *(done 2026-10-21; also applied to the agent submission check and the stress memo)* in `validate_gos_evidence`. Today only `₹<digits>`
  is checked: `Rs. 32,50,000`, `INR 3250000` and `₹32.5 lakh` (invented, ALERT-01) all pass.
  Parse ₹ / Rs. / INR, Indian commas, lakh / crore, into exact integer rupees; remove the silent
  ±1% match; aggregates must cite a calculator fact (no totals recomputed in the validator); any
  monetary expression the parser cannot read fails the gate. Done when tests show the four forms
  above normalise identically, invented figures fail in every form, and the existing gate and
  demo tests still pass. ~3–4h.
- [x] T7.2 **P0** Enforce the hard gate at the recording boundary. *Done 2026-10-21; applies to every disposition; aggregate-without-run check waits on T7.1 (strict xfail in `tests/test_recording_gate.py`).* `alert_disposition_recorder`
  re-runs `validate_gos_evidence` on the final rationale against the alert's transactions and
  the cited `compute_run_id` (which must belong to that alert), and refuses FILE with an
  unsupported figure. Rename the UI action "FILE STR" → "Record decision to file"; a missing STR
  reference is shown as pending, never as a receipt. Done when a direct recorder call with an
  unsupported amount, or with another alert's run ID, raises and writes no ledger row. ~3h.
  Policy-gate enforcement stays advisory here (open `tipping_off_str` question).
- [x] T7.3 **P1** Fix live-eval classification. *Done 2026-10-21 (code + offline tests); live rerun not yet done.* `run_live_eval.py` marks an assessment "valid"
  whenever the call does not throw, but `suspicion_evaluator` returns fallback records instead
  of throwing. Report success / repaired / fallback / failure separately; re-check
  `evals/REPORT-2026-10-21-live.json` (or rerun) before quoting 16/16 again. Done when a fallback
  cannot count as success (offline test with an injected unparseable model). ~2h.
- [x] T7.4 **P2** Pass the API key through `bootstrap.build()` → `backend_from_name(...)`; today the
  sandbox backend is constructed without it. Prerequisite for T1.3; no sandbox claim from this. ~0.5h.

Deferred from the brief (not before submission unless all of the above are done): evidence-first
workspace redesign (D1), inspectable claim chips / claim map (D2, cf. T2.4), sensitivity-view
rewording (D3), confirmation step + idempotent recording (rest of D4), reconstructable decision
packages storing full inputs (T3), all-attempt model accounting + fault injection (rest of T4),
holdout set and three-condition comparison (rest of T5), entity-based adverse-media search (T6),
session isolation for the hosted demo (rest of T7 in the brief — revisit when deploying).

## Week 4d — Oct 21: rest of the design brief (done at the human's request)
- [x] T8.1 Brief T1 rest — draft-hash binding, idempotency, atomic write, disclosure block at recording
- [x] T8.2 Brief T2 rest — claim map, factor uniqueness, citation existence, agent rationale rules
- [x] T8.3 Brief T3 — saved inputs, program archive, decision package + offline verifier
- [x] T8.4 Brief T4 rest — all-attempt accounting, error kinds, truncation, agent budgets
- [x] T8.5 Brief T6 rest — typology topic search, Tavily injected in eval
- [x] T8.6 Brief T7 rest — constraints.txt, demo-mode isolation + budget, Dockerfile *(Docker build not tested)*
- [x] T8.7 Brief D1–D4 — evidence-first panel, figure panel, sensitivity wording, confirmation step
- [x] T8.8 Brief T5 rest — holdout v1, comparison harness, live runs (see CLAIMS_REGISTER)
- [x] T8.9 Brief §6 documents
- [ ] T8.10 **(H)** Update `.github/workflows/ci.yml` (read-only) to run `python -m pytest -q` so the new suites run in CI
- [ ] T8.11 **(H)** Review holdout labels in `evals/holdout/HOLDOUT-v1.json` (author-assigned)
- [ ] T8.12 **(H)** Decide the `tipping_off_str` audience question (open since 2026-10-21)

## Week 4e — Oct 21: four-criteria improvement plan (approved by the human)
Source: the 2026-10-21 pre-submission audit. The human owns git (no commits/pushes from Claude),
the video, the deck, the licence and hosting. Everything else below is Claude's.
- [x] T9.1 (A3) Wire `DispositionPipeline` step methods into `app.py` with one shared `RunTrace` per alert + a visible run-trace panel
- [x] T9.2 (A4) `.github/workflows/ci.yml` running the full offline gate on Python 3.11 with `constraints.txt` *(written 2026-10-21; not yet run on GitHub; the human reviews and pushes)*
- [~] T9.3 (A1) Live sandbox probe. **Blocked on a Nebius project ID (human):** backend corrected to the real SDK and the endpoint reached, but no run completed. Add `NEBIUS_PROJECT_ID` to `.env`, then `python3 -m scripts.probes.probe_sandbox`; record a real `BACKEND_RUN_REF` and local↔sandbox agreement
- [x] T9.4 (A2) One clean live rerun of `run_live_eval`, committed under a new dated name; README quotes exactly that file
- [x] T9.5 (C1) In-app decision-package verifier (never executes package-supplied code)
- [x] T9.6 (C2) Stress test headline in plain language ("this FILE rests on exactly one fact …")
- [x] T9.7 (D4) "Proof check" page: a wrong figure blocked, then the corrected draft passing; works offline
- [x] T9.8 (D2/D3) Cold-start hero + "What am I looking at?" + glossary
- [x] T9.9 (D5) Accessibility pass (contrast, labels, keyboard order, reduced reliance on colour)
- [x] T9.10 (B1) Measured-evidence view in the app reading the committed holdout/live reports
- [x] T9.11 (B2/B3/C3) `docs/IMPACT.md` with sourced problem-sizing and a labelled generalisation note; README thesis tightened
- [ ] T9.12 Hosted demo (D1) — **PENDING by the human's decision**
- [ ] T9.13 (H) Licence (T0.3), git history/baseline tag, video, deck — human-owned

## Week 4f — Oct 22: judging pass (`docs/BUILD_PROMPT_JUDGING.md`, approved by the human)

- [x] T10.0 Phase 0 audit → `docs/JUDGING_AUDIT.md` (reviewed by the human 2026-10-22)
- [x] T10.1 Phase 1 Verdict card on the Disposition Panel (both readings, option (b)); evidence and AI behind "Show the proof"
- [x] T10.2 Phase 2 Twin Cases page (ALERT-01 vs ALERT-16) + "Start here" entry on the Alert Queue
- [x] T10.3 Phase 3 Impact: stakes strip with corpus rule-ID chips (STR-002, INS-001, INS-002, SB-003) + test; fix Dashboard caption
- [x] T10.4 Phase 4a Platform trace strip (tier → model → tokens → seconds; compute backend shown honestly)
- [ ] T10.5 Phase 4b Sandboxes probe — only if Nebius grants access
- [x] T10.6 Phase 5 README/video script/Limitations — README aligned; script in `docs/DEMO_RUNBOOK.md`; Devpost draft with Limitations and platform-feedback facts in `docs/DEVPOST_DRAFT.md` (human edits, records and submits: T5.1–T5.3)

## Week 5 — Oct 24 → Oct 30: story and submission
- [ ] T5.1 **(H)** Video (≤2:50). 0:00–0:30 the calculator catching a wrong figure → 0:30–1:30 the full disposition with tiered Nemotron → 1:30–2:10 tipping-off block + ledger chain verify → 2:10–2:50 eval table, spoken mention of Token Factory, the models and Sandboxes.
- [ ] T5.2 Devpost text + substantive platform feedback (separate $100 prize)
- [ ] T5.3 **(H)** Submit by Wed Oct 28. Oct 29–30 is buffer only.

## Cut order if behind (cut from the top)
1. T2.4 inline chips → plain citation line (already exists)
2. T3.1 hosted Content Safety → documented fallback
3. T1.4 richer structuring seed
4. T3.3 reconstruct view

Never cut: T0.4, T1.3 (or an honest "local only" statement), T2.1, T3.2, T5.x, T7.1, T7.2.
