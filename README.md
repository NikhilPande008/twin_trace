# Twin Trace — every rupee traced

**An AML copilot for Indian bank Principal Officers. It shows what a decision rests on, which
evidence would change it, and why each figure in it can be defended to FIU-IND.**

Built for the **Nebius × NVIDIA Global AI Hackathon 2026** · Track: Best Apps & Agents
(+ Best Use of Tavily).

> **The model drafts. A fixed, hashed calculator supplies every number. A gate refuses anything
> else, again at the moment a decision is recorded.**
>
> All data in this repo is synthetic. Each capability is labelled **PROVEN** (a test or recorded
> run shows it), **STUBBED** or **ASSUMED**. Live status is in [HANDOFF.md](HANDOFF.md).

**Try it in three minutes (no API key needed):** run the app, open **Twin Cases** to see two
look-alike alerts and what each decision rests on, then **Proof Check** and try to slip a made-up
total past the gate, then **Decision Ledger** to check the hash chain and verify a decision package. **Measured Results** shows
every number we have, computed from dated reports, next to its limits.

**Why it matters.** FIU-IND received 4,33,761 STRs in FY 2021-22 and describes STR quality as
something it manages through engagement with banks; Indians lost ₹22,845.7 crore to cyber fraud in
2024 according to a Lok Sabha reply. Each alert needs a decision someone can defend later. What we
did and did not establish is in [docs/IMPACT.md](docs/IMPACT.md): no officer study has been run, and
we found no source for the claim that FIU-IND penalises templated narratives.

---

## The story in 30 seconds

Two alerts fire on the same rule on the same day. Each has ₹3,45,000 of credits from UPI handles
that pass straight out again. One is a money mule. The other is a family paying a hospital bill.

The Principal Officer must **file** one and **close** the other, then defend both decisions to an
FIU-IND inspector months later. Generic LLM copilots fail this job in two ways. They add up
figures themselves, and they sound certain. A PO cannot sign a Ground of Suspicion with a total
the model invented.

This copilot does three things instead.

1. **It never does the arithmetic.** Every ₹ figure comes from a fixed, hashed *calculator of
   record* or from a single transaction row. A draft that cites any other number cannot be
   marked ready.
2. **It stress-tests the decision.** The calculator is re-run on every plausible
   counter-hypothesis (*"what if this transaction is explained?"*, *"what if that registry flag
   is a false positive?"*). It then reports the smallest set of facts the decision hinges on.
   - For the mule (ALERT-01): **the FILE rests on a single fact, the I4C flag on handle C.** If
     that flag is a false positive, the verdict drops. So the Ground of Suspicion has to
     document it. (PROVEN: `test_file_rests_on_the_i4c_flag`.)
   - For the family (ALERT-16): **the NOT-FILE comes with reopen triggers.** If the hospital or
     the brother's handle later appears on a registry, the alert must reopen. Flagging the
     sister alone would not reopen it. (PROVEN: `test_not_file_twin_gets_reopen_triggers`.)
   - The app opens on this. The **Twin Cases** page puts both alerts side by side: same rules,
     same ₹3,45,000, one calculator signal different, and what each decision rests on. Every
     alert's Disposition Panel starts with both readings (if you file / if you close); the
     evidence, hashes and AI output are one toggle below. The opposite decisions are the
     scenario's labels: the stress test shows what each rests on; it does not choose.
3. **An agent investigates, and the system checks its work.** Nemotron decides which tools to
   call and in what order. Its final assessment is rejected and sent back if it cites a fact,
   transaction or rule that the tools never returned. It is also rejected if it contains a number
   that did not come from the calculator. (**PROVEN live** on 16 synthetic alerts, 2026-10-21
   09:12 UTC: 12/12 agreement on clear FILE/NOT_FILE; 16 submissions rejected by validation and
   corrected, across 12 alerts. Source: the final live report, below.)

Every step is written to an append-only, hash-chained ledger and an evidence table. A decision
can be reconstructed, and re-computed, from its hashes.

---

## What Twin Trace proves

| Every… | …is backed by | Status |
|---|---|---|
| ₹ figure in a Ground of Suspicion | a transaction amount **or** a calculator-of-record fact (stdlib-only program; code, input and output SHA-256 per run; `reproduce()` re-verifies) | PROVEN |
| "what if" in the stress test | its own branch run of the same program, linked to the base run (`PARENT_RUN_ID`, `HYPOTHESIS_JSON`) | PROVEN |
| agent tool call | an `EVIDENCE` row (`agent_step`) with a content hash and the model call behind it | PROVEN |
| decision | an append-only, **hash-chained** ledger row (DB triggers block UPDATE/DELETE) | PROVEN |
| regulatory answer | a PROVEN/ASSUMED corpus rule; NEEDS-VERIFICATION rules are never indexed; off-corpus questions get no answer | PROVEN |
| tipping-off request | a refusal before any model call | PROVEN |

---

## How it works

```
Alert ─► screen_request ─► calculator of record ─► Decision Stress Test ─► evidence ─► AI steps ─► PO decides ─► hash-chained ledger
          (tipping-off)     (hashed program,        (branch runs on            (Tavily:        (Nemotron     (AI shown last,
                             local or Sandbox)       counter-hypotheses,        adverse media,   Nano/Super/   anti-anchoring)
                                                     minimal flip sets)         regulator sites) Ultra)

Agentic investigator (Nemotron Super, tool calling, ≤10 steps):
  get_case · run_calculator · stress_test · lookup_rule · check_regulator_updates ·
  screen_adverse_media · submit_assessment  ──►  validated against tool outputs, or rejected
```

**Decision Stress Test** (`ddp/stress/`). Deterministic signals are computed from calculator
facts: flagged-counterparty share, cash structuring, rapid pass-through, fan-in and the multiple
of declared income. Each signal is a product heuristic, not a regulatory threshold. Counter-
hypotheses are searched smallest first, and only *minimal* flip sets are kept (no subset of a
reported set flips the verdict on its own). The search has a run budget and reports when that
budget is exhausted. An optional Nemotron memo turns the report into prose. It is thrown out if
it contains any number that is not a transaction amount or a fact value.

---

## Where Nebius Token Factory and NVIDIA Nemotron are used

| Step | Tier | Model (confirmed live 2026-10-21) |
|---|---|---|
| Anti-templating quality check, stress-test memo | triage | Nemotron 3 Nano 30B-A3B |
| 11-factor suspicion evaluation, **agentic investigator (tool calling)** | reasoning | Nemotron 3 Super 120B-A12B |
| Ground of Suspicion drafting | disposition | Nemotron 3 Ultra 550B |

- **Token Factory API** (`ddp/llm.py`, OpenAI-compatible). It handles `complete()` for
  structured steps and `chat()` with tools for the agent. Tool-call arguments are normalised:
  an empty string `""` is treated as `{}`.
- **Structured output** (`ddp/structured.py`). JSON schemas for every structured step. Mode is
  `json_object`, or `json_schema` with automatic fallback on HTTP 400. Every response is also
  **validated locally**, with one repair retry, and the step fails closed. Server-side
  constraints are not trusted on their own: reasoning models can escape them.
- **Visible in the app.** The Disposition Panel's *Platform trace* shows each tier, the model
  Token Factory reported, and the calls, tokens and seconds for that alert, built only from
  recorded calls. The stress test and the agent show their steps live while they run.
- **Token Factory Sandboxes.** `NebiusSandboxBackend` is written to run the calculator in a
  sandbox through `contree-sdk` and store the sandbox run reference per run. **Not run (blocked):**
  on 2026-10-21 the probe ran with both key and project ID set but received 403 Forbidden from
  `/sandboxes/v1/instances` — Sandboxes access is not provisioned on this account. The
  calculator runs in a local isolated subprocess, and the app says so. Details: [docs/PLATFORM_NOTES.md](docs/PLATFORM_NOTES.md).

## Where Tavily is used

- **Typology context** (`TavilyEvidenceSource`). A topic search built from the alert's typology
  only (e.g. "UPI money mule account pass-through fraud India"). No name, account, transaction
  or narrative text leaves the bank. Hits are labelled *not about this customer* and never
  count as evidence for a figure. Snippets are capped and marked untrusted.
- **Regulator updates** (`fetch_regulatory_updates`). Searches only rbi.org.in,
  fiuindia.gov.in, sebi.gov.in, enforcementdirectorate.gov.in, pib.gov.in and egazette.gov.in,
  using `include_domains` with a second domain check on the results. A question that contains
  any case identifier is refused, so no case data goes into a public search. Results are
  *unverified pointers* for the PO. They never become corpus rules.
- **Failure is never shown as "nothing found".** Every call records an outcome (`ok`,
  `no_results`, `no_key`, `refused`, `timeout`, `network_error`, `http_error`, `bad_response`),
  and each screen attempt is stored as evidence. The panel and the agent say "did not run" when
  it did not.
- **Live run (2026-10-21):** `python3 -m scripts.probes.probe_tavily` passed 6/6 cases, including
  a forced 401 and a forced timeout ([report](evals/TAVILY-PROBE-2026-10-21.md)). This is not
  entity screening: synthetic names searched on the public web could match real people, so the
  product deliberately searches typology, not customers.

---

## Quick start

```bash
pip install -r requirements.txt -c constraints.txt   # tested pins (Python 3.11+)
cp .env.example .env                  # add NEBIUS_API_KEY (and TAVILY_API_KEY)
python -m scripts.seed_db             # synthetic data
python -m scripts.check_models        # confirm model IDs against the live catalog
streamlit run app.py                  # Proof Check and the stress test work offline
```

Optional, for the Sandboxes backend only: `pip install contree-sdk`, set `NEBIUS_PROJECT_ID` in
`.env`, then `python3 -m scripts.probes.probe_sandbox` (see [PLATFORM_NOTES](docs/PLATFORM_NOTES.md)).

Offline (no key), the calculator, stress test, evidence gate, retrieval and ledger all work.
The Nemotron steps and the agent are disabled.

## Tests and evaluation

```bash
python -m pytest -q                         # offline tests, no network
python tests/eval_harness.py                # failure-mode scenarios
python -m scripts.run_live_eval --mock      # harness self-test → evals/REPORT-<date>-mock.md
python -m scripts.run_live_eval             # LIVE: Nemotron on all 16 alerts → evals/REPORT-<date>-live.md
python -m scripts.run_comparison --gate-only  # holdout: gate on seeded faults (deterministic)
python -m scripts.run_comparison            # LIVE: template vs model-without-controls vs full product
python -m scripts.verify_package <file>     # re-check an exported decision offline
```

Design and evidence documents: [validation contract](docs/VALIDATION_CONTRACT.md) ·
[decision package](docs/DECISION_PACKAGE.md) · [user journey](docs/USER_JOURNEY.md) ·
[claims register](docs/CLAIMS_REGISTER.md) · [impact and sources](docs/IMPACT.md) ·
[demo runbook](docs/DEMO_RUNBOOK.md) ·
[evaluations](evals/README.md) · [implementation status](docs/DESIGN_AND_TECH_IMPLEMENTATION.md)

**Live results, 2026-10-21 — 16 synthetic development alerts, Nemotron via Token Factory**
([report](evals/live-2026-10-21-final/REPORT-2026-10-21-live.md), 09:12 UTC):

| Metric | Result |
|---|---|
| 11-factor assessment: model output schema-valid | **16 / 16** — 14 first try, 2 after one repair (both first attempts were cut off at the token limit); 0 fallbacks |
| Agent agreement with gold on clear cases | **12 / 12** (9 FILE, 3 NOT_FILE). An always-FILE rule would score 9 / 12 |
| CONTESTED cases (ambiguous by design) | 4 — the agent chose FILE on all 4 (it leans towards filing) |
| Agent submissions rejected by validation and corrected | **16** across 12 alerts |
| Median time per alert | 26.0 s for the 11-factor assessment, 20.2 s for the agent |

Model output varies between runs: an earlier run the same morning
([report](evals/rerun-2026-10-21/REPORT-2026-10-21-live.md)) had 4 repairs and 19 rejected
submissions with the same 12 / 12 and 4 / 4. The first run that morning reported "16/16 valid" but
counted fallbacks; that figure is withdrawn ([DECISIONS.md](DECISIONS.md)).

**Holdout (6 synthetic cases, author-labelled — not expert ground truth):**

| Measure | Result |
|---|---|
| Seeded faulty narratives caught by the gate (deterministic) | **10 / 15**; 10 / 12 of the kinds it is designed to catch ([run](evals/RUN-20261021T074721Z-gate-only/REPORT.md)) |
| Supported narratives wrongly rejected | **0 / 11** |
| Same model drafting without the product's controls | 15 unsupported figures; **6 / 6** drafts had at least one ([run](evals/RUN-20261021T080109Z-live/REPORT.md)) |
| Full product | the drafter still produced unsupported figures in 3 / 6 drafts; the gate rejected those 3; **0** unsupported figures in the 3 it accepted |

Six cases support no general accuracy claim. Officer review time was not measured.

No accuracy, latency or cost figure is quoted anywhere unless it comes from a dated report in
`evals/`. Mock reports are stamped as mock.

## Limits (honest)

- The stress-test signals are **product heuristics**, not FIU-IND criteria. Most seeded alerts
  have a single summary transaction, so the calculator sees little in them. The stress test
  says this explicitly when a FILE rests on evidence outside the signals.
- The regulatory corpus is a snapshot: 13 of its 49 rules are NEEDS-VERIFICATION and excluded.
- The ledger is tamper-**evident**, not tamper-proof. The anti-templating checklist is a product
  heuristic.
- The agent's disposition is advisory and is shown last. The PO decides. In the dated run it
  chose FILE on all 4 contested cases: it leans towards filing.
- The twin alerts' opposite decisions are the scenario's labels. ALERT-16 models ELEVATED, not
  LOW; what clears it (a hospital invoice, family links) is in the case file, outside the
  calculator.
- The officer ID on a decision is self-asserted: this build has no sign-in.
- Not "compliant" or "FIU-IND approved". This tool helps write defensible decisions; it does not
  make them.

## Licence

To be added (TASKS T0.3).
