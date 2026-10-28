# JUDGING_AUDIT.md — where the project stands against the four judging criteria

**Date:** 2026-10-22 · **Phase 0 of** `docs/BUILD_PROMPT_JUDGING.md` · **No code changed.**
**Reviewed by the human:** yes, 2026-10-22; chose option (b) in §6.

Method: read CLAUDE.md, HANDOFF.md, DECISIONS.md, CHANGES_SINCE_BASELINE.md and README.md; ran the
offline gate; ran the app (`streamlit run app.py`, key configured) in a 1440×900 browser and walked it
as a first-time judge; timed the stress test with and without a model; read the layout order in
`app.py`. Every statement below comes from one of those. Scores are deliberately harsh.

**One framing fact drives the scoring.** CLAUDE.md §6: judges "may use only the text, images and a
≤3-minute video". They will not click through the app. Design, Idea and Impact are scored from
**what fits in recorded frames and the Devpost text**. Anything that needs scrolling, a click, or a
30-second wait is effectively invisible unless the video shows it.

---

## 1. The prompt's premises, checked

`BUILD_PROMPT_JUDGING.md` was written from an older snapshot. These premises are out of date:

| Premise in the prompt | Actual state (2026-10-22) | Source |
|---|---|---|
| "80 pytest, eval_harness 8/8" | **345 pytest** pass; eval_harness 24/24 checks (8/8 scenarios); eval_harness_v2 25/26 (1 live skip) | run today |
| "NOT yet proven live on Nebius (no API keys)" | **Proven live.** Token Factory URL + 3 Nemotron model IDs confirmed 2026-10-21 (`check_models --ping`, DECISIONS.md); full 16-alert live eval committed in `evals/live-2026-10-21-final/`, quoted in README and pinned by `tests/test_evidence_view.py` | HANDOFF §5d, §5i |
| Phase 4b step 2: run `run_live_eval --alerts ALERT-01,ALERT-16` | Already done as part of the 16-alert run | same |
| Sandboxes ASSUMED | **BLOCKED**: probe ran with key and project ID; HTTP 403 from `/sandboxes/v1/instances` (beta not provisioned) | DECISIONS.md 2026-10-21 |
| "five pages" | **Seven**: Alert Queue, Proof Check, Disposition Panel, Decision Ledger, Dashboard, Measured Results, Regulatory Reference | `app.py:1858` |
| Verdict needs to be computed from the stress test | A plain-language headline already exists (`ddp/stress/headline.py`, T9.6). It is just buried | `app.py:915` |
| "each phase ends with a commit" | The human does all git by hand; Claude does not commit (standing instruction). Phase ends will list changed files instead | memory, HANDOFF §5i |

So Phase 4b reduces to one item (Sandboxes, waiting on Nebius), and Phase 1 is mostly **moving
existing output up**, not building it.

---

## 2. Walking the app as a judge

### Alert Queue (landing page)
- **First view:** "What am I looking at?" expander, open by default: ~150 words of prose, then four
  metric tiles (16 awaiting, 16 overdue, ₹5.87Cr pending), then a five-control filter bar, then 16
  rows. The stakes are in the prose, not in anything a viewer's eye lands on.
- **To the core value:** read the intro, find ALERT-01 in the list, click "Review →".
- "16 overdue" is the first number shown. On synthetic data dated weeks ago, this reads like a
  broken demo, not an urgent queue.

### Proof Check — the strongest screen in the app
- Two columns: "A draft with an invented total" → red **Blocked. ₹3,95,000 is not a transaction
  amount or a calculator fact.** next to "The same draft with the calculator's figure" → green
  **Passes**. Currency-spelling toggle above. Readable in ~10 s. No key needed.
- This is already the "comparison view" the judges praised. It is the model for Phase 2.
- Weakness: the intro paragraph above it is dense; the page is second in the nav, but the intro on
  the landing page sends the viewer there only by text.

### Disposition Panel (ALERT-01) — the backwards screen
Measured at 1440×900 (viewport height 900 px):

| Element | Position from top | Notes |
|---|---|---|
| Case header, `Not yet known: AI assessment not run` | above the fold | first message is a gap |
| Alert narrative (blockquote) | above the fold | |
| Signal Brief: 4 metric tiles + 3 captions | above the fold | |
| Right column: empty Ground of Suspicion text box, Officer ID, date/time, FINGate ref | above the fold | form before any finding |
| Calculator of record: fact list + derivations + **SHA-256 provenance line** | ~1 screen down | |
| "Decision sensitivity (stress test)" heading | **~1,400 px** | |
| "Run stress test" button + FILE/NOT_FILE radio | **~1,540 px** | must click |
| Headline "This FILE rests on exactly one fact." | **~1,650 px, after the click** | the aha |
| AI suspicion assessment | ~1,890 px | needs key |
| Agentic investigation | ~2,140 px | needs key |
| Page height | ~2,720 px (3 screens) | before any AI output |

- **Time to verdict:** the deterministic stress test takes **0.52 s (ALERT-01) and 0.11 s
  (ALERT-16)** (timed today, no model). In the running app with a key configured, the same click
  took about **25–35 s**, because `_stress_panel` passes `with_memo=_llm_ready()` and waits for a
  Nemotron memo before showing anything (`app.py:902`). The aha is gated on a model call it does not
  need.
- **The twin trap.** The intro tells the viewer to open ALERT-16 "and see what would reopen it".
  The radio defaults to **FILE**. Opening ALERT-16 and clicking "Run stress test" therefore shows
  *"This FILE rests on any one of 3 facts"* (it tests a FILE for the family), not the reopen
  conditions. A judge following the app's own instructions gets the wrong half of the story unless
  they also flip the radio. Verified today in code and by running the engine.
- **Order of the evidence column:** narrative → signal brief → calculator (with hashes) → stress test
  → typology search → red-flag codes → rule lookup → AI assessment → agent → run trace. Technical
  justification (derivation strings, run IDs, code/input/output hashes) appears ~1,000 px before
  the one sentence saying what the decision rests on. This is exactly the profile the judges
  penalised.
- **Labels everywhere.** Each section carries a kind badge ("Source facts", "Product heuristic",
  "Model interpretation", "Unverified external", "Officer conclusion") plus a caption plus a help
  icon. Individually honest; together they are the "text-heavy screen that buries the call to
  action".

### Decision Ledger
- Hash-chain status, per-decision expanders, "Reconstruct decision" with a Reproduce button,
  package download and an upload verifier. Strong substance, all below expanders. Fine as a
  "proof" page; not a first-impression page.

### Dashboard
- Stock Streamlit: metric tiles, `st.bar_chart` of alert types, a list of signal sources, a token
  table. Caption reads "Key metrics FIU-IND inspectors focus on", but the alert-to-STR ratio is
  labelled in the corpus as an **internal governance metric** (INS-003, ASSUMED) and the help text
  itself says "no FIU-IND benchmark published". The caption overstates; Phase 3 should fix the
  wording. Little here helps any criterion.

### Measured Results / Regulatory Reference
- Measured Results is honest and well sourced (computed from committed reports, limits shown
  expanded). Regulatory Reference works. Neither is a first-impression page. Both are good material
  for a single frame in the video.

### Styling ("default LLM-generated" check)
Reads as stock Streamlit dark theme: `primaryColor #1a6eb5` (Streamlit-like blue), default fonts,
default metric tiles, emoji in headings and icons (🏦 🔍 ✍️ 🔴 🟠 ⚪ ✅ ⛔ ↻ ↩), many italic captions.
The colour work that exists is good and tested (WCAG AA, `ddp/palette.py`), but there is no visual
identity: no single accent, no verdict-coloured surface, no deliberate type scale. A judge
watching a video will place it as "a Streamlit prototype".

---

## 3. Scores (1–5, against the published rubric, as seen by a video-only judge)

### Design — **2 / 5**
- **Evidence for:** Proof Check is a clear, complete two-column comparison. Accessibility
  contrast is enforced by a test. Mobile/tablet layouts were checked earlier (CHANGES row "UI
  (brief D1–D4)").
- **Gap:** no aha in under two minutes on the main page; verdict ~1.7 screens down, behind a
  click, and behind a 25–35 s model call when a key is set. Form fields before findings. Twin path
  broken by the default radio. Generic styling.
- **Closing it:** reshape. The headline, flip sets, reopen triggers and summary already exist
  (`ddp/stress/headline.py`, `engine.py:104–128`). Move them up, run without the memo, relocate the
  rest into "Show the proof". Small new code: one card component, one CSS block.

### Quality of the Idea — **3 / 5**
- **Evidence for:** the idea is genuinely non-obvious and has three layers that no generic AML
  copilot shows: a calculator of record that owns every number; minimal flip sets ("this FILE rests
  on one fact"); reopen triggers for closures. The README tells it in 30 seconds.
- **Gap:** the app never shows the twins together. Seeing the fork needs: open ALERT-01, scroll,
  click; switch to ALERT-16, scroll, flip the radio, click — six interactions and three scrolls.
  Unless the video does that by hand, the idea is invisible.
- **Honesty constraint for Phase 2 (important):** the calculator does **not** decide the twins
  differ. ALERT-01 models **HIGH**, ALERT-16 models **ELEVATED**, not LOW (four signals fire on
  ALERT-01 and three of those also fire on ALERT-16; the flagged-counterparty signal is the
  difference). The opposite dispositions come from the gold labels / the officer (the hospital
  invoice is in the KYC and narrative, outside the calculator). What the system shows is **what each
  decision rests on and what would overturn it**. The Twin Cases view must say "proposed FILE" /
  "proposed closure", not "the system decided". Overclaiming here is the easiest way to lose a domain
  judge.
- **Closing it:** reshape. Two stress-test runs (0.6 s total, offline) side by side.

### Potential Impact — **2 / 5**
- **Evidence for:** `docs/IMPACT.md` is unusually careful: sourced figures (FIU-IND 4,33,761 STRs
  FY 2021-22; ₹22,845.7 crore cyber-fraud loss 2024 via a reported Lok Sabha reply), reasoning
  labelled as reasoning, and a NOT ESTABLISHED list. README "Why it matters" uses only those.
- **Gap:** in the app, the user and stakes live in one prose expander. None of the regulatory stakes
  that make a *defensible* decision matter are shown with a citation, although the corpus already
  has them:
  - STR-002 (PROVEN): file within **7 working days** of forming suspicion.
  - INS-001 (ASSUMED, labelled internal governance per DG-13): inspectors examine alerts that were
    **not** filed; an undocumented not-filed rationale is a recognised risk.
  - INS-002 (PROVEN): filing decisions must be made by the designated Principal Officer.
  - SB-003 / STR-004 (PROVEN): tipping-off is prohibited.
  - RR-001 (PROVEN): transaction records kept for 5 years.
- **Must stay out:** INS-004 (templated narratives) is NEEDS-VERIFICATION. No penalty or fine rule
  exists in the corpus; any "penalty" claim needs a new properly sourced rule or must be cut.
- **Closing it:** reshape + copy. A compact "Who this is for / what is at stake" strip with rule-ID
  chips that resolve to PROVEN/ASSUMED rows, plus a test. No new numbers.

### Technological Implementation — **3 / 5** (substance 4, visibility 2)
- **Evidence for (substance):** live Token Factory calls on three Nemotron tiers with a committed,
  dated eval (16/16 schema-valid, 12/12 agreement on clear cases, 16 validation rejections
  corrected); agent with validated tool submissions; hash-chained, trigger-enforced ledger;
  reproducible hashed calculator with branch runs; exact rupee parser; 345 offline tests; live
  Tavily probe 6/6.
- **Gap (visibility):** which tier answered which step is only in a collapsed "Pipeline run trace"
  at the bottom of the evidence column and a token table at the bottom of the Dashboard. The sidebar
  says "Compute: local". Nothing on screen says *Nemotron Nano / Super / Ultra* while it works.
  Spinners exist ("Evaluating against 11 factors…", "Investigating…") but there are no step
  indicators for the agent loop or stress branches.
- **Sandboxes:** blocked on Nebius (403). It cannot be claimed and should not be implied by the
  platform strip. Proven-live already beats it; do not spend hours here.
- **Closing it:** reshape (4a). Data exists: `llm.last_call`, `RunTrace` steps, agent `tokens`,
  `COMPUTE_RUNS.BACKEND`/`BACKEND_RUN_REF`.

### Summary table

| Criterion | Score | Main gap | Fix type |
|---|---|---|---|
| Design | 2 | Verdict buried ~1,650 px, behind a click and a model call; twin radio trap; stock styling | Reshape (Phase 1) |
| Quality of the Idea | 3 | The twin fork is never on one screen | Reshape (Phase 2) |
| Potential Impact | 2 | Stakes and user not shown in-app; corpus rules not surfaced | Reshape + copy (Phase 3) |
| Technological Implementation | 3 | Proven depth is invisible on screen | Reshape (Phase 4a) |

---

## 4. Inventory — built, tested, and confirmed running today

| Component | Location | Confirmed today |
|---|---|---|
| Decision Stress Test | `ddp/stress/engine.py`, `signals.py`, `hypotheses.py` | ran ALERT-01 FILE (HIGH, flip size 1, 0.52 s) and ALERT-16 NOT_FILE (ELEVATED, 3 reopen triggers, 0.11 s); also in the running app |
| Stress headline | `ddp/stress/headline.py` | output checked for both twins |
| Calculator of record | `ddp/compute/aggregations.py`, `runner.py` | runs on page load (provenance line visible) |
| Agent | `ddp/agent.py` | `run_live_eval --mock` on ALERT-01/16: submitted FILE / NOT_FILE; live results in `evals/live-2026-10-21-final/` |
| Structured output | `ddp/structured.py` | covered by pytest; mock eval `assess=success` |
| Live eval runner | `scripts/run_live_eval.py` | `--mock --alerts ALERT-01,ALERT-16` wrote a report to the scratchpad (not to `evals/`) |
| Proof Check | `ddp/proofcheck.py`, `page_proof_check` | viewed in the running app |
| Measured Results | `ddp/evidence_view.py` | pytest |
| Package verifier | `ddp/package.py` | pytest |
| Run trace | `ddp/pipeline.py` `RunTrace` | pytest (`test_app_pipeline.py`) |
| Palette + contrast test | `ddp/palette.py`, `tests/test_accessibility.py` | pytest — any new Phase 1 colour must pass this test |

Reshape phases should import these, not copy them.

---

## 5. Hard blockers and items only the human can do

Ordered by how much they can cost the submission.

1. **Git history / baseline tag.** `git tag` returns nothing; the repo has one commit ("first
   commit"). CLAUDE.md §1 and README/CHANGES rely on `baseline-this platform-2026-09-25..HEAD` as the
   Devpost "significantly updated" evidence. Today that command fails. This outranks every UI
   change: without it the "pre-existing project" explanation is unverifiable.
   `docs/PRE_SUBMISSION_REVIEW.md` already flags it.
2. **LICENSE (T0.3).** A visible OSS licence in a public repo is a hard gate (CLAUDE.md §6). Still
   absent pending the this platform IP check.
3. **Sandboxes (T9.3).** 403, beta not provisioned. Request access; re-run
   `python3 -m scripts.probes.probe_sandbox` only if it arrives. Otherwise keep "ASSUMED / local".
4. **Video and Devpost text.** Judges see only these. Phases 1–2 exist to give the video its first
   60 seconds.
5. **CI** (`.github/workflows/ci.yml`) has never run on GitHub.
6. **Open domain calls:** holdout labels (T8.11), `tipping_off_str` audience (T8.12).
7. **Decision needed for Phase 1 (see §6).**

Not blockers: hosting (judges cannot use it), more live eval runs (one dated run is committed and
quoted).

---

## 6. Recommended phase order

1. **Human, first:** restore the baseline tag/history and settle the licence (items 1–2 above).
   No UI work fixes those.
2. **Phase 1 + Phase 2 together.** Build one "verdict card" component and use it twice: once at the
   top of the Disposition Panel, twice side by side on a Twin Cases page. Run the stress test
   deterministically (`with_memo=False`) on page load, so the card is instant; keep the memo button
   inside "Show the proof". Fix the default-radio trap as part of this.
3. **Phase 3** (small): stakes strip with rule-ID chips (STR-002, INS-001, INS-002, SB-003) and a
   test that every cited ID is PROVEN/ASSUMED. Correct the Dashboard caption.
4. **Phase 4a:** platform strip (tier → model → tokens → seconds per step; compute backend shown
   honestly as "local subprocess"; Sandboxes "not available on this account").
5. **Phase 5:** README/video script/Limitations.
6. **Phase 4b:** only the Sandboxes probe, only if Nebius grants access.

### Decision for the human before Phase 1
The stress test checks a **proposed** disposition; it does not produce one. The Verdict card needs
a proposal to check. Options:
- **(a) Default from the modeled level** (HIGH → check a FILE; ELEVATED/LOW → check a closure),
  with a visible toggle. ALERT-01 → FILE, ALERT-16 → closure, matching the story. Risk: a default
  *is* a nudge, though deterministic, not the AI's.
- **(b) Show both readings** on the card ("If you file, it rests on… / If you close, reopen
  if…"). No nudge at all; slightly more text.
- **(c) The officer picks first**, card appears after. Most anti-anchoring; adds a click before the
  aha.

Recommendation: **(b)** on the Disposition Panel (no anchoring question at all) and the
proposed-disposition pairing from the scenario on the Twin Cases page, labelled as such. If the
human prefers (a), log it FIRM in DECISIONS.md.
