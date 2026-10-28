# BUILD_PROMPT_JUDGING.md — audit, then raise the project against the four judging criteria

Paste everything below the line into a fresh Claude Code session opened at the repo root
(`~/Hackathons/twin-trace`). It runs in phases. Each phase ends with a commit
and a `HANDOFF.md` update, so any phase can be resumed in a new session with:
"Continue BUILD_PROMPT_JUDGING.md from Phase N."

This prompt supersedes the generic `docs/BUILD_PROMPT.md` for the final-week push. The project is
already submission-ready; this is a **reshaping pass to score higher**, not a rebuild. Do not add
genuinely new capabilities unless a phase names one. The hackathon judges' own advice is
"polish and focus, don't add more" — honour it.

---

You are the lead engineer on **twin-trace**, a solo entry to the Nebius ×
NVIDIA Global AI Hackathon 2026 (Best Apps & Agents track, + Best Use of Tavily bonus).

- **Hard deadline:** Fri 30 Oct 2026, 22:30 IST. Target submit: Wed 28 Oct. ~8 days of runway.
- The project WORKS and is offline-green (80 pytest, eval_harness 8/8 as of 2026-10-20). It is
  NOT yet proven live on Nebius (no API keys have been run against it).
- ~25,650 participants registered. The bar is high. The goal of this pass is to convert a
  technically strong but justification-dense tool into one a judge *gets* in two minutes.

## 0. Read first, in this order (do not skip)

1. `CLAUDE.md` — standing rules. The invariants table (§3) and claim discipline (§4) bind every
   change in this prompt. In particular: separation from `~/Hackathons/bank fraud detection`;
   never rewrite history at/before tag `baseline-this platform-2026-09-25`; no invented numbers; the
   AI recommendation is shown LAST (anti-anchoring) — see the note under Phase 2.
2. `HANDOFF.md` — current state, what is PROVEN/STUBBED/ASSUMED.
3. The last 5 entries of `DECISIONS.md`.
4. `CHANGES_SINCE_BASELINE.md` — so you never describe reused work as new.
5. `README.md` — the story is already told here (two twin alerts). The app must now tell the
   same story as fast as the README does.
6. Run the offline gate: `python -m pytest -q && python tests/eval_harness.py`. If red, fixing it
   is the first task, before anything below.

## Why this pass exists (the finding that drives every phase)

A panel of Nebius / Tavily / NVIDIA judges published their rubric and four live project reviews.
Four points matter for us, because our project is the exact profile two of their reviewed
projects were dinged for (strong hard-logic engine, text-heavy UI that buries the value):

- **Design:** they reward a complete, intuitive experience with an "aha moment in under two
  minutes"; they penalise text-heavy screens that bury the call to action under technical
  justification. Our Disposition Panel currently shows narrative + signals + calculator captions
  + SHA-256 hashes BEFORE the actual decision and what it rests on. That is backwards.
- **Quality of the Idea:** they reward a non-obvious idea shown clearly. Ours — *two
  identical-looking alerts, opposite correct decisions, and the system shows the fork* — is
  strong but buried: you must know to open ALERT-01 and ALERT-16 separately to see it.
- **Potential Impact:** they want a credible, specific real-world case (who, what problem, why).
  The app states no stakes today.
- **Technological Implementation:** they reward *meaningful, visible* platform use and liked
  visible progress cues / comparison views. Our tiered-Nemotron + Sandboxes + agent depth is
  real but invisible in the UI, and still ASSUMED (not run live). A judge cannot score what they
  cannot see, and proven-live beats feature-rich.

The "aha" we are hiding: **same signal, opposite defensible decisions, and the machine shows
why in one glance.** Every phase below serves making that legible fast, without deleting the
rigour that makes it credible.

---

## Phase 0 — Audit the current state (no code changes; produce a written report)

Before touching anything, produce an honest audit at `docs/JUDGING_AUDIT.md`. This is a
deliverable in its own right: a new session (or the human) should be able to read it and know
exactly where the project stands against each criterion and what the gap is.

Do this:

1. **Walk the app as a judge would.** Run it (offline is fine) and, page by page
   (`page_alert_queue`, `page_disposition`, `page_ledger`, `page_dashboard`, `page_regulatory`
   in `app.py`), record: what a first-time viewer sees first, how many clicks/scrolls to the
   core value, and where technical justification appears before the call to action. Use the
   headless `AppTest` harness in `tests/test_app_smoke.py` to enumerate what renders if you
   cannot see pixels; read the layout order in `app.py` directly (`_ai_panel`,
   `_ai_panel_core`, `_decision_rail`, `_stress_panel`, `_agent_panel`).
2. **Score the project against each of the four criteria, 1–5, with evidence.** For each: the
   current state, the specific gap versus the finding above, and whether closing it is a
   reshape (reuse existing code) or new work. Be critical — this audit is worth more if it is
   harsh. Call out anything that reads as "default LLM-generated styling" (the judges flagged
   that explicitly).
3. **Inventory what already exists so no phase rebuilds it.** The Decision Stress Test
   (`ddp/stress/`), the agent (`ddp/agent.py`), structured output (`ddp/structured.py`), the
   calculator facts (`ddp/compute/aggregations.py`), the eval runner (`scripts/run_live_eval.py`)
   are all built and tested. Confirm each runs. The reshape phases must *surface* these, not
   duplicate them.
4. **List the hard blockers**, chiefly: no live keys → platform claims are ASSUMED, no dated
   eval numbers. Flag anything that needs the human.

End Phase 0 with: commit `docs/JUDGING_AUDIT.md`; update `HANDOFF.md`; print a one-screen summary
of the four scores and the recommended phase order. **Then stop and show the human the audit
before building** — if they are not present, proceed to Phase 1 and note in `HANDOFF.md` that the
audit was not reviewed.

---

## Phase 1 — Design: the "Case Verdict" front door (highest ROI; reshape only)

Goal: a judge reaches the decision and what it rests on in one screen, with the rigour one click
away. Reuse the Decision Stress Test output entirely; add no new computation.

- At the TOP of the Disposition Panel (`page_disposition` / `_ai_panel`), add a **Verdict card**:
  - the proposed disposition (FILE / NOT_FILE) with the existing `disp_badge`;
  - the stress test's `summary` distilled to **one plain-English sentence** of what the decision
    rests on (reuse `report["summary"]` / `load_bearing` / `reopen_triggers` from
    `ddp/stress/engine.py` — do not recompute; call the tester if no report is cached);
  - 2–3 chips: load-bearing evidence (for FILE) or reopen triggers (for NOT_FILE).
- **Everything currently above the fold becomes a click.** Move the 11-factor assessment, the
  calculator captions, the SHA-256 provenance line, the branch table and evidence IDs into an
  expandable **"Show the proof"** section below the card. Delete nothing — relocate. The hashes
  and provenance are the credibility; they are just no longer the *first* thing seen.
- Keep the anti-anchoring invariant (CLAUDE.md §3): the **AI's** recommendation still renders
  after the human's own view / the deterministic signals. The Verdict card shows the
  *deterministic stress-test* verdict and what it rests on — that is not the AI's opinion, so it
  may lead. If in doubt, keep the AI suspicion assessment inside "Show the proof".
- Add a tiny bit of intentional, non-default styling (the judges flagged generic LLM styling):
  a consistent accent, clear verdict colour (reuse `VERDICT_COLORS` / `DISP_COLORS`), real
  whitespace. Do not pull in a heavy CSS framework.

Tests: extend `tests/test_app_smoke.py` so the Disposition Panel renders the Verdict card offline
and the proof section is present but collapsed. Keep all existing smoke assertions passing.

End Phase 1: offline gate green; commit; `CHANGES_SINCE_BASELINE.md` + `HANDOFF.md` updated;
new `DECISIONS.md` entry (PROPOSED) describing the information-hierarchy change.

---

## Phase 2 — Quality of the Idea: the "Twin Cases" view (the demo spine; reshape)

Goal: make the non-obvious idea legible in 30 seconds. This becomes the centre of the video.

- Add a **Twin Cases** view (a new page in the sidebar, or a prominent entry point on the Alert
  Queue) that places **ALERT-01 and ALERT-16 side by side**: same ₹3,45,000 credits, same rule
  fired (RFI-001 + I4C), then the stress test splits them —
  - ALERT-01 (FILE): rests on the single I4C flag on handle C (flip size 1);
  - ALERT-16 (NOT_FILE): reopens only if the hospital / brother / father is later flagged; the
    sister alone does not flip it.
- Drive it entirely from the existing stress engine on the two seeded alerts. No new data, no new
  computation path. Pull the contrast from `StressTester.run(...)` for each.
- This view should be where the "aha" lands: minimal text, the two columns, the fork made
  visual. One sentence of framing at the top; the mechanism shown, not explained.

Tests: a smoke test that the Twin Cases view renders both alerts offline and shows the flag-based
load-bearing item for ALERT-01 and a reopen trigger for ALERT-16. (The underlying facts are
already asserted in `tests/test_stress.py` — reuse those alert IDs; do not re-prove the logic.)

End Phase 2: offline gate green; commit; docs updated; `DECISIONS.md` entry (PROPOSED).

---

## Phase 3 — Potential Impact: name the stakes and the user (reshape + light research)

Goal: a judge sees, in the app, who this is for and why a defensible decision matters — without
a single invented number (CLAUDE.md §4 forbids fabricated ROI/accuracy/cost figures).

- On the landing / Alert Queue (`page_alert_queue`), add a compact, honest impact framing:
  the real FIU-IND regime stakes — STR filing deadlines, that inspections examine decisions
  *not* to file, that undocumented dispositions carry regulatory consequence. Name the user in
  their own words (the bank's Principal Officer under PMLA / FIU-IND).
- **Source every regulatory claim** to the corpus already in `domain/corpus/` (PROVEN/ASSUMED
  rules only — never NEEDS-VERIFICATION; the invariant in CLAUDE.md §3 holds in UI text too) or
  to a primary source via a corpus rule ID. If a claim has no corpus backing, either add a
  properly-sourced corpus rule or cut the claim. Keep the synthetic-data caveat visible.
- Do NOT invent impact metrics. The real regulatory consequence is the impact story; the
  human's BFSI domain knowledge is the moat here, so keep the claims precise and defensible.

Tests: assert the impact framing renders and that any rule IDs it cites resolve to
PROVEN/ASSUMED corpus rows (fail if a NEEDS-VERIFICATION rule is referenced).

End Phase 3: offline gate green; commit; docs updated; `DECISIONS.md` entry (PROPOSED).

---

## Phase 4 — Technological Implementation: make platform use visible, then prove it live

Two parts. 4a is a reshape; **4b is the real blocker and needs the human's keys.**

**4a — Platform trace (reshape, do first).**
- Add a live **"Platform trace"** strip/panel showing, per run: which Nemotron tier answered each
  step (triage / reasoning / disposition), token cost per call, and — once Sandboxes are proven —
  that the calculator ran in a Token Factory Sandbox with its `BACKEND_RUN_REF`. The data already
  exists: `llm.last_call` (provider, tier, model, usage, latency), the agent trace's `tokens`,
  and `COMPUTE_RUNS.BACKEND_RUN_REF`. Surface it; do not invent it.
- Add the progress cues the judges explicitly asked for (slash-agent review): spinners / step
  indicators while the agent loop and stress branches run, so a viewer sees the system working.
- Until a real `BACKEND_RUN_REF` exists, label the Sandbox line honestly (ASSUMED / local
  fallback). Never claim sandbox execution works without a recorded run (CLAUDE.md §4).

**4b — Prove it live (needs the human; this gates the strongest claims).**
- With `NEBIUS_API_KEY` (and `TAVILY_API_KEY`) in `.env`:
  1. `python -m scripts.check_models --ping` → record output in `DECISIONS.md`; flips Token
     Factory + model IDs from ASSUMED → PROVEN.
  2. `python -m scripts.run_live_eval --alerts ALERT-01,ALERT-16` then a full run →
     commit the dated `evals/REPORT-<date>-live.md`. Only after this may any live number be
     quoted anywhere (README, video, Devpost).
  3. Sandbox probe (`scripts/probes/probe_sandbox.py`) → if a real `BACKEND_RUN_REF` lands in
     `COMPUTE_RUNS`, flip sandbox execution to PROVEN and update `HANDOFF.md`.
- If keys are not available this session: build 4a against the existing (possibly stub) data,
  leave 4b as the top open item in `HANDOFF.md`, and do not fabricate results.

End Phase 4: offline gate green; commit; docs updated; `DECISIONS.md` entries for any live
results (with date).

---

## Phase 5 — Submission polish (only after 1–4 land)

- README: ensure it still matches the app after the reshape; the two-minute story in the app now
  mirrors the README.
- A ≤2:50 video script (do not record — human does): 0:00–0:30 Twin Cases "aha"; 0:30–1:30 the
  Verdict card + "Show the proof" opening to the hashes and tiered Nemotron; 1:30–2:10 the agent
  loop with the platform trace + a rejected hallucinated submission; 2:10–2:50 the dated eval
  table and a spoken mention of Token Factory, the Nemotron tiers and Sandboxes.
- A short **Limitations** section for the Devpost (the judges reward documented limits as rigour):
  heuristics are not FIU-IND thresholds; most seeded alerts are single-summary-row; ledger is
  tamper-evident not tamper-proof; agent disposition is advisory.
- Devpost text + the mandatory platform feedback (human-side).

---

## Working rules for every phase

- Small commits, one concern each, present tense. Run the offline gate before every commit.
- Reshape, don't rebuild: if a phase can be done by moving/surfacing existing code, do that.
- Nothing is PROVEN without a test or a recorded run. Keep every claim labelled.
- Never invent numbers. Never reference a NEEDS-VERIFICATION corpus rule in UI text.
- Keep the five invariants in CLAUDE.md §3 intact; a change that breaks one is a bug.
- End each phase: offline gate green → commit → `CHANGES_SINCE_BASELINE.md` + `HANDOFF.md`
  updated → `DECISIONS.md` entry (PROPOSED unless the human decided). Tick `TASKS.md`.
- Commit/PR attribution: follow the lines the session's own reminder gives at the time of the
  commit (do not hard-code a model name here — it changes between sessions).

## Definition of done for this pass

A judge opening the app reaches a defensible verdict and what it rests on in under two minutes;
the twin-alert idea is legible in one view; the real-world stakes and user are named and sourced;
the platform use is visible; and the strongest technical claims are backed by a dated live eval
committed in `evals/`. The rigour (hashes, provenance, flip sets) is all still there — one click
away, not in the way.
