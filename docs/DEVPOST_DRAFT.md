# Devpost draft — for the human to edit and paste

Status: **draft, 2026-10-22.** Every claim below is in `docs/CLAIMS_REGISTER.md`; keep it that way
when editing. Numbers carry their date and denominator. The human owns the final text, the
platform-feedback section and the submission.

---

## Name
Twin Trace — every rupee traced

## Tagline (≤ 200 chars)
An AML copilot for Indian bank Principal Officers that shows what each file-or-close decision rests
on, what would overturn it, and why every rupee in it can be defended to FIU-IND.

## Inspiration
In India, a bank's Principal Officer decides for every alert whether to file a Suspicious
Transaction Report with FIU-IND or close it, and must be able to defend either choice at
inspection. FIU-IND received 4,33,761 STRs in FY 2021-22 and describes STR quality as something it
works on with banks (FIU-IND Annual Report 2021-22, §3.2.1). The written reasoning, and the
numbers in it, is the part that has to survive scrutiny months later. A language model that adds up
figures itself and sounds certain is the wrong tool for that job.

## What it does
- **Twin Cases.** Two synthetic alerts fire the same rules on the same ₹3,45,000. One is a mule
  account, one a family paying a hospital bill. The app puts them side by side: the calculator finds
  one different signal (a flagged counterparty); the filing rests on exactly one fact; the closure
  comes with three conditions that would reopen it.
- **Both readings, before any AI.** Every alert opens on what a FILE would rest on and what would
  reopen a closure, computed by re-running a fixed, hashed calculator on every counter-hypothesis
  (32 runs for ALERT-01, no model). The officer chooses; the evidence and hashes are one click down.
- **Every rupee cited.** A figure in the Ground of Suspicion must equal a transaction amount or a
  calculator fact, however it is written (₹, Rs., INR, lakh, crore). Anything else is blocked, again
  at the moment of recording.
- **An agent that cannot invent evidence.** Nemotron Super investigates with tools; a submission
  citing a number, fact or rule the tools never returned is rejected and sent back.
- **A ledger you can re-check.** Decisions go to an append-only, hash-chained ledger and export as a
  package anyone can verify offline. Requests to tip off the customer are refused before any model
  call.

## How we built it
- **Nebius Token Factory + NVIDIA Nemotron**, three tiers: Nano 30B (quality check, stress-test
  memo), Super 120B (11-factor assessment, tool-calling agent), Ultra 550B (Ground of Suspicion
  draft). Each step asks for a tier, never a model ID; the ledger records which model answered. The
  app's *Platform trace* shows the tier, the model Token Factory reported, and tokens and seconds
  for every call.
- **Structured output:** `json_object` mode, local schema validation, one repair retry, fail closed.
- **Calculator of record:** a stdlib-only Python program run in an isolated subprocess, with code,
  input and output SHA-256 recorded per run; counter-hypotheses are branch runs of the same program.
- **Tavily:** typology context (no customer data leaves the bank) and a regulator-only search
  (RBI, FIU-IND, SEBI and others); failures are shown as "did not run", never as "nothing found".
- Streamlit UI, SQLite with database triggers for append-only tables, 368 offline tests.

## Measured results (synthetic data; dated)
Live run, 2026-10-21 09:12 UTC, 16 synthetic alerts (`evals/live-2026-10-21-final/`):
- 11-factor assessment: 16/16 schema-valid model output (14 first try, 2 after one repair; 0
  fallbacks).
- Agent: 12/12 agreement on the clear cases (9 FILE, 3 NOT_FILE); an always-FILE rule would score
  9/12. It chose FILE on all 4 contested cases. 16 submissions were rejected by validation and
  corrected, across 12 alerts. Output varies run to run: an earlier run had 19 rejections, same
  12/12.
- Holdout, 6 author-labelled cases: the same model drafting without the product's controls put
  unsupported figures in 6/6 drafts; with the product, the drafter still did in 3/6 and the gate
  rejected all 3; 0 unsupported figures in accepted drafts. Six cases support no general claim.

## Challenges we ran into
- Nemotron's reasoning tokens count against `max_tokens`; early structured calls came back empty or
  truncated until the budget was raised. Both repairs in the dated run followed truncation.
- Our first gate read only `₹<digits>`; "Rs.", "INR" and "lakh" spellings of an invented total got
  through. We replaced it with an exact parser and re-check at recording.
- Token Factory Sandboxes: we wrote the backend against the real SDK, but our account was refused
  access (HTTP 403), so the calculator runs locally and the app says so.

## Accomplishments we're proud of
- The decision's dependencies are computed, not narrated: "this FILE rests on exactly one fact".
- A model-written number cannot reach the ledger, in any spelling.
- Every public number traces to a committed, dated report, and the withdrawn one is labelled.

## What we learned
Trust boundaries matter more than prompts: the drafter still produced unsupported figures in half
the holdout drafts, and the deterministic gate is what kept them out.

## What's next
- Run the calculator in Token Factory Sandboxes once access is granted.
- Richer seed transactions: most alerts are one summary row, so only 1 of 9 gold-FILE alerts
  reaches a HIGH modeled level today.
- A Nemotron content-safety layer for paraphrased tipping-off (the current gate is regex).

## Limitations
- All data is synthetic. Not "compliant" and not FIU-IND approved; the tool helps write defensible
  decisions, it does not make them.
- Stress-test signals and the anti-templating checklist are product heuristics, not FIU-IND
  criteria.
- The twins' opposite decisions are the scenario's labels; the stress test shows what each rests on
  but does not choose. ALERT-16 models ELEVATED, not LOW.
- The figure gate checks values, not meaning: a true figure in a false sentence passes.
- The ledger is tamper-evident, not tamper-proof. The officer ID is self-asserted (no sign-in).
- The agent's disposition is advisory and shown last; it leans towards filing on contested cases.
- The regulatory corpus is a dated snapshot; 13 of 49 rules are NEEDS-VERIFICATION and never used.
- No officer study: no time-saved or error-rate claim.

## What we built
This project was built for the Nebius × NVIDIA Global AI Hackathon 2026. We built the
calculator of record, the hash-chained ledger, the decision stress test, the agent, structured
output, the Tavily steps, the Token Factory integration and the reshaped UI. The full feature
list is in `CHANGES_SINCE_BASELINE.md`.

## Built with
python · streamlit · sqlite · nebius-token-factory · nvidia-nemotron · tavily · contree-sdk

---

## Platform feedback — facts to draw on (write it in your own words)
From DECISIONS.md and PLATFORM_NOTES.md:
1. **Reasoning tokens and `max_tokens`.** Super and Ultra spend `reasoning_tokens` inside
   `max_tokens`; at 16 the Super ping returned an empty string. The docs could say this and suggest
   a budget for structured output.
2. **Base URL confusion.** `api.studio.nebius.com` returned 401 with our key;
   `api.tokenfactory.nebius.com/v1/` worked.
3. **Model ID casing differs by tier:** `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`,
   `nvidia/nemotron-3-super-120b-a12b`, `nvidia/Nemotron-3-Ultra-550b-a55b`.
4. **Sandboxes SDK.** The `ContreeClient` → `ContreeSync` recipe we had taken from our reading of
   the docs (check the current docs before saying they are wrong) raised
   `AttributeError` with `contree-sdk` 0.3.6; the working shape was
   `ContreeSync(config=ContreeConfig(auth=IAMAuth(token, project_id)))`. Without a project the API
   answered 400 `Missing "Project" header`; with one, `/sandboxes/v1/instances` answered 403 with no
   pointer to how to request access.
5. **What worked well:** `json_object` mode for the structured steps on Nano and Super (drafting on
   Ultra is free text); OpenAI-compatible tool calling for the agent, after treating empty-string
   arguments as `{}`.
