# CLAUDE.md — standing instructions for every session in this repo

You are working in **twin-trace**: the Nebius × NVIDIA Global AI Hackathon 2026
entry "Twin Trace". Read this file fully before doing anything.

## 0. Session start (always, in this order)

1. `CLAUDE.md` (this file)
2. `HANDOFF.md` — current state, what is PROVEN vs STUBBED vs ASSUMED, next step
3. `TASKS.md` — find the lowest-numbered open task in the current week
4. The last 3 entries of `DECISIONS.md`
5. `CHANGES_SINCE_BASELINE.md` — so you never re-describe reused work as new
6. Run the offline gate: `python -m pytest -q && python tests/eval_harness.py`.
   If it is red, fixing it is the first task, before any new feature.

## 1. Project scope

This is a standalone project. Never read from, import from, or write to any folder outside this
repo. No relative paths out of this repo, no symlinks, no git submodules, no shared virtualenv.

Domain assets in `domain/corpus/`, `domain/scenarios/` and `DOMAIN.md` belong to this project.
Edit them freely here. Archived docs in `docs/archive/` are history, not a spec.

## 2. What the product is (one paragraph — keep every change consistent with it)

An alert-disposition copilot for a bank's Principal Officer under India's PMLA / FIU-IND regime.
It produces decisions that can be defended to FIU-IND. Its key trace properties are:

(a) every ₹ figure in a Ground of Suspicion is either a single transaction amount or a fact from
the **calculator of record** (a fixed, hashed program run on the case transactions);
(b) every decision goes to an **append-only, hash-chained ledger** with model and compute
provenance;
(c) regulatory answers come only from PROVEN/ASSUMED corpus rules, and the system abstains when
nothing covers the question;
(d) tipping-off requests are refused.

Models come from Nebius Token Factory (tiered Nemotron); compute from a local isolated subprocess
today, and from Token Factory Sandboxes once T1.3 is done.

## 3. Invariants — a change that breaks one of these is a bug, whatever else it achieves

| Invariant | Enforced by |
|---|---|
| NEEDS-VERIFICATION rules never appear in any output | `ddp/retrieval.py` (never indexed) + `test_needs_verification_rules_unreachable` |
| Off-corpus questions return [] (abstain) | `CorpusIndex.coverage` + eval SCN-20 |
| A GoS citing a ₹ amount not in transactions or computed facts cannot be READY | `validate_gos_evidence` + tests |
| DECISION_LEDGER / COMPUTE_RUNS: no UPDATE, no DELETE | SQLite triggers in `ddp/store.py` |
| Ledger rows are hash-chained; `verify_ledger_chain()` passes on an untouched DB | `ddp/store.py` + tests |
| Tipping-off requests are refused before any model call | `screen_request` + eval SCN-22 |
| The 11 POE factors, the checklist items and `CHECKLIST_BASIS` wording are unchanged | review; baseline diff |
| AI recommendation is shown LAST (anti-anchoring) | `app.py` layout |
| `ddp/compute/aggregations.py` is stdlib-only and imports nothing from this repo | review; it is executed in isolation |
| Regulatory thresholds are passed in as parameters tied to a corpus rule ID, never hard-coded in the program | `ddp/bootstrap.PARAM_SOURCES` |

## 4. Claim discipline (applies to code comments, docs, README, video script, Devpost text)

Label every non-trivial claim **PROVEN** (a test or a recorded run demonstrates it), **STUBBED**
(interface exists but does not do the real thing yet), or **ASSUMED** (believed but not
verified). Current status is tracked in `HANDOFF.md §2`.

- Never say sandbox execution works until a real `BACKEND_RUN_REF` from Nebius appears in
  `COMPUTE_RUNS` and `HANDOFF.md` records the run.
- Model IDs and the base URL are ASSUMED until `python -m scripts.check_models` passes. Record the
  output in `DECISIONS.md`.
- Never invent numbers: no accuracy, latency, cost or "x% fewer hallucinations" figures unless
  they come from a harness run committed in this repo with its date.
- Never claim "compliant", "FIU-IND approved" or "tamper-proof". The ledger is tamper-**evident**.
  The checklist is a product heuristic (DG-09), not an FIU-IND standard.
- All data is synthetic. Token Factory Sandboxes (beta) must not receive personal or sensitive
  data. Do not add real customer data, real names or real account numbers, ever.

## 5. How to work

- Small commits, one concern each, present tense ("add Tavily adverse-media step"). Run the
  offline gate before every commit.
- When a feature lands, add a row to `CHANGES_SINCE_BASELINE.md` (what was added or changed).
- Record any real design choice as a new entry at the bottom of `DECISIONS.md`. It is append-only:
  never edit old entries. To reverse a decision, add a new entry that supersedes it. Mark each
  entry **FIRM** (the human decided) or **PROPOSED** (you decided; the human to confirm).
- At session end, update `HANDOFF.md` (state, what changed, next step, blockers) and tick
  `TASKS.md`.
- New skills take a `tier` ("triage" | "reasoning" | "disposition"), never a model ID.
- Any new number the product shows must come from the calculator of record or a transaction row.
  If a new figure is needed, add it to `aggregations.py` with a derivation string and a test.
- Scope guard: before starting anything not in `TASKS.md`, say so and ask. The deadline is fixed
  (see §6) and a second concurrent hackathon competes for the same hours.

## 6. Event constraints (verified 2026-09-26; re-check the Devpost page if in doubt)

- Deadline: **Fri 30 Oct 2026, 10:00 PDT = 22:30 IST.** Internal target: submit Wed 28 Oct.
- Track: Best Apps & Agents (+ Best Use of Tavily bonus). Judged on Technological Implementation
  (tie-breaker), Design, Potential Impact and Quality of the Idea, equally weighted. Judges may
  use only the text, images and a ≤3-minute video.
- Hard gates: a runtime call to Token Factory, **and** at least one NVIDIA open model. A public
  repo with an OSS licence visible, and a README showing where Nemotron and Token Factory are
  used.
- LICENSE is absent pending the human's licence selection (TASKS T0.3). Do not add one on your own.

## 7. Commands

```bash
pip install -r requirements.txt
cp .env.example .env                 # add NEBIUS_API_KEY
python -m scripts.seed_db            # build data/ddp.sqlite3 (idempotent)
python -m scripts.check_models       # verify model ids against the live catalog
streamlit run app.py                 # UI (works offline; AI features need the key)
python -m pytest -q                  # offline gate (no network)
python tests/eval_harness.py         # failure-mode scenarios
```

## 8. Map

```
app.py                   Streamlit UI (5 pages)
ddp/config.py            env + model tiers
ddp/llm.py               Token Factory client (OpenAI-compatible), FunctionLLM for tests
ddp/store.py             SQLite schema, append-only triggers, hash chain
ddp/retrieval.py         BM25 over PROVEN/ASSUMED rules, abstention
ddp/skills.py            workflow skills (ported) + computed-fact evidence gate
ddp/compute/             calculator of record (aggregations.py = the hashed program; runner.py = backends + provenance)
ddp/bootstrap.py         wiring + regulatory params (PARAM_SOURCES)
ddp/seed_data.py         16 synthetic alerts + 31 transactions
ddp/corpus_loader.py     YAML -> corpus rows
domain/                  corpus (49 rules), 21 scenarios
design/                  UI design docs (still valid)
docs/archive/            archived session and design docs
tests/                   offline suites (all run without network)
```
