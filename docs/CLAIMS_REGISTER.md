# Claims register

Every public claim (README, Devpost, video) and what supports it. If a claim is not here, do not
make it. Approval owner for every row: the human. Last updated 2026-10-29 (Week 7: living decisions).

## Product behaviour

| Claim (exact scope) | Status | Evidence | Limits |
|---|---|---|---|
| A rupee figure in a Ground of Suspicion must equal a single transaction amount or a calculator-of-record fact; otherwise the draft cannot be READY | PROVEN | `tests/test_money_gate.py`, `tests/test_offline.py`, `scripts/demo_caught_it.py` | values, not meaning (holdout H-01) |
| ₹, Rs., INR, lakh and crore phrasings of the same figure are all checked; ranges and unreadable figures fail | PROVEN | `tests/test_money_gate.py` (18 forms) | amounts in words, other currencies not supported |
| An unsupported figure or customer-disclosure language cannot be recorded, even bypassing the UI | PROVEN | `tests/test_recording_gate.py`; checked in the running app 2026-10-21 | other policy patterns are advisory |
| A repeated submission records one decision; ledger and status are written atomically | PROVEN | `tests/test_recording_gate.py` | — |
| Ledger rows are append-only and hash-chained (tamper-**evident**) | PROVEN | `tests/test_nebius_edition.py` | not tamper-proof |
| A recorded decision can be exported and verified offline; the calculator reproduces from recorded inputs | PROVEN | `tests/test_package.py` | runs before 2026-10-21 have no saved inputs |
| Off-corpus questions abstain; NEEDS-VERIFICATION rules never appear | PROVEN | `tests/eval_harness.py` SCN-20, `test_needs_verification_rules_unreachable` | heuristic threshold |
| Tipping-off requests are refused before any model call | PROVEN | `tests/eval_harness.py` SCN-22 | regex; paraphrases across sentences missed |
| Model failures, retries and truncation are recorded, never shown as success | PROVEN | `tests/test_fault_injection.py` | — |
| A model reply cut off at the output limit is retried once at a larger cap and otherwise shown as an error; it is never returned as an answer or shown as 11 placeholder factors (fix of 2026-10-28) | PROVEN offline; live: one app run on ALERT-01 and three assessments, 2026-10-28 (not committed as a report) | `tests/test_fault_injection.py`, `tests/test_app_pipeline.py::test_cut_off_assessment_is_an_error_not_eleven_gaps` | the agent and the stress memo were not re-run live on the new budget; the dated 2026-10-21 reports predate this change |
| Web search sends no case data (typology topic only) | PROVEN | `tests/test_evidence.py::test_query_contains_no_case_data` | not entity screening |
| A recorded decision is re-checked when a fact it rests on changes: the calculator is re-run on the decision's saved inputs and an append-only, hash-chained event says holds, reopened or needs review; the ledger row is never edited | PROVEN offline | `tests/test_watch.py` (12), `tests/test_watch_ui.py` | the registry feed is synthetic; no bank feed is connected |
| Flagging the hospital's handle reopens the closed twin (ELEVATED → HIGH) and names it as a trigger listed at decision time; flagging the sister does not | PROVEN offline | `tests/test_watch.py::test_flagging_the_hospital_reopens_and_names_the_fact`, `::test_flagging_the_sister_does_not_reopen_the_closure` | synthetic twins; product heuristics |
| FIU-IND has penalised banks for improper, cursory or unreasoned alert closure | SOURCED | Section 13 order summaries: UBI 13/2024, Axis 09/2024, HSBC 19/2022 (`domain/enforcement/fiu_orders.yaml`, read 2026-10-28) | seven orders read; summaries are "representational", not precedent; no rate is claimed |
| Eleven inspector questions, derived from those orders, are answered from the record alone, with the rows each answer rests on; the same check runs before recording and its gaps are written into the ledger row | PROVEN offline | `tests/test_inspection.py`, `ddp/inspection.py` | this project's questions, not an FIU-IND checklist |
| On 16 synthetic alerts, a Twin Trace record answers 96 / 174 inspector questions and a cursory closure 32 / 160 | Measured (deterministic) | `evals/INSPECTION-2026-10-28-deterministic.md` | no factor assessment or sign-in in either record; synthetic |
| A model's claim that the record answers a question is accepted only with row citations that exist, belong to the decision and match their hash | PROVEN offline (seeded faults) | `tests/test_inspection.py::test_seeded_citation_faults_are_rejected` | — |
| Nemotron Super cross-examined 16 records: 79 questions, 25 answered with valid citations, 54 not answered, 0 citations rejected | Measured (live, 2026-10-28) | `evals/INSPECTION-2026-10-28-live.md` | one run; model output varies |
| Regulatory lookup re-ranks BM25 hits with Token Factory embeddings; abstention is still the BM25 rule | PROVEN offline; embeddings live | `tests/test_hybrid_retrieval.py`; `evals/RETRIEVAL-2026-10-28-live.md` | embedding model is Qwen3-Embedding-8B (not NVIDIA); rerank endpoint returned 404 |
| On 16 paraphrased questions the labelled rule was in the top 3 for 13 (BM25) vs 16 (hybrid); 4 / 4 off-corpus questions abstained in both | Measured (live, 2026-10-28) | `evals/RETRIEVAL-2026-10-28-live.md` | questions written by the coding assistant after reading the corpus |
| A proposed rule change is kept only if its passage appears word for word on the fetched regulator page, is never used for answers while pending, and on promotion sends every decision citing the rule for review | PROVEN offline | `tests/test_lookback.py` | promotion does not edit the corpus |
| Tier panel (Nano, Super, Ultra in parallel) on 22 synthetic cases: 0 / 6 CONTESTED cases marked contested; 4 / 5 NOT_FILE cases marked contested (smaller tiers said FILE, Ultra did not); 0 / 11 FILE cases marked contested | Measured (live, 2026-10-28) | `evals/PANEL-2026-10-28-live.md` | one run; author-assigned labels; the panel does **not** detect contested cases. Do not claim it does |
| The lookback ran live on three rules: fetch and check worked, nothing was kept, because the corpus source links are landing pages | Measured (live, 2026-10-28) | `evals/LOOKBACK-2026-10-28-live.md` | a finding about the corpus links (gap DG-14), not a working update feed |
| The Proof Check page: an invented total is blocked and a recording attempt writes 0 ledger rows, in every currency spelling (₹, Rs., INR, lakh); the same draft with the calculator's figure passes. The attempt uses a throwaway ledger | PROVEN | `tests/test_proofcheck.py`, `tests/test_app_pipeline.py`; checked in the running app 2026-10-21 | values, not meaning |
| An uploaded decision package is verified in-app without executing any program the deployment does not already trust | PROVEN | `tests/test_package_upload.py` (hostile program with a matching hash is never run) | reproduction is skipped, and the package does not verify, for unknown program versions |
| The stress test states in one sentence what a FILE rests on, or what would reopen a closure, using only the deterministic report | PROVEN | `tests/test_stress_headline.py` (ALERT-01, -16, -04) | modeled levels are product heuristics |
| Assessment, drafting, screening and the policy gate run through one pipeline trace in the app | PROVEN | `tests/test_app_pipeline.py` | the trace is session-only |
| Status colours meet WCAG AA text contrast (4.5:1) | PROVEN (computed) | `tests/test_accessibility.py` | no screen-reader pass was run |
| The Disposition Panel opens on both readings — what a FILE rests on and what would reopen a closure — computed deterministically, with no model | PROVEN | `tests/test_verdict.py`, `tests/test_app_smoke.py` | the officer chooses; levels are product heuristics |
| ALERT-01 and ALERT-16 fire the same rules on the same ₹3,45,000; the calculator differs on one signal (flagged counterparty); the FILE rests on one fact and the closure has three reopen conditions | PROVEN | `tests/test_verdict.py`, `tests/test_app_smoke.py` | the opposite decisions are the scenario's synthetic labels, not the system's choice; ALERT-16 models ELEVATED, not LOW |
| Every regulatory stake on the landing page cites a PROVEN/ASSUMED corpus rule | PROVEN | `tests/test_stakes.py` | INS-001 is ASSUMED (governance practice, not a circular) |

## Platform use (hackathon gates)

| Claim | Status | Evidence |
|---|---|---|
| Runtime calls to Nebius Token Factory with NVIDIA Nemotron (Nano 30B, Super 120B, Ultra 550B) | PROVEN | `scripts/check_models.py --ping`, 2026-10-21 (3/3 tiers answered); `evals/live-2026-10-21-final/` |
| Tavily live: typology search, regulator-only search, refusal, forced failures 6/6 | PROVEN | `evals/TAVILY-PROBE-2026-10-21.md` |
| Calculator runs in Token Factory Sandboxes | **BLOCKED, not run** | 2026-10-21: backend corrected to the real `contree-sdk` 0.3.6 call shape; with key and project ID set, `/sandboxes/v1/instances` returned **HTTP 403** (Sandboxes access not provisioned on this account). No `BACKEND_RUN_REF`. Offline tests only (`tests/test_sandbox_backend.py`). **Do not claim sandbox execution**; say "the calculator runs in a local isolated subprocess; the Sandboxes backend is written but our account was refused access" |
| The app shows which Nemotron tier and model answered each step, with tokens and seconds, from recorded calls only | PROVEN | `tests/test_platform_trace.py`, `tests/test_app_pipeline.py`; one live Nano call checked 2026-10-22 | per session; telemetry, not a performance claim |

## Measured results (synthetic data; quote with date and denominator)

| Claim | Status | Evidence |
|---|---|---|
| Holdout gate: 10 of 15 seeded faults caught (10 of 12 the gate is designed to catch); 0 of 11 supported narratives rejected | PROVEN (deterministic) | `evals/RUN-20261021T074721Z-gate-only/` |
| 16-alert live assessment: 16/16 model-valid (14 first try, 2 after one repair; 0 fallbacks); both repairs followed truncation | PROVEN (2026-10-21 09:12 UTC, dev set, **old seed**) — history; quote the 2026-10-28 row below | `evals/live-2026-10-21-final/` (README quotes this file) |
| Agent: 12/12 on clear dev cases (9 FILE, 3 NOT_FILE); chose FILE on all 4 contested; 16 submissions rejected by validation and corrected across 12 alerts | PROVEN (2026-10-21 09:12 UTC, dev set, **old seed**) | `evals/live-2026-10-21-final/` — say "an always-FILE rule scores 9/12" alongside |
| Run-to-run variation: an earlier run the same morning had 4 repairs and 19 rejections, with the same 12/12 and 4/4 | PROVEN (2026-10-21 07:47 UTC) | `evals/rerun-2026-10-21/` — say model output varies between runs |
| Holdout: same model without controls put unsupported figures in 6/6 drafts (15 figures); the full product's drafter did so in 3/6, all 3 rejected by the gate; 0 unsupported figures in accepted drafts | PROVEN (2026-10-21, 6 cases) | `evals/RUN-20261021T080109Z-live/` — six author-labelled cases, no general claim |
| 16-alert live run on the current seed: assessment 16/16 model-valid, all first try; agent 12/12 on clear cases (an always-FILE rule scores 9/12), FILE on all 4 contested; 14 submissions rejected by validation and corrected across 9 alerts; medians 18.1 s (assessment), 14.9 s (agent) | PROVEN (2026-10-28 13:38 UTC, dev set, current seed, agent prompt before item 4) — **the figure to quote** | `evals/live-2026-10-28-seed/` (README quotes this file) |
| Agent prompt change (2026-10-28) to weigh closure or deferral: NOT shown to reduce the filing lean, and reverted. Dev contested filed 4/4, 4/4 → 3/4, 3/4; holdout 2/2, 2/2 → 1/2, 2/2; one run of each set lost a clear case | MEASURED, no improvement claimed (8 live runs, 2026-10-28) | `evals/AGENT-LEAN-2026-10-28.md` |
| Stress-summary framing fix (2026-10-28): no effect on the filing lean. Contested filed dev 4/4, 4/4 and holdout 2/2, 2/2, as before | MEASURED (4 live runs, 2026-10-28) | `evals/AGENT-FRAMING-2026-10-28.md` |
| Stress test on the current seed: 3 of 9 gold-FILE alerts reach a HIGH modeled level from calculator signals (ALERT-01, -06, -10); 1 of 9 on the old seed | PROVEN (deterministic, 2026-10-28, no model) | `evals/REPORT-2026-10-28-deterministic.md` — signals are product heuristics; thresholds unchanged |
| First run's "16/16 assessments valid" | **WITHDRAWN** | counted fallbacks; likely 14/16 (`evals/README.md`) |

## Impact and context (sourced; see `docs/IMPACT.md`)

| Claim | Status | Evidence |
|---|---|---|
| FIU-IND received 4,33,761 STRs in FY 2021-22 | SOURCED (primary, dated) | FIU-IND Annual Report 2021-22, §3.2.1, p. 20 |
| FIU-IND says STR quality is an engagement issue and issues guidelines to improve it | SOURCED (primary) | same page |
| Indians lost ₹22,845.7 crore to cyber fraud in 2024 (₹7,465.1 crore in 2023) | SOURCED (secondary report of a Lok Sabha reply; verify on sansad.in) | Scroll.in, 2025-07-23 |
| FIU-IND specifically penalises templated narratives | **NOT ESTABLISHED** | no source found 2026-10-21; checklist stays a product heuristic (DG-09) |
| Any officer time saved or error reduction in practice | **NOT ESTABLISHED** | no officer study |

## Never claim

"compliant", "FIU-IND approved", "tamper-proof", "every claim verified", time saved, cost saved,
fewer false positives, accuracy beyond the dated reports above, or sandbox execution.
