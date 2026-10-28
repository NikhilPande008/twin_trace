# Judge evaluation — 2026-10-28

Role-played scoring of **Twin Trace** (Nebius × NVIDIA Global AI Hackathon 2026, Best Apps & Agents +
Best Use of Tavily) as the judging panel would see it, with ~2 days left before the Fri 30 Oct
22:30 IST deadline. Read and run only; this file is the only thing written.

**What was looked at.** The public repo `NikhilPande008/twin_trace` (fresh clone into a scratch
directory, README quick-start followed as written), the local working tree, `README.md`,
`HANDOFF.md`, the last 5 `DECISIONS.md` entries, `CHANGES_SINCE_BASELINE.md`, `docs/DEVPOST_DRAFT.md`,
`docs/DEMO_RUNBOOK.md`, `docs/CLAIMS_REGISTER.md`, everything under `evals/`, `data/ddp.sqlite3`
(read-only) and `gh repo view`. The app was walked in the browser on the user's running instance
(Alert Queue, Twin Cases, Disposition Panel for ALERT-01). That server stopped mid-walk, so the other
five pages (Proof Check, Decision Ledger, Dashboard, Measured Results, Regulatory Reference) were
rendered headlessly from the public clone with Streamlit `AppTest` in demo mode, with no key. No
model call was made.

**Premise check.** The brief says the entry is already submitted. The repo does not show that:
`TASKS.md` T5.1 (video), T5.2 (Devpost text) and T5.3 (submit) are all unticked, and no video link
appears anywhere. This report scores what exists and treats the video as a plan, not a finished thing.

---

## Blockers (from §B)

1. **No video.** None is in the repo or linked from the README or the Devpost draft, and T5.1 is
   open. Judges may use only the text, images and a video of 3 minutes or less. Without a video
   there is effectively no entry. What exists is a strong script (`docs/DEMO_RUNBOOK.md`, 299
   spoken words).
2. **The public repo contradicts the licence gate.** GitHub reports `licenseInfo: mit` and
   `LICENSE` is MIT, but the **public** `README.md` ends with "## Licence — To be added (TASKS
   T0.3)", and the public `CLAUDE.md` says "LICENSE is absent pending the human's licence
   selection". The local fix exists but has not been pushed (`git diff README.md`). A judge who
   scrolls to the end sees "To be added".
3. **The public repo has the broken live path.** The 2026-10-28 output-budget fix (`ddp/config.py`,
   `ddp/llm.py`, `ddp/skills.py`, `app.py`, plus tests) is uncommitted. Your own DECISIONS entry says
   that without it, live 11-factor assessments fell back to 11 × `insufficient_data` and the Ultra
   draft returned half-finished reasoning as the narrative. A judge who adds a key to the public code
   hits that.

---

## A. Headline

**Verdict: a genuinely well-engineered, unusually honest entry that is not yet judgeable.** The
technology is real and proven live by a dated, committed report. Three Nemotron tiers run on Token
Factory. A tool-calling agent has its submissions rejected by deterministic validation (16 times
across 12 alerts in the quoted run). A hashed calculator of record supplies every rupee, and a
counterfactual stress test computes what each decision rests on. The twin-alert framing makes the
idea readable on one screen. The claim discipline is the best I would expect to see in this field:
I found no invented numbers and no "compliant" or "tamper-proof" wording. Everything limiting the
score is packaging. There is no video. The public README still says the licence is "To be added".
The public code is a day behind a live-path fix. And the strongest screens can only be seen by
cloning and running Streamlit, because there is no hosted demo and no screenshot in the README.

**Score: 14 / 20** if the video follows the runbook. Tech 4 · Design 3 · Impact 3 · Idea 4.

- **Single thing limiting the score:** the video does not exist. Design and Idea both depend on a
  judge seeing the Twin Cases screen, and right now nothing shows it to them.
- **Single highest-leverage 2-day fix:** push the pending commit, then record the runbook video on
  that code with one live rehearsal first. Put the video link and three screenshots at the top of
  the README.

---

## B. Hard-gate check

| Gate | Result | Evidence seen |
|---|---|---|
| Runtime call to Nebius Token Factory | **PASS** | `DECISIONS.md` 2026-10-21 (T0.4): `check_models --ping` → `https://api.tokenfactory.nebius.com/v1/` HTTP 200, 28 models, 3/3 tiers answered. `evals/live-2026-10-21-final/REPORT-2026-10-21-live.md` (09:12 UTC, LIVE): 16 alerts with per-alert seconds and tokens (for example the ALERT-01 agent: 11,731 tokens, 11.3 s). The running app's sidebar read "Models (Token Factory): Configured · last call succeeded". |
| NVIDIA open model invoked | **PASS** | Report header: `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`, `nvidia/nemotron-3-super-120b-a12b`, `nvidia/Nemotron-3-Ultra-550b-a55b`. Code: `ddp/agent.py` `TIER = "reasoning"`; tiers in `ddp/config.py`. |
| OSS licence present | **PASS, judge-visible contradiction** | `LICENSE` is MIT (© 2026 Nikhil Pande); `gh repo view` → `visibility: PUBLIC`, `licenseInfo: mit`. The public README says "To be added". The fix is local and unpushed (Blocker 2). |
| README shows where Nemotron and Token Factory are used | **PASS** | README "Where Nebius Token Factory and NVIDIA Nemotron are used": a tier → step → model table, `ddp/llm.py`, `ddp/structured.py`, and the in-app Platform trace. It matches the code. |
| Video of 3 minutes or less | **FAIL (not present)** | No file or link. T5.1 open. Script in `docs/DEMO_RUNBOOK.md`. |
| (Not a gate) Sandboxes | Disclosed honestly | `COMPUTE_RUNS`: 1,040 rows, all `BACKEND='local'`, 0 with a `BACKEND_RUN_REF`. README, app strip and claims register all say BLOCKED (HTTP 403). The app reads "Token Factory Sandboxes: not used — the probe was refused (HTTP 403 …)". |

**Quick-start as a stranger (public clone, Python 3.14.3, fresh venv):** `pip install -r
requirements.txt -c constraints.txt` OK → `cp .env.example .env` → `python -m scripts.seed_db` →
"corpus 49, alerts 16, transactions 31; ledger chain ok" → `python -m pytest -q` **446 passed** →
`python tests/eval_harness.py` **24 checks passed, 0 failed; Scenarios 8/8**. All 8 pages render with
no exceptions. **The README runs as written.** One small trap: on this Mac `python` is not on PATH
(only `python3`), so the README's `python -m …` lines fail outside a venv.

**Local working tree:** `python3 -m pytest -q` → **451 passed in 47.57 s**, eval harness 24/24.
The 5-test gap is the unpushed fix.

---

## C. Scores

### 1. Technological Implementation — 4 / 5 (tie-breaker)

**What justifies it.**
- Nemotron use is meaningful, not a wrapper. There are three tiers chosen per step (Nano for checks,
  Super for the 11-factor assessment and the agent, Ultra for drafting), and each skill asks for a
  tier, not a model ID. The agent (`ddp/agent.py`) runs a bounded tool loop over 7 tools. Its
  `submit_assessment` is rejected and sent back when it cites a fact, transaction or rule the tools
  never returned, or a number that is not a transaction amount or calculator fact. The dated run
  shows this happening: 16 rejections across 12 alerts. I checked the per-row sum, the 12/12 on clear
  cases (9 FILE + 3 NOT_FILE) and the medians (26.0 s and 20.2 s) against the report table, and they
  match.
- Structured output uses `json_object` with local schema validation, one repair, and fails closed.
- The calculator of record is stdlib-only, with code, input and output SHA-256 recorded per run and
  `reproduce()`. The stress test runs counterfactual branches (`PARENT_RUN_ID`, `HYPOTHESIS_JSON`) and
  keeps only minimal flip sets.
- The ledger is hash-chained and protected by SQLite triggers. Decision packages verify offline.
- 446 offline tests pass on the public repo.
- The Platform trace strip on the Disposition Panel makes the platform use visible without reading
  code.

**What caps it at 4.**
- The public code is one fix behind the live path the video will show (Blocker 3). The agent `chat()`
  path and the stress memo were **not** re-run live on the new budget (DECISIONS 2026-10-28, "Not
  checked live").
- The eval reports cite revisions `cccac3d` and `9e3333a`, which are not in the public one-commit
  history. The explanation in `evals/README.md` is also unpushed, so a judge cannot tie a report to
  code.
- Sandboxes are blocked (403). That is not your fault and is disclosed well, but it is still a
  missing piece of platform depth.

**What a 5 looks like:** the same system, a public repo whose HEAD is the code that produced a live
run dated after the last behavioural change, and a video that shows one agent rejection happening
live with the platform strip on screen. **Realistic in 2 days: yes.** It needs a push plus one live
re-run (`python -m scripts.run_live_eval`, committed as `evals/REPORT-2026-10-29-live.md`).

### 2. Design — 3 / 5

**What I saw.**
- **Alert Queue (landing):** a "Start here" box with a **Twin Cases →** button above the fold, then a
  "Who this is for / What is at stake" table with cited rule chips. The call to action is clear.
- **Twin Cases:** the best screen in the entry. A same/same/same table with one highlighted **the
  difference** row (flagged counterparty), then two cards: "This FILE rests on exactly one fact." and
  "This closure comes with reopen conditions." (Brother / City General Hospital / Father). It reads in
  about 10 seconds. This is the aha moment, and it can be reached in one click.
- **Disposition Panel (ALERT-01):** the verdict card ("What the decision rests on", both readings,
  "Deterministic: 32 runs … no model") is above the fold. The Platform trace comes next, and the proof
  sits behind a toggle. The AI comes last, as intended.
- **Proof Check:** a strong interactive demo. "**Blocked.** `₹3,95,000` is not a transaction amount
  or a calculator fact" sits beside "**Passes the figure check.** … ₹3,45,000 ← F-TOTAL-CREDIT". It
  works with no key.

**Where a judge docks points.**
- **No judge can see any of this without cloning.** There is no hosted demo (T9.12 pending), and the
  README has **no images**, although `docs/screenshots/` holds four. The first screen of the README
  is about 230 lines of dense prose and tables.
- **The look is stock Streamlit** with custom colour tokens: sidebar radio navigation across 8 pages,
  expanders and captions. It is competent and accessible (contrast-tested), but it reads as a
  template, not as an intentional product.
- **Jargon in the hero card.** The "Rests on" chips read "no explanation for T01-3 + no explanation
  for T01-5" and "no explanation for T01-1 + … + T01-4 +1 more in the proof". These are transaction
  IDs in the most important sentence on the page.
- **A rounded figure in the header of the core page.** `app.py:635` renders "Alerted amount
  ₹345,000 (3.5L)": Western digit grouping, where every other screen uses ₹3,45,000, and a lakh
  figure rounded from 3.45 to 3.5. Your own holdout flags a rounded figure as a fault (H-01, "Roughly
  ₹3 lakh"). A domain judge will notice this on the page whose whole point is that every rupee is
  exact.
- 8 pages is a lot for a 3-minute story. The Dashboard and Regulatory Reference are not in the
  runbook and add nothing to the pitch.

**What a 5 looks like:** a judge sees the Twin Cases screen within 10 seconds of opening the README
or video, and the hero sentence is in plain language. **Realistic in 2 days:** partly. The README
screenshots and the hero GIF take about an hour. The chip wording and the `3.5L` fix are small UI
copy changes, but they mean touching code during freeze, so do them only with a re-run of the gate.
A visual redesign is not worth it.

### 3. Potential Impact — 3 / 5

**What I saw.** The user is named precisely: a bank's Principal Officer under PMLA, filing or
closing each alert and defending that choice to FIU-IND. The landing card ties the stakes to cited
corpus rules (STR-002 PROVEN, INS-001 ASSUMED, …). README numbers carry sources: 4,33,761 STRs in
FY 2021-22 (FIU-IND Annual Report, primary), and ₹22,845.7 crore lost to cyber fraud in 2024 (a
secondary report of a Lok Sabha reply, labelled as such in `docs/IMPACT.md`). "No officer study has
been run" is stated openly.

**What caps it.**
- There is no user or practitioner signal: no quote, no interview, no pilot. "This is the real
  bottleneck" rests on the builder's reading of the regulation.
- The cyber-fraud figure is about fraud losses, not about the cost of weak STR narratives. A
  skeptical judge sees a big number loosely attached to the problem.
- The audience is a narrow regulatory niche (Indian POs). That is credible, but judges unfamiliar
  with PMLA need one sentence on why a bad Ground of Suspicion hurts the bank: inspection findings,
  penalties under PMLA s.13. Use that sentence only if a PROVEN corpus rule backs it.

**What a 5 looks like:** one real practitioner sentence (even an anonymised AML officer saying "we
get asked to justify closed alerts"), plus a problem statement in money or risk terms that is
sourced to the reporting duty itself. **Realistic in 2 days:** only if you already know someone
to ask. Otherwise leave it: the honest framing is worth more than a weak quote.

### 4. Quality of the Idea — 4 / 5

**What I saw.** The idea is non-obvious and shows real domain understanding:
- the model drafts but never adds up;
- a hashed calculator of record supplies every number;
- the decision's dependencies are computed by counterfactual branch runs ("this FILE rests on
  exactly one fact"), not narrated;
- the twin alerts show it. Same rules, same ₹3,45,000, one signal different, opposite outcomes.

The twin contrast is **legible, not hidden**. It is the second sentence of the README story, the
landing page's call to action, and beat 2 of the video script. The anti-anchoring order (AI shown
last) and the tipping-off refusal show the builder understands how a PO actually works.

**What caps it.** The opposite decisions are the scenario's own labels (disclosed: "the stress test
does not choose them"), and ALERT-16 models ELEVATED, not LOW. A sharp judge may ask "so the system
can't tell the twins apart?" The answer — "it shows what each decision rests on, and the closure's
evidence is in the case file" — is subtle and needs to be said in the video in one line, not left
in Limitations. Most seeded alerts are one summary transaction, so the calculator sees little on 15
of the 16 (disclosed: 1 of 9 gold-FILE alerts reaches HIGH).

**What a 5 looks like:** the video says, in one sentence, "the system doesn't decide — it tells
you exactly which fact your decision depends on, so you know what to document." **Realistic:** yes,
it is a script line.

---

## D. Best Use of Tavily (bonus) — weak contender (2 / 5)

**What exists, and it is thoughtful.** There are two uses. A typology search that deliberately
sends no customer data ("UPI money mule account pass-through fraud India"). A regulator-only search
restricted with `include_domains` to rbi.org.in, fiuindia.gov.in and four others, with a second
domain check and a refusal when the question contains a case identifier. Every outcome is recorded
(`ok`, `no_results`, `refused`, `timeout`, …) and never shown as "nothing found". A live probe passed
6/6 including a forced 401 and a forced timeout (`evals/TAVILY-PROBE-2026-10-21.md`). The privacy
reasoning for not doing entity screening is a real design decision.

**Why it scores low for the bonus.**
- **It changes no decision.** Results are labelled "not about this customer" and never count as
  evidence. That is correct for the domain, but it reads as decoration to a Tavily judge.
- **Both twins get the identical query and identical results** (probe: ALERT-01 and ALERT-16 both
  sent the same typology string and got the same 5 hits). The feature cannot tell the hero cases
  apart.
- **It is not in the video.** The runbook never shows Tavily, and its failure table says "Tavily
  did not run — skip it; it is optional context." Invisible to judges.
- **The naming overclaims.** The agent tool is called `screen_adverse_media`, and the docstring at
  `ddp/agent.py:13` says "adverse-media search on the case subject". The README diagram says
  "(Tavily: adverse media, regulator sites)". The code does typology search, as the README body
  correctly says. A judge reading code sees "adverse media screening" that is not screening.

**Cheapest lift:** a 10-second video beat on the regulator-only search (a live RBI/FIU-IND result
shown as an *unverified pointer*, and the refusal when a case ID is in the question), plus one
README sentence on why it refuses to screen names. That moves this from "checkbox" to "thought
about". Do not build entity screening.

---

## E. Claim-integrity flags

None of these is a hype claim. The entry's claim discipline is strong: no "compliant", no
"tamper-proof" except as "not tamper-proof", no NEEDS-VERIFICATION leak in the UI (the sidebar shows
the count only, "13 (excluded from output)"), and every quoted metric matches a dated file. The flags
are drift and wording a careful judge could catch.

1. **The public README says "Licence: To be added (TASKS T0.3)."** It is a gate-adjacent
   contradiction of `LICENSE` and GitHub's MIT detection (local fix unpushed).
2. **The Devpost draft says "451 offline tests (count on 2026-10-28)".** The public repo runs **446**.
   This becomes true once you push; until then a judge who runs the tests sees a different number.
3. **Report revisions cannot be traced.** The Measured Results page caption says "code revision
   `9e3333a`", and README metrics depend on reports at `cccac3d` / `9e3333a`. Neither exists in the
   public history. The `evals/README.md` note explaining this is unpushed.
4. **"PROVEN live" figures predate a behavioural change.** The README presents the 2026-10-21 run as
   current. The 2026-10-28 budget change altered the model-call path, and the claims register says
   so ("the dated 2026-10-21 reports predate this change"), but the README does not.
5. **Provenance exposure (git history).** The public repo has one commit, `302a2b2 first commit`,
   dated 2026-10-28 13:52 IST: 185 files and 28,217 lines. There are no tags locally or on the remote
   (`baseline-snowflake-2026-09-25` is gone). Meanwhile public files refer to reused baseline work:
   `CLAUDE.md` §8 says "workflow skills (ported)", and `CHANGES_SINCE_BASELINE.md` says "(baseline:
   application convention only)". The Devpost draft's "What we built" says "This project was built
   for the … Hackathon" and does not mention the baseline. If an organiser checks the "significantly
   updated during the Submission Period" rule, there is no commit history to show it, and the docs
   point to an undisclosed earlier codebase. This is the one integrity risk that could matter more
   than score.
6. **Rounded figure in the UI.** `app.py:635` "₹345,000 (3.5L)": 3.5 lakh is not a transaction
   amount or a calculator fact, and the product's thesis forbids exactly this. It is display, not a
   Ground of Suspicion, so no invariant is broken, but it is visible on the hero page.
7. **"Append-only … evidence table" ambiguity.** The README says "Every step is written to an
   append-only, hash-chained ledger and an evidence table". `ddp/store.py` has UPDATE/DELETE triggers
   on `PROGRAMS`, `DECISION_LEDGER` and `COMPUTE_RUNS` only, not on `EVIDENCE` (EVIDENCE rows carry
   content hashes). The sentence can be read as claiming EVIDENCE is append-only.
8. **Dashboard header "Key FIU-IND Inspection Metrics".** This overstates. The caption underneath
   correctly says the ratio is an internal governance metric (INS-003, ASSUMED) with no FIU-IND
   benchmark. The header has not changed since the 2026-10-22 audit flagged it.
9. **Tavily "adverse media" naming.** See §D.

What I checked and found clean: the README live table against
`evals/live-2026-10-21-final/REPORT-2026-10-21-live.md` (16/16, 14+2, 12/12, 4/4, 16 rejections, 26.0 s /
20.2 s); the holdout figures against `evals/RUN-*`; the withdrawn "16/16" is labelled as withdrawn; the
Sandboxes claim reads "not run (blocked)" everywhere; the Twin Cases footer says the scenario
decisions are author labels; the glossary says "Tamper-evident, not tamper-proof"; and the POE list is
described as "this product's compilation, not an FIU-IND-issued checklist".

---

## F. The 2-day fix list, ranked by score gained ÷ effort

| # | Fix | Lifts | Expected move | Type | Hours | Needs the human? |
|---|---|---|---|---|---|---|
| 1 | **Review and push the pending commit** (output-budget fix, licence wording, `evals/README` revisions note, CLAUDE/TASKS/DECISIONS). Closes Blockers 2–3 and flags 1–3. | Gate, Tech | Removes a gate-visible contradiction; protects Tech 4 | reshape | 0.5 | **Yes** (review, commit, push) |
| 2 | **One live rehearsal on the pushed code**, then `python -m scripts.run_live_eval` and commit the dated report. This proves the agent `chat()` path and stress memo on the new budget, and the README can quote a run matching HEAD. | Tech | Tech 4 → 4.5 (a run tied to public code) | reshape | 1.5 (mostly waiting) | **Yes** (key, credits) |
| 3 | **Record the video from `DEMO_RUNBOOK.md`.** Add one line on "the system doesn't decide, it shows what your decision rests on", and a 10-second Tavily regulator-search beat if time allows (cut Proof Check first if over 3:00). | Gate, Design, Idea, Tavily | Gate FAIL → PASS; Design +1, Idea holds 4, Tavily 2 → 3 | new (human) | 4–6 | **Yes** |
| 4 | **Top of README:** the video link, then 2–3 screenshots (Twin Cases, verdict card, Proof Check "Blocked"), above the prose. `docs/screenshots/` already exists; re-shoot Twin Cases. | Design, Idea | Design +0.5 (judges see the aha moment without cloning) | reshape | 1 | Partly (screens need the running app) |
| 5 | **Provenance statement in Devpost**, one honest paragraph: what existed before the submission period (the ported baseline), what was built during it (point to `CHANGES_SINCE_BASELINE.md`), and that history was squashed into one public commit on 2026-10-28. If the pre-squash history or the baseline tag still exists anywhere, push it as a tag. | Integrity (all four) | Avoids an eligibility challenge, not points | reshape | 0.5–2 | **Yes** (only the human knows what history survives) |
| 6 | **Copy fixes, no logic:** `app.py:635` "₹3,45,000" (drop "(3.5L)"); the Dashboard header to "Internal governance metrics"; README sentence 7 → "an append-only, hash-chained ledger and a content-hashed evidence table"; `ddp/agent.py:13` docstring → "typology search (no case data)". Re-run the offline gate. | Design, integrity | Small, but removes things a domain judge would catch | reshape | 0.75 | No (but feature freeze: human approves) |
| 7 | **Devpost text:** fix "451" only after the push; write the platform feedback in your own words (separate prize, T5.2); state "one sentence why a weak GoS hurts a bank" from a PROVEN rule. | Impact, platform prize | Impact holds 3; enables the feedback prize | reshape | 1.5 | **Yes** |

**Not worth touching in 2 days:**
- Sandboxes (blocked by account access; already disclosed well).
- A hosted demo (deploy risk, session isolation, a public key). Screenshots and the video do the same
  job for judges.
- A UI redesign, or richer seed transactions (T6.6).
- Entity screening via Tavily, or a Nemotron safety layer for tipping-off.
- More eval cases. Six holdout cases will not become a credible accuracy claim by Friday, and the
  entry already says so.

**Order of work:** today, #1 → #6 → #2. Tomorrow, #3 → #4. Then #5 and #7 with the Devpost form, and
Friday stays buffer.
