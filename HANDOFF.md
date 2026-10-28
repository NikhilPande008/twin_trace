# HANDOFF.md — current state

**Updated:** 2026-10-22 (BUILD_PROMPT_JUDGING pass complete except 4b; light/dark themes, §5o)
**Next session starts at:** human-owned submission work: restore the baseline tag/history, make the
repo public (MIT `LICENSE` is merged), rehearse and record the video from `docs/DEMO_RUNBOOK.md`,
edit and submit `docs/DEVPOST_DRAFT.md`. Phase 4b (Sandboxes probe) only if Nebius grants access.
**Offline gate:** 443 pytest green, eval_harness 24/24, eval_harness_v2 definitive checks pass, demo_caught_it passes.

## 5o. Light and dark themes on design tokens (2026-10-22)

- Two themes, switched by the viewer in the app menu (⋮ → System / Light / Dark):
  `[theme.light]` / `[theme.dark]` in `.streamlit/config.toml`. Light = the implementation brief's
  tokens; dark = derived values (PROPOSED, DECISIONS.md 2026-10-22).
- Custom HTML follows the switch in the browser: palette roles are CSS variables defined as
  `light-dark(<light>, <dark>)` on `.stApp`. `app.py` has no raw colours (a test enforces it).
- `tests/test_accessibility.py`: every pair ≥ 4.5:1 in both themes, button fill vs white text,
  both config sections equal the palette. Checked in the running app: both themes, live switch,
  computed colours match the palette, no server errors. No screen-reader pass.
- **Not done / to know:** `light-dark()` needs a 2024+ browser (Chrome 123, Safari 17.5, Firefox
  120). A running app must be restarted to pick up `config.toml`.
- Changed: `ddp/palette.py`, `app.py`, `.streamlit/config.toml`, `tests/test_accessibility.py`.

## 5n. Judging pass Phase 5 — submission material (2026-10-22)

- README: Twin Cases and both readings in the story; platform trace; Sandboxes now "not run
  (blocked, 403)" everywhere, and "is written to run" instead of "runs"; story quotes the final live
  report (16 rejections across 12 alerts) instead of the earlier one (10); new limits (agent filing
  lean, twins' labels, ALERT-16 ELEVATED, self-asserted officer ID).
- `docs/DEMO_RUNBOOK.md` rewritten as the video script: Alert Queue → Twin Cases → verdict card →
  proof → live assessment + platform trace → agent on ALERT-02 (rejections in both dated runs;
  ALERT-07 backup; Proof Check carries the rejection if neither shows one) → Proof Check → dated
  results. 299 spoken words.
- `docs/DEVPOST_DRAFT.md` (new): all sections, Limitations, the "significantly updated" statement
  (flags the missing baseline tag), and platform-feedback facts for the human to write up.
- `docs/CLAIMS_REGISTER.md`: Sandboxes row corrected to BLOCKED (403); rows for both readings, twin
  cases, platform trace and stakes.
- Not done: video, deck, final Devpost text, platform feedback in the human's words.

## 5m. Judging pass Phase 4a — platform trace (2026-10-22)

- Strip under the verdict card: triage/reasoning/disposition with the reported model, calls,
  tokens, seconds for this alert; per-call table in an expander; calculator backend from provenance
  and the Sandboxes 403 status. Built from recorded calls only.
- Live status panels for the stress test (branch runs, then memo) and the agent (each step, tool,
  rejection); spinners for assess/draft/re-check name the model.
- Live check 2026-10-22: one stress-test memo call recorded as triage, Nemotron Nano, 2,095 tokens,
  16.8 s. Assessment, draft and agent paths verified only with a scripted model (to save credits).
- Changed: `ddp/platform_trace.py` (new), `tests/test_platform_trace.py` (new), `app.py`,
  `ddp/stress/engine.py`, `ddp/agent.py`, `tests/test_agent.py`, `tests/test_app_pipeline.py`,
  `tests/test_app_smoke.py`, `TASKS.md`, `CHANGES_SINCE_BASELINE.md`, `DECISIONS.md`, `HANDOFF.md`.

## 5l. Judging pass Phase 3 — stakes (2026-10-22)

- Alert Queue: "Who this is for / What is at stake" card with STR-002, INS-001, INS-002, SB-003
  (levels read from the corpus), what the tool does about each, and an expander with the rule text
  and source. Intro collapsed by default. Dashboard caption corrected (INS-003).
- No impact numbers in the app (CLAUDE.md §5); they stay in `docs/IMPACT.md` for README/video.
- New guard test: no NEEDS-VERIFICATION or unknown corpus rule ID in UI source.
- Changed: `ddp/stakes.py` (new), `tests/test_stakes.py` (new), `app.py`, `tests/test_app_smoke.py`,
  `TASKS.md`, `CHANGES_SINCE_BASELINE.md`, `DECISIONS.md`, `HANDOFF.md`.

## 5k. Judging pass Phases 1–2 (2026-10-22)

- **Verdict card** at the top of the Disposition Panel: both readings (human chose option (b)),
  deterministic, no memo, instant. Evidence + AI behind a "Show the proof" toggle, order unchanged.
- **Twin Cases** page + "Start here" box on the Alert Queue; intro's three-minute path now starts there.
- `ddp/verdict.py` (pure, from stress reports only); headline bug fixed for closures against HIGH
  signals; saffron accent + card surface in the palette, contrast-tested.
- Checked in the running app at 1440×900 and 375×812; no console errors.
- **Not done / to know:** the AI assessment is now behind the toggle, so drafting with AI needs it
  on (rail caption says so). Viewing an alert writes its two readings' branch runs (DECISIONS
  2026-10-22). README "Try it" line updated; the rest of README and DEMO_RUNBOOK wait for Phase 5.
- Changed: `app.py`, `ddp/verdict.py` (new), `ddp/palette.py`, `ddp/stress/headline.py`,
  `tests/test_verdict.py` (new), `tests/test_app_smoke.py`, `tests/test_app_pipeline.py`,
  `tests/test_accessibility.py`, `tests/test_stress_headline.py`, `README.md`, `TASKS.md`,
  `CHANGES_SINCE_BASELINE.md`, `DECISIONS.md`, `docs/JUDGING_AUDIT.md`, `HANDOFF.md`.

## 5j. Judging audit — Phase 0 (2026-10-22)

- `docs/JUDGING_AUDIT.md` written. **Not yet reviewed by the human.** Scores (video-only judge):
  Design 2, Idea 3, Impact 2, Tech 3 (substance 4, visibility 2).
- Premises in `BUILD_PROMPT_JUDGING.md` that are out of date: live Token Factory/Nemotron is already
  PROVEN (2026-10-21 reports); Sandboxes is BLOCKED (403), not ASSUMED; the app has 7 pages; a stress
  headline already exists. Phase 4b reduces to the Sandboxes probe.
- Findings to act on in Phase 1/2: the verdict headline sits ~1,650 px down behind a click; with a key
  set, the stress test waits 25–35 s for a Nemotron memo though the deterministic run takes
  0.1–0.5 s (`app.py:902`, `with_memo=_llm_ready()`); the FILE/NOT_FILE radio defaults to FILE, so
  ALERT-16 shows "rests on any one of 3 facts" instead of reopen conditions unless the viewer flips
  it. ALERT-16 models ELEVATED, not LOW: the Twin Cases view must present proposed dispositions,
  not a system decision.
- Dashboard caption "Key metrics FIU-IND inspectors focus on" overstates (INS-003 is an internal
  governance metric); fix in Phase 3.
- Per the standing instruction, phase ends list changed files for the human; Claude does not commit.
- Changed this session: `docs/JUDGING_AUDIT.md` (new), `HANDOFF.md`.

## 0. This session (2026-10-20) — what changed

- **Decision Stress Test** (`ddp/stress/`): signals → verdict (HIGH/ELEVATED/LOW) from calculator
  facts only; counter-hypotheses run as hashed branch runs (`COMPUTE_RUNS.PARENT_RUN_ID`,
  `HYPOTHESIS_JSON`); minimal flip sets; reopen triggers; stored as `stress_test` evidence.
  ALERT-01 FILE rests on the I4C flag on handle C (flip size 1) or both flagged debits (size 2).
  ALERT-16 NOT_FILE reopens if the hospital, brother or father is flagged; not the sister.
- **Agent** (`ddp/agent.py`) + `TokenFactoryClient.chat()` with tools. Validated submission.
- **Structured output v2** (`ddp/structured.py`): fixes latent json_object-vs-bare-array bug.
- **Calculator**: `F-FLAGGED-INFLOW-SHARE-BP`, `F-INCOME-MULTIPLE-X10` (income parsed from KYC
  profile text by `bootstrap.parse_declared_monthly_income`; `compute_params(store, alert_id)`).
  Note: adding the income param changes INPUT_SHA256 for new runs; old runs reproduce only with
  their own recorded params.
- **Tavily regulator search** (`fetch_regulatory_updates`).
- **`scripts/run_live_eval.py`** (`--mock` works; live needs key). Mock finding worth knowing:
  only 1 of 9 gold-FILE alerts reaches HIGH on calculator signals, because most alerts are one
  summary transaction (T6.6).
- **UI**: stress-test section + agent trace panel on the Disposition Panel.
- **README** rewritten story-first.

## 1. Where things stand

- **Phase 1 complete.** Architecture analysis, critique, and target design are in
  `docs/ARCHITECTURE.md`. Implementation plan is `docs/IMPLEMENTATION_PLAN.md`.
  Platform verification stubs are in `docs/PLATFORM_NOTES.md`.
- Port interfaces (`ddp/ports.py`): LLMPort, ComputeBackendPort, EvidenceSourcePort,
  PolicyGatePort. Test fakes StaticEvidenceSource and PassthroughPolicyGate included.
- Pipeline skeleton (`ddp/pipeline.py`): RunTrace + StepResult + DispositionPipeline wrapping
  existing skill calls. No behaviour change. Steps ①–⑥ wired; adverse_media and policy_gate
  use stubs (StaticEvidenceSource, PassthroughPolicyGate) until T2.1 and T3.1.
- EVIDENCE table added to `ddp/store.py` schema (additive; `CREATE TABLE IF NOT EXISTS`;
  no rows written yet). `append_evidence`, `evidence_for_alert`, `get_evidence` methods added.
- 6 DECISIONS.md ADR entries added (Phase 1 architecture decisions, all PROPOSED).

- **Phase 2 partial (offline work complete; live verification blocked on NEBIUS_API_KEY):**
  - `ddp/llm.py`: `response_format` parameter added to `TokenFactoryClient.complete()` and the
    LLM Protocol. `json_object` mode is passed for all JSON-expecting skill calls.
  - `ddp/skills.py`: `_complete_json_array()` helper — calls with `response_format={"type":
    "json_object"}`, one repair retry on parse failure (adds `[repair prompt]` suffix), raises
    `ValueError` on double failure. `suspicion_evaluator` uses it and degrades to all
    `insufficient_data` on double failure. `str_quality_checker` uses it and **FAILS CLOSED**
    (all 10 items fail, quality_score=0, recommendation=REJECT) on double failure — T3.4 fix
    brought forward.
  - `ddp/compute/runner.py`: `NebiusSandboxBackend` now has a real implementation when
    `api_key` is provided (base64-encode program + one shell command + stdin=json). When
    `api_key=None` (default), still raises with "T1.3" (test `test_sandbox_backend_is_honest_stub`
    continues to pass).
  - `scripts/probes/probe_sandbox.py`: probe script to verify the sandbox end-to-end when the
    key is available.
  - `docs/PLATFORM_NOTES.md`: updated with researched JSON mode and Sandboxes SDK facts (ASSUMED
    until live probe).
  - Offline gate: `pytest -q` → **35 passed** (3 new); `eval_harness` → 8/8 scenarios (24 checks).

## 2. Claim status

| Capability | Status | Notes |
|---|---|---|
| Offline suites green | PROVEN | 80 pytest + 24 eval checks (2026-10-20) |
| Ledger append-only (DB triggers) + hash chain | PROVEN | tests edit/delete through raw SQL |
| Calculator of record, local backend, reproducible hashes | PROVEN | |
| Computed facts admissible in the hard gate, with fact-ID citations | PROVEN | |
| Retrieval abstains off-corpus; NV unreachable | PROVEN | heuristic threshold, see ddp/retrieval.py |
| UI pages render offline | PROVEN | headless AppTest |
| Port interfaces (LLMPort, ComputeBackendPort, etc.) | PROVEN | ddp/ports.py + existing impls satisfy protocols |
| Pipeline skeleton (RunTrace, DispositionPipeline) | PROVEN | ddp/pipeline.py; offline gate green |
| EVIDENCE table schema + store methods | PROVEN | additive; no rows written yet |
| Token Factory live call | **ASSUMED** | base URL + model IDs unverified → T0.4 |
| Structured output (json_object mode + repair retry) | **PROVEN offline**; live: likely 14/16 model-valid (2026-10-21 run; 2 fallbacks were counted as valid) | runner fixed (T7.3); live rerun pending |
| str_quality_checker fail-closed (T3.4 fix) | **PROVEN** | `test_str_quality_checker_fail_closed_on_double_failure` |
| Nemotron output quality on this task | **ASSUMED** | no live run yet |
| Sandbox execution of the calculator | **BLOCKED** | 2026-10-21: probe ran with project ID set; 403 ForbiddenError from `/sandboxes/v1/instances` — Sandboxes access not provisioned on this account. No `BACKEND_RUN_REF`. Do not claim. |
| Tavily adverse-media | **PROVEN live** (integration, 2026-10-21); relevance **not shown** (synthetic seed → generic queries) | `evals/TAVILY-PROBE-2026-10-21.md` |
| Tavily failure vs no-results | **PROVEN** live + offline (8 statuses; `adverse_media_screen` evidence row) | `tests/test_evidence.py` |
| `run_to_draft` fails closed (incl. policy-gate block) | **PROVEN offline** | `tests/test_pipeline_fail_closed.py` |
| DeterministicPolicyGate catch rates | **PROVEN** | `ddp/gate.py`, eval_harness_v2 E1 |
| NemotronContentSafetyGate | **STUBBED** (falls back to DeterministicPolicyGate) | T3.1 |
| Eval harness v2 (gate, abstention, evidence, live stubs) | **PROVEN** 23/26 offline; 3 SKIPs need live key | `tests/eval_harness_v2.py` |
| Demo "caught it" script | **PROVEN** | `scripts/demo_caught_it.py` |
| Decision Stress Test (branch runs, minimal flip sets, reopen triggers) | **PROVEN offline** | `tests/test_stress.py`; heuristics PROPOSED |
| Agentic investigator (tool loop, validated submission) | **PROVEN offline** (scripted model) | live Nemotron tool calling **ASSUMED** → T6.2 |
| Regulator-only Tavily search | **PROVEN live** 2026-10-21 (5 rbi.org.in results; refusal sends nothing) | T6.3 done |
| Live eval runner | **PROVEN (mock)** | no live numbers yet → T6.5 |

## 3. Blockers / decisions only the human can make

1. **Credits** — claim both $25 Token Factory grants (T0.1) and apply to the AI Builder Program.

## 5c. Phase 4 final commit — token usage tracker (2026-09-28)

- `ddp/store.py`: `token_usage_summary()` reads prompt+completion tokens from all
  `DECISION_LEDGER.METADATA_JSON.model_calls` rows, aggregates by tier, returns
  `{total_prompt, total_completion, total, by_tier, decisions_with_model_calls}`.
- `app.py` Dashboard: 3 metrics (prompt, completion, total) + per-tier table; honest caption
  about source (ledger only) and directs to billing console for accurate spend.
- `tests/test_nebius_edition.py`: `test_token_usage_summary` added; 53 tests total, all pass.
- TASKS.md: T2.1–T4.3 all marked done.
- **OFFLINE WORK IS FEATURE-COMPLETE.** All remaining open tasks need NEBIUS_API_KEY or are human-only.

## 5b. Phase 4 (this session) — what changed (T4.1)

- `app.py`: added `get_pipeline()` helper (4th element of `build()` return).
- `_adverse_media_panel(selected, alert)`: new function. Shows evidence items from the store
  (type=adverse_media) for the current alert. Has a "Fetch adverse media" button that calls
  `pipeline.step_adverse_media(…)` and re-runs. When no TAVILY_API_KEY, shows a caption.
  Wired into `_ai_panel()` after the calculator panel.
- `DeterministicPolicyGate` verdict on GoS: after quality score, shows gate pass/fail live
  on the current draft text. Policy violations are shown as st.error with policy ID + reason.
- `_reconstruct_view(row, meta)`: new function. Inside each ledger expander, an expandable
  "↩ Reconstruct decision" section shows compute run hashes, a "Reproduce" button (calls
  `compute_reproduce(…)`), model calls with tier + token usage, and corpus rules cited.
- Sidebar: shows Tavily API key status alongside model status.
- Offline gate: 52 pytest + 24 eval v1 + 23 eval v2 = all pass.

## 5a. Phase 3 (this session) — what changed

- `ddp/evidence/tavily.py` + `ddp/evidence/__init__.py`: TavilyEvidenceSource. No-key path
  returns []; query safety enforced; snippets capped at 300 chars; untrusted sentinel added.
- `ddp/gate.py`: DeterministicPolicyGate (regex, always-on) + NemotronContentSafetyGate
  (STUBBED, falls back to deterministic).
- `ddp/store.py`: `append_evidence` now normalises key case (accepts both lower- and UPPER-).
- `ddp/pipeline.py`: `DispositionPipeline.__init__` accepts `store`; `step_adverse_media`
  persists evidence items; `run_to_draft` passes `alert_id` to the step.
- `ddp/bootstrap.py`: imports Tavily + gate; `build()` returns 4-tuple with pipeline.
- `tests/test_evidence.py`: 18 offline tests (no-key, query safety, mock API, snippet cap,
  untrusted sentinel, store persistence, gate catch rates).
- `tests/eval_harness_v2.py`: 26 checks (E1–E5); 23 pass, 3 SKIP (live model).
- `scripts/demo_caught_it.py`: "caught it" demo runs offline, DEMO PASSED.
- `.streamlit/config.toml`: theme + security settings.
- `README.md`: full rewrite with architecture, Nebius/Nemotron/Tavily sections, eval table.
- `CHANGES_SINCE_BASELINE.md`, `DECISIONS.md`: updated.
- Offline gate: **52 pytest + 24 eval v1 checks + 23 eval v2 checks = all pass**.

## 5. Known gaps / honest caveats

- Prompts were written for `llama3.3-70b`. Nemotron may need JSON-format tuning even
  with `json_object` mode enforced. A live run at T1.1 will reveal whether repair retries fire.
- `str_quality_checker` fail-closed fix (T3.4) is now PROVEN (brought forward in Phase 2).
  All parse failures now yield quality_score=0, recommendation=REJECT — no silent pass-through.
- The SLA uses the baseline's calendar-to-working-day proxy (×5/7), which ignores holidays.
- The retrieval abstention threshold (coverage < 0.5) was tuned on a handful of queries.
- `DispositionPipeline.run_to_draft()` is not yet wired into app.py (app.py still calls
  CoPilotSkills directly). App wiring is part of T4.1 UI polish phase. The pipeline is
  used by the eval harness (T3.2).

## 5d. Live keys session (2026-10-21) — T0.4 / T1.1 / T1.2

**T0.4 — Model IDs PROVEN**
- check_models: HTTP 200 from api.tokenfactory.nebius.com/v1/models
- 3/3 tiers confirmed: Nano 30B (triage), Super 120B (reasoning), Ultra 550B (disposition)
- Finding: Nano and Super have internal reasoning tokens. At max_tokens=16 the ping returned
  empty string (reasoning used the full budget). Raised _complete_structured default to 4096.
- api.studio.nebius.com tested and rejected (401) — the correct URL is tokenfactory.

**T1.1 — Live 11-factor assessment PROVEN**
- python -m scripts.run_live_eval --alerts ALERT-01,ALERT-02,ALERT-16 --skip-agent
- Schema-valid: 3/3; repair retries: 0. Report: evals/REPORT-2026-10-21-live.md.
- Latency: 31–50s per alert on reasoning (Super 120B). json_object mode is sufficient.

**T1.2 — GoS drafting hard gate PROVEN**
- ALERT-01: Quality 10/10, status=READY, hard_gate=True. Forced-wrong ₹350,000 caught.
- ALERT-02: hard_gate=True. Forced-wrong ₹425,000 caught. Quality checker 0/10 (parse
  failure: ALERT-02's longer narrative still hits Nano's token budget at 4096 — known issue).
- Fix 1: F-DECLARED-INCOME added to aggregations.py so ₹28,000 KYC income passes gate.
- Fix 2: max_tokens raised to 4096 for _complete_structured/_complete_json_array.
- Claim status: hard gate PROVEN; quality checker PROVEN for simple alerts, STUBBED for
  complex multi-account alerts until Nano token budget is further diagnosed or tier is raised.

## 5e. Tavily live + fail-closed pipeline (2026-10-21)

- **Tavily live:** `python3 -m scripts.probes.probe_tavily` → 6/6 cases pass
  (`evals/TAVILY-PROBE-2026-10-21.md`): adverse media ALERT-01/16 (HTTP 200, 5 hits each),
  regulator search (5 rbi.org.in hits), case-identifier refusal (nothing sent), forced 401 →
  `http_error`, forced 1 ms timeout → `timeout`. API key absent from outputs (asserted).
- **Finding — adverse-media relevance:** the seed has no names, so `_build_query` produces generic
  queries ("India bank money laundering fraud…", "Freelance money laundering…"). Hits are
  unrelated articles and AML job listings. Do not present adverse-media hits as screening
  results in the demo; the regulator search is the meaningful live Tavily use.
- **Failure statuses:** `TavilyEvidenceSource.last_status` / `source.last_status` after
  `fetch_regulatory_updates`. Each screen attempt is an `adverse_media_screen` EVIDENCE row
  (CHECK widened by the existing additive migration). Panel shows "did not run" (st.error) vs
  "ran, no results" (st.info). Agent tools return `screen_status` and say "did not run".
  Panel change is covered only by the existing headless smoke test, not checked visually.
- **`run_to_draft` fails closed:** stops at compute / assess (incl. unparseable) / draft / empty
  narrative; policy-gate block or gate error → `blocked=True`, draft kept for revision.
  Still not wired into app.py.
- **Gate gap fixed (same day):** new `tipping_off_customer` policy blocks telling the customer
  about a report / FIU / investigation (`tests/test_gate_tipping_off.py`). Scan of 2,612
  scenario + seed sentences: no new hits.
- **Open policy question (human):** `tipping_off_str` blocks bare filing references
  ("STR filed", "CTR filed") although a GoS goes to FIU-IND and the expert gold drafts
  (scenarios 06/09/10) reference companion STRs. It already blocks scenario 07's gold closure
  ("CTR filed per schedule"). I did not widen it to "STR has been filed" for that reason, and
  did not narrow it either. Decide: keep, or restrict `tipping_off_str` to customer-facing text.
- Offline gate: 146 pytest, eval_harness 24/24, eval_harness_v2 25/26 (1 skip).

## 5f. Trust-boundary tasks T7.x (2026-10-21)

- **T7.4 done:** `build()` passes the API key to the sandbox backend (construction only).
- **T7.3 done:** fallbacks no longer count as valid. **Finding:** the committed live report's
  "16/16" counted ALERT-01 and ALERT-04 fallbacks → likely 14/16 (README/CHANGES corrected; see
  DECISIONS). Live assessment rerun not done (costs credits; would overwrite the same-date
  report file — use `--out` or a new date).
- **T7.2 done:** recorder enforces the evidence gate (all dispositions); checked in the running
  app: refusal shown, ledger unchanged. New button label wraps badly in a narrow column.
- **T7.1 in progress, stashed** (`git stash list`, applies cleanly on main): `ddp/money.py`
  parser (₹ / Rs. / INR / lakh / crore / K, ranges → unparsed), exact matching, no totals in the
  validator, `F-DECLARED-ANNUAL-INCOME` + `parse_declared_annual_income`. **Blocked:**
  `tests/test_offline.py` and `tests/eval_harness.py` are read-only (baseline) and assert the gold
  narrative passes *without* calculator facts — true today only because of the bypass
  ("₹3.6 lakh" skipped; ₹5,55,000 total computed by the validator). Needs the human's OK to edit.
  When T7.1 lands, remove the strict xfail in `tests/test_recording_gate.py`.
- Until T7.1 lands, a rationale written with "Rs."/"INR"/"lakh" still passes the gate,
  including at recording. Do not demo with those forms.
- Brief stored: `docs/DESIGN_AND_TECH_BRIEF-2026-10-21.md`.
- Offline gate: 160 pytest + 1 xfail, eval_harness 24/24, eval_harness_v2 25/26 (1 skip).

## 5g. T7.1 landed (2026-10-21)

- Exact rupee parsing in the gate, the agent submission check and the stress memo (see CHANGES).
  The "Rs. / INR / lakh" bypass is closed, including at recording.
- Baseline tests edited **with the human's explicit OK**: `tests/test_offline.py` (2 gold-narrative
  checks) and `tests/eval_harness.py` (SCN-18 gold narrative) now pass calculator facts. Both are
  read-only again. `tests/test_transactions.py` did not need changes.
- `aggregations.py` changed (new fact), so its CODE_SHA256 changed: runs recorded before today
  reproduce only against the program version they were recorded with.
- Known limits: amounts in words are unparsed (fail); other currencies are not recognised; the
  gate checks figures, not whether the sentence around a figure is true.
- Offline gate: 222 pytest, eval_harness 24/24, eval_harness_v2 25/26 (1 skip), demo_caught_it passes.

## 5h. Rest of the design brief (2026-10-21)

All brief items are implemented; status per item is in `docs/DESIGN_AND_TECH_IMPLEMENTATION.md`
and each public claim's evidence is in `docs/CLAIMS_REGISTER.md`.

- New modules: `ddp/claims.py`, `ddp/package.py`; scripts `export_decision`, `verify_package`,
  `run_comparison`; holdout `evals/holdout/HOLDOUT-v1.json`.
- Schema (additive, migrated on open): `COMPUTE_RUNS.INPUT_JSON`, `PROGRAMS` table (append-only),
  `LEDGER_IDEMPOTENCY` unique index, EVIDENCE type `adverse_media_screen`.
- Read-only files found: requirements.txt, .gitignore, ci.yml, .env.example, seed_data.py,
  corpus, scenarios, design docs, launch.json. Nothing was changed in them. Pins are in
  `constraints.txt`. **CI runs only five named scripts**, so new suites run locally (`pytest -q`)
  but not in CI until ci.yml changes.
- Holdout findings (not tuned away): the gate checks values, not meaning (H-01); counterparty
  match is literal (H-02).
- Not verified: Docker build (no daemon), hosted deployment, sandbox execution, screen-reader pass.
- Live (2026-10-21): rerun 16/16 model-valid (4 repairs, all truncation); agent 12/12 clear,
  FILE on all 4 contested; holdout: baseline 6/6 drafts with unsupported figures, product 3/6
  rejected by the gate, 0 unsupported in accepted. Findings and follow-ups in DECISIONS.md.
- Fixed after the run: zero-valued facts were rejected (H-03). Not fixed: reasoning leakage in
  Ultra drafts (H-05); truncation at 4096 tokens.
- Offline gate: 273 pytest, eval_harness 24/24, eval_harness_v2 25/26 (1 skip); CI's five
  scripts pass; clean Python 3.11 install with constraints.txt passes.

## 5i. Four-criteria improvement session (2026-10-21, second session)

Source: the pre-submission audit. The human owns git (Claude never commits or pushes), the video,
the deck, the licence and hosting. Tasks T9.1–T9.13 are in TASKS.md; per-item status is in
CHANGES_SINCE_BASELINE.md; every public claim is in docs/CLAIMS_REGISTER.md.

**Done**
- UI runs through the pipeline with a visible run trace (T9.1); CI workflow written (T9.2).
- Sandbox probe (T9.3): found the assumed SDK call shape was wrong, rewrote the backend to the real
  `contree-sdk` 0.3.6 shape, and reached the live endpoint. **Probe ran 2026-10-21 with project ID
  set; received 403 ForbiddenError from `/sandboxes/v1/instances` — Sandboxes beta not provisioned.**
  No `BACKEND_RUN_REF`. Claim remains BLOCKED. Details in DECISIONS.md and docs/PLATFORM_NOTES.md.
- One clean live evaluation committed (`evals/live-2026-10-21-final/`); README quotes exactly that
  file and `tests/test_evidence_view.py` pins the numbers (T9.4). Run-to-run variation is stated.
- In-app decision-package verifier that never executes untrusted code (T9.5); stress-test headline
  (T9.6); Proof Check page (T9.7); cold-start intro, glossary and help text (T9.8); WCAG AA colour
  contrast enforced by a test (T9.9); Measured Results page computed from committed reports (T9.10);
  `docs/IMPACT.md` with sourced figures and NOT ESTABLISHED claims (T9.11).
- **Bug found by the new UI test and fixed:** three `icon="✓"/"✗"` arguments were invalid emoji and
  crashed the page after a draft passed the policy gate and on the Ledger's Reproduce button.

**Human action items**
1. **Licence (T0.3):** still absent — human to choose Apache-2.0 or MIT and add LICENSE.
3. **Sandbox (T9.3):** probe ran 2026-10-21 and hit **403 Forbidden** — Sandboxes beta is not
   provisioned on this account. To unblock: request access from the Nebius console or via
   support. If access arrives before submission, re-run the probe; only then record the
   `BACKEND_RUN_REF` and change the claim. Otherwise leave the README wording as-is ("ASSUMED").
4. **Hosting (T9.12):** pending by decision. The Dockerfile copies `evals/` so Measured Results works
   there; Docker was not build-tested.
5. **CI:** `.github/workflows/ci.yml` is new and has not run on GitHub.
6. **Holdout labels (T8.11) and `tipping_off_str` audience (T8.12)** are still open.
7. **Public wording:** do not say FIU-IND penalises templated narratives (no source found), and do not
   state any time-saved, accuracy or cost figure.
8. Video, deck and the Devpost text (T5.x).

**Not done, by choice**
- T6.6 / T1.4 richer seed transactions: `seed_data.py` is read-only and the new rows need a domain
  check by the human. Only 1 of 9 gold-FILE alerts reaches a HIGH modeled level because most are a
  single summary transaction; this is stated on the Measured Results page.
- T2.4 inline claim chips; the evidence-first redesign; reasoning leakage in Ultra drafts (H-05).

**Findings to know**
- Model output varies run to run (4 vs 2 repairs; 19 vs 16 agent rejections), so quote one named
  report and the denominator.
- `contree-sdk` 0.3.6 does not install `contree-client`; the old comment in `requirements.txt`
  (read-only) is out of date.
- The package CLI verifier executes the package's program (isolated subprocess); only the in-app
  verifier refuses untrusted code. Documented in docs/DECISION_PACKAGE.md.
