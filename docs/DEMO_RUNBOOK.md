# Demo runbook and video script (≤ 2:50)

Rehearse twice from a fresh browser session before recording. Every spoken line below is a
behaviour with a test or a dated run behind it (see `CLAIMS_REGISTER.md`). Do not say anything that
is not in that register. Judges see only the video, the text and the images: what is not on screen
does not exist for them.

## Before you start

```bash
pip install -r requirements.txt -c constraints.txt
python -m scripts.seed_db          # fresh synthetic data
DDP_DEMO_MODE=1 streamlit run app.py   # every browser session gets fresh in-memory data
```

- `.env` has `NEBIUS_API_KEY` (and `TAVILY_API_KEY` if you show search).
- Browser at 1440×900 or larger, sidebar open, zoom 100%. Close other tabs.
- Live model steps take time (median 26.0 s assessment, 20.2 s agent in the dated run). Record the
  waits and cut them in editing; keep the status panel on screen for a second so the viewer sees
  the steps happen. Never speed up or fake a result.
- Have the final live report open in a tab: `evals/live-2026-10-21-final/REPORT-2026-10-21-live.md`
  (or the in-app **Measured Results** page).

## Script

| Time | Show | Say (only this) | Must be on screen |
|---|---|---|---|
| 0:00–0:08 | Alert Queue, top | "A bank's Principal Officer has to decide, for each alert, file a report with FIU-IND or close it, and defend that choice later." | "Who this is for" card, the four cited rules (STR-002, INS-001, INS-002, SB-003) |
| 0:08–0:30 | **Twin Cases →** | "These two alerts fired the same rules on the same three lakh forty-five thousand rupees. One was filed, one closed. The calculator finds one difference: a flagged counterparty. The filing rests on exactly one fact. The closure comes with three conditions that would reopen it." | Table with every row "same" except the highlighted **the difference** row; ALERT-01 card *This FILE rests on exactly one fact*; ALERT-16 card *reopen conditions* (brother, hospital, father) |
| 0:30–0:50 | **Open ALERT-01 →** | "Every alert opens on both readings: if you file, if you close. No model was used for this; it is thirty-two runs of a fixed, hashed calculator." | Verdict card with both halves; footer *Deterministic: 32 runs … no model* |
| 0:50–1:10 | Toggle **Show the proof**; scroll through the calculator panel and the stress-test branches | "The proof is one click down: each figure, its derivation, the transactions it came from, and the code, input and output hashes of the run." | `F-TOTAL-CREDIT`, `F-TOTAL-DEBIT` with txn IDs; the run line with code / input / output hashes; *All 23 branches* |
| 1:10–1:30 | Click **Run 11-Factor Assessment**; cut the wait; then scroll up to the **Platform trace** | "The AI assessment runs on Nemotron through Nebius Token Factory, shown after the evidence. The platform trace shows which tier answered: Super for reasoning, Nano for checks, Ultra for drafting." | Spinner naming *nemotron-3-super-120b-a12b (reasoning tier)*; platform strip with the reasoning tier showing *1 call(s) · … tokens* |
| 1:30–2:05 | Alert selector → **ALERT-02**; Show the proof → **Run investigator**; cut the wait but keep the status lines | "An agent investigates with tools. It chooses what to look at; it cannot invent evidence. When its answer cites a number or a fact the tools never returned, the submission is rejected and sent back." | Status panel lines *Step n: Nemotron (reasoning tier) chooses…*, tool names, and **submit_assessment: rejected by validation, sent back**, then *accepted* |
| 2:05–2:20 | **Proof Check** | "The same rule holds for the officer's own text. A made-up total is blocked however it is written, and cannot be recorded." | Left: **Blocked.** ₹3,95,000; right: **Passes**; switch to *lakh* |
| 2:20–2:50 | **Measured Results** (or the report tab) | "On sixteen synthetic alerts, live on the twenty-first of October: sixteen of sixteen assessments were valid model output, two after one repair. On the twelve clear cases the agent agreed twelve of twelve; an always-file rule would get nine. It chose to file on all four contested ones. Sixteen submissions were rejected by validation and corrected. Models: Nemotron Nano, Super and Ultra on Token Factory. The calculator runs in a local isolated subprocess; our Sandboxes access was refused, and the app says so. Synthetic data, results and limits are in the repo." | The dated table; date and *16 synthetic alerts* visible |

The spoken lines are 299 words, about 2:10 at a calm 140 words a minute, leaving room for the
cut-down waits. Cut the 2:05–2:20 beat
first if over time.

### If the agent beat does not show a rejection

Model output varies between runs (the dated runs had 16 and 19 rejections). If ALERT-02 is accepted
first time, try **ALERT-07** once. If that is also clean, keep the run (say "this time it got it
right first time") and let the Proof Check beat carry the rejection. Do not re-run until it fails.

## If something fails live

| Failure | What to do |
|---|---|
| Model call fails (sidebar: *last call failed*; strip shows *failed*) | Say so. Show 0:00–1:10 and 2:05–2:50, which need no model. Do not fake a result |
| Assessment shows *fallback* | Say "the model output did not parse; the app shows placeholders, not a result" and move on |
| Tavily *did not run* | Skip it; it is optional context |
| Package verify fails | Stop and investigate; do not record the video |

## Extra beats (if a second take or the deck needs them)

- **Decision Ledger**: record a decision, *Hash chain verified*, download the package, then
  `python3 -m scripts.verify_package <file>` → **PACKAGE VERIFIED**. Upload it in-app; it never
  runs code it does not trust.
- **Tipping-off**: in the Ground of Suspicion, type `We informed the customer that an STR has been
  filed.` → record → *Not recorded — policy gate: tipping_off_customer*.

## Never say

"compliant", "FIU-IND approved", "tamper-proof", "every claim verified", "hallucination rate",
"runs in Sandboxes", or any accuracy, time-saved or cost figure that is not in
`CLAIMS_REGISTER.md`. Do not call the twins' decisions the system's decisions: they are the
scenario's labels.
