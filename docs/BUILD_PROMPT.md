# BUILD_PROMPT.md — Claude Code master prompt: architecture → submission

Paste everything below the line into Claude Code, opened at the repo root
(`~/Hackathons/twin-trace`). It runs in phases. Each phase ends with a commit
and a HANDOFF update, so any phase can be resumed in a fresh session with: "Continue
BUILD_PROMPT.md from Phase N."

---

You are the lead engineer on **twin-trace**, my solo entry to the Nebius ×
NVIDIA Global AI Hackathon 2026 (Best Apps & Agents track, plus the Best Use of Tavily bonus).

- **Hard deadline:** Fri 30 Oct 2026, 22:30 IST.
- **My target:** submit Wed 28 Oct.
- **Feature freeze:** Fri 23 Oct.
- I am also finishing a this platform hackathon (prototype due 4 Oct, finale 27–30 Oct), so my hours
  are scarce. Spend them on what judges score.

Your job: take this repo from its current state (ported, offline-green, not yet live on Nebius)
to a submission-ready product. Start by analysing and implementing the technical architecture,
then execute the build plan.

## Non-negotiables (read before anything else)

1. **Obey `CLAUDE.md` completely.** In particular:
   - separation from `~/Hackathons/bank fraud detection` (never read or write it);
   - never rewrite history at or before tag `baseline-this platform-2026-09-25`;
   - the invariants table in §3;
   - claim discipline in §4.
2. **Every claim is labelled PROVEN / STUBBED / ASSUMED.** Nothing is PROVEN without a test or a
   recorded live run. No invented numbers anywhere: code, docs, README, video script, Devpost
   text.
3. **Verify platform facts; never guess them.** Before writing code against any external API
   (Token Factory, Sandboxes, Serverless Endpoints, Tavily, Nemotron Content Safety), read its
   current official docs with WebFetch/WebSearch. Record what you verified, with the URL and the
   date, in `docs/PLATFORM_NOTES.md`. If the docs are unclear, write a minimal probe script under
   `scripts/probes/`, run it, and record the result. If an API cannot be verified, keep an
   honest stub and say so. A working fallback beats a pretend integration.
4. **Synthetic data only.** Token Factory Sandboxes are in beta and forbid personal or sensitive
   data.
5. **Keep the offline gate green at every commit.** Run `python -m pytest -q` and
   `python tests/eval_harness.py`. Tests for live services must auto-skip without keys; they
   never fail CI.
6. **Commit discipline.** Small commits, one concern each. Use the attribution trailer your
   environment requires.
7. **Stop and ask me only for:**
   - API keys or credits;
   - licence / IP decisions;
   - spending real money beyond the free credits (give me the estimate first);
   - anything that changes what the product claims to do.

   Everything else: decide, record it in `DECISIONS.md` as **PROPOSED** with its rationale, and
   continue.
8. **Git on my Mac is normal git.** If you run inside a sandbox that cannot delete files, git
   lock files will break. Tell me instead of working around it.

## Session start (every session)

Follow `CLAUDE.md` §0: read HANDOFF, TASKS, the last 3 DECISIONS entries and
CHANGES_SINCE_BASELINE, then run the offline gate. Report in ≤10 lines:
- gate status;
- current phase;
- what is ASSUMED/STUBBED that this session will try to prove;
- anything blocking you that needs me.

---

## Phase 1 — Architecture analysis and target design (no feature code yet)

**Goal:** a written architecture that every later phase implements against, and that the README
and video can explain in 30 seconds.

1. **Map the as-is system.** Read all of `ddp/`, `app.py` and `tests/`. Produce
   `docs/ARCHITECTURE.md` §1 "As-is": a component diagram (Mermaid), data flow for one alert
   end to end, every external dependency, and every place a number, citation or decision is
   produced.
2. **Critique it against the four judging criteria**, equally weighted:
   - Technological Implementation (the tie-breaker);
   - Design;
   - Potential Impact;
   - Quality of the Idea (a "creative, non-obvious use" of Token Factory and Nemotron).

   List concretely where the current code would lose points. Minimum set to cover:
   - Nemotron output reliability (JSON parsing; the quality checker fails *open* on unparseable
     output);
   - the calculator running only locally;
   - no adverse-media evidence;
   - no policy gate beyond keyword rules;
   - no measured evaluation;
   - Streamlit UX gaps against `design/` docs;
   - single-process SQLite on a hosted demo;
   - prompt-injection surface from case text.
3. **Design the target architecture** in `docs/ARCHITECTURE.md` §2 "Target". Required elements:
   - **Unified evidence model.** Every fact the product may rely on is an evidence item with
     `evidence_id`, `type` (transaction | computed_fact | adverse_media | corpus_rule |
     policy_verdict), `source`, `provenance`, `content_hash` and `created_at`, stored
     append-only. Ground-of-Suspicion claims and ledger decisions reference evidence IDs. Decide
     whether this is a new `EVIDENCE` table or views over the existing tables, and justify it.
   - **Ports and adapters** for:
     - the LLM (exists);
     - compute backends: local and nebius-sandbox;
     - evidence sources: transactions, calculator, Tavily;
     - policy gates: deterministic screen, then Nemotron Content Safety;
     - persistence.

     Each port has a typed contract (dataclasses or TypedDicts) and a fake for tests.
   - **Orchestration.** Define the disposition pipeline as explicit, resumable steps:
     ```
     screen → compute → adverse-media → assess (reasoning tier) → draft (disposition tier) →
     gates (deterministic hard gate + policy gate + quality check) → human decision → ledger
     ```
     Each step's inputs, outputs and failure behaviour are defined. Fail closed wherever a
     compliance output would otherwise pass unchecked. It stays human-in-the-loop, with the
     AI recommendation shown last.
   - **Model-tier policy.** Which tier each step uses, why, the expected token budget per alert,
     and the fallback when a tier is unavailable.
   - **Structured output strategy** for Nemotron: JSON mode / `response_format` if Token Factory
     supports it for the model (verify), otherwise schema-in-prompt + validate + one repair
     retry. Never silently default to "pass".
   - **Deployment topology** for the hosted demo. It must stay free to test until judging ends
     (15 Dec). Evaluate:
     - (a) Streamlit Community Cloud or similar + Token Factory API;
     - (b) running the app on Nebius AI Cloud (Serverless Endpoint / DevPod — verify what can
       host a web app).

     Option (b) strengthens the "runs on Nebius" story; weigh cost and effort honestly. Also
     cover the persistence choice for a hosted multi-viewer demo (per-session SQLite vs shared)
     and secrets handling.
   - **Security.** Prompt-injection handling for case text and web content (Tavily results are
     untrusted data), secret handling, and no raw reasoning traces or PII in the ledger.
   - **Observability.** A per-alert run trace: steps, models, latency, tokens, cost estimate —
     viewable in the UI and exportable as JSON for the video.
4. **Write ADRs.** One `DECISIONS.md` entry per material choice, marked PROPOSED.
5. **Produce `docs/IMPLEMENTATION_PLAN.md`:**
   - the gap list from as-is to target, ordered by (judged value ÷ effort);
   - each item mapped to a TASKS.md ID (update TASKS.md if the plan changes it);
   - explicit cut lines.
6. **Refactor only what the target needs *now*** to make later phases clean: introduce the port
   interfaces and the pipeline skeleton with the existing behaviour behind them. No behaviour
   change. All tests green.
7. **Commit.** Update HANDOFF, then show me a 15-line summary of the architecture and the
   top 5 risks. Continue to Phase 2 unless the summary contains a decision only I can make.

**Done when:**
- ARCHITECTURE.md (as-is, critique, target, Mermaid diagrams), IMPLEMENTATION_PLAN.md and the
  ADRs are committed;
- the port interfaces and pipeline skeleton exist;
- the gate is green.

## Phase 2 — Go live on Nebius (TASKS T0.4, T1.1, T1.2)

Needs `NEBIUS_API_KEY` in `.env`. If it is missing, stop and ask me.

1. Run `python -m scripts.check_models --ping`. Fix the base URL and model IDs from the live
   catalog, and record the output in DECISIONS.md and PLATFORM_NOTES.md.
2. Implement the structured-output strategy from Phase 1. Make `str_quality_checker` fail
   closed. Add a parse-failure counter to the run trace.
3. Live-run the full pipeline on ALERT-01 (FILE), ALERT-02 (structuring), ALERT-16 (legitimate
   twin of ALERT-01, gold NOT_FILE) and one INSUFFICIENT_EVIDENCE case (scenario 16).
   - Save redacted run traces under `evals/runs/<date>/`: models, tokens, latency, outputs,
     gate results — never secrets.
   - Tune prompts for Nemotron without changing their regulatory semantics. Any change to POE
     factors, checklist items or `CHECKLIST_BASIS` is forbidden.
4. Add live tests marked `@pytest.mark.live` that skip without a key.

**Done when:** all four cases complete live, the traces are committed, and Token Factory moves
to PROVEN in HANDOFF.

## Phase 3 — Calculator of record in Token Factory Sandboxes (T1.3)

1. From the official docs (Sandboxes overview, CLI `run`, API for spawning instances,
   checkpoints), write a probe that starts a sandbox from a Python base image, runs a
   stdin→stdout program, returns output and a run/instance identifier, and tears down.
   Record the exact working call shape in PLATFORM_NOTES.md.
2. Implement `NebiusSandboxBackend.execute()`:
   - disable networking if the API allows;
   - bound the timeout;
   - make cleanup idempotent;
   - return the real run reference.
3. Prove equivalence: the same input gives an identical `OUTPUT_SHA256` locally and in the
   sandbox. `reproduce()` must work across backends.
4. Make the backend selectable in the UI, and show "executed in Nebius Sandbox `<ref>`" in the
   calculator panel and the ledger.
5. If Sandboxes cannot be made to work by 3 Oct, stop. Record why in DECISIONS.md, keep the
   stub, and make every doc say "local isolated subprocess". Tell me.

**Done when:** a real `BACKEND_RUN_REF` is in COMPUTE_RUNS, the equivalence test passes live,
and Sandbox execution moves to PROVEN.

## Phase 4 — Adverse-media evidence via Tavily (T2.1, T2.2)

1. Verify the Tavily API (search/extract, parameters, credits) from the official docs.
2. Implement the Tavily evidence source:
   - queries for the subject profile and each counterparty, built from **synthetic** names;
   - domain and recency controls;
   - results stored as `adverse_media` evidence items (query, URL, title, snippet, retrieved_at,
     content_hash).
3. Treat all web content as untrusted data: never as instructions, never passed unfenced into a
   prompt. Add an injection test that uses a hostile snippet.
4. The reasoning tier may cite adverse-media evidence IDs. The hard gate rejects adverse-media
   claims that do not resolve to a stored item.
5. Nothing adverse-media-related may appear in any customer-facing text (tipping-off). Add a
   test.

**Done when:** a live screen on a demo case produces stored, cited evidence, and the injection
and tipping-off tests pass.

## Phase 5 — Policy gate with Nemotron Content Safety (T3.1)

1. Verify availability and hosting options for Nemotron Content Safety (custom-policy mode):
   Token Factory catalog, Nebius Serverless Endpoint, dedicated endpoint. Estimate cost per hour
   and per demo day, and **ask me before spending** beyond the credits.
2. Define three custom policies in `policies/*.md`:
   - tipping-off;
   - unnecessary PII;
   - accusation without cited evidence.

   Run the gate on every draft and every customer-facing message. Store the verdict and category
   as `policy_verdict` evidence. Do not store reasoning traces.
3. Put the deterministic `screen_request` first; the model gate adds coverage and never replaces
   it. Fail closed if the gate is unavailable for customer-facing text.
4. If hosting is not viable, implement the port with a documented fallback, and say plainly in
   the docs that it is not the NVIDIA model.

## Phase 6 — Evaluation harness v2 (T3.2), then the "caught it" demo case (T2.3)

1. Build `evals/` so that it:
   - runs the 21 gold scenarios (plus planted-violation variants) through the live pipeline;
   - reports numeric-accuracy rate of drafts **with vs without** computed facts (with = the
     product; without = the same prompt with the facts block removed);
   - reports hard-gate catch rate on planted wrong totals, policy-gate catch rate on planted
     tipping-off/PII, abstention precision/recall on on-corpus vs off-corpus questions, and
     disposition agreement with gold labels (FILE / NOT_FILE / CONTESTED handled explicitly);
   - reports cost and latency per alert.
2. Commit a dated report: `evals/REPORT-<date>.md` + JSON. These are the **only** numbers that
   may appear in the README, video or Devpost. Include sample sizes and limitations.
3. Build the demo case for the video's opening: a draft states a wrong aggregate, the hard gate
   blocks it, and the corrected draft cites fact IDs from a sandbox run. It must be reproducible
   from a script: `python -m scripts.demo_caught_it`.

## Phase 7 — Product and design polish (T2.4, T3.3, T4.1)

1. Apply `design/` docs to the investigator flow:
   ```
   alert → evidence (transactions, computed facts, adverse media) → assessment → draft with
   inline fact-citation chips → gates → decision → ledger
   ```
   Keep the AI recommendation last.
2. Add a "Reconstruct decision" view. From a DECISION_ID it shows the evidence items, compute
   run (with a Reproduce button), model calls, policy verdicts, corpus rules and chain
   verification.
3. Show the per-alert run trace: steps, models, tokens, latency, estimated cost.
4. The app must pass its own basic accessibility review: keyboard reachable, labelled controls,
   sufficient contrast.

## Phase 8 — Deploy (T4.2) and docs (T4.3). FREEZE: Fri 23 Oct

1. Deploy using the topology chosen in Phase 1:
   - seeded synthetic data;
   - demo reset that never deletes the ledger mid-session (use per-session DBs or a clearly
     labelled demo reset);
   - secrets via the platform's secret store.

   Record the URL and how it stays up until 15 Dec.
2. Final README:
   - problem;
   - proof-carrying properties;
   - architecture diagram;
   - exactly where Token Factory, Nemotron (per tier), Sandboxes and Tavily are used, and why;
   - the evaluation table from the dated report;
   - "Built on prior work" (from CHANGES_SINCE_BASELINE.md, with the git commands to verify it);
   - limitations;
   - setup.
3. Bring `CHANGES_SINCE_BASELINE.md` fully up to date. It becomes the Devpost "significantly
   updated" text.

## Phase 9 — Submission package (T5.x)

Draft these for me to review and record. You cannot submit or record on my behalf.

1. `submission/VIDEO_SCRIPT.md`, ≤2:50 with timestamps:
   - 0:00–0:30 — the calculator catching a wrong figure;
   - 0:30–1:30 — the full disposition on tiered Nemotron;
   - 1:30–2:10 — tipping-off block, ledger chain verify and reproduce;
   - 2:10–2:50 — eval table, and a spoken naming of Token Factory, the models, Sandboxes and
     Tavily.

   Add a shot list and exact on-screen text.
2. `submission/DEVPOST.md`: the story, "what's new since baseline", built-with list and
   limitations, all numbers sourced from the eval report.
3. `submission/PLATFORM_FEEDBACK.md`: substantive, specific feedback on Token Factory,
   Sandboxes, Nemotron and Tavily from what you actually hit. There is a separate feedback prize.
4. A pre-submission red-team checklist:
   - every claim traced to a test or report;
   - demo URL works logged-out;
   - repo public with licence (my decision, T0.3);
   - `.env` not committed;
   - video ≤3:00.

## Reporting and pacing

- **End of every phase:** update HANDOFF (claim-status table, blockers, candidate backports),
  tick TASKS, add rows to CHANGES_SINCE_BASELINE, commit, and print the one-line next-session
  prompt.
- **Behind schedule?** Apply the cut order in TASKS.md; never silently drop scope. These dates
  are hard checkpoints:
  - Phase 3 by **3 Oct**;
  - Phase 6 by **17 Oct**;
  - freeze **23 Oct**.

  If a checkpoint slips, tell me what you are cutting before cutting it.
- **Never cut:** live Token Factory calls, the evidence gate, ledger integrity, the eval report,
  and honest labelling of anything unfinished.

Begin with the session-start report, then Phase 1.
