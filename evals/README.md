# Evaluations

Every number this project quotes must come from a file in this folder, with its date.

## Datasets

| Set | Where | Role | Labels |
|---|---|---|---|
| Development | `ddp/seed_data.py` (16 alerts, read-only) + `domain/scenarios/` (21) | prompts, rules and UI were built against these | scenario authors; synthetic |
| Holdout v1 | `holdout/HOLDOUT-v1.json` (6 cases) | measurement only; nothing is tuned on it | **author-assigned by the coding assistant, not expert ground truth**; pending human review |

The holdout is frozen: change it only by adding `HOLDOUT-v2.json`. Each run records the
dataset sha256.

## Commands

```bash
python3 -m scripts.run_comparison --gate-only     # A: gate on seeded faults (deterministic)
python3 -m scripts.run_comparison                 # A + B: three conditions, live models
python3 -m scripts.run_live_eval --tavily --out evals/<dir>   # 16 dev alerts, live
python3 -m scripts.probes.probe_tavily            # Tavily live probe
```

Use `--mock` for an offline self-test of either runner. Mock reports say MOCK and are not quoted.

## Conditions (holdout, Part B)

- **C1 template**: a structured manual template filled from calculator facts, with no model.
- **C2 baseline**: the same model drafts from the raw case, with no computed facts and no gate.
  This is evaluation only, not a product path.
- **C3 full**: the product: 11-factor assessment → drafter with calculator facts → hard gate.

## Metrics

| Metric | Definition |
|---|---|
| Unsupported figures | rupee figures in a draft that equal no transaction amount and no calculator INR fact, plus unreadable figures. Measured by the same validator for every condition |
| Drafts with any | drafts with at least one unsupported figure |
| Needs review | figures equal to a real amount but attached to a different counterparty |
| Accepted by gate | C3 drafts with `hard_gate_passed` |
| Unsupported in accepted | unsupported figures in gate-accepted drafts (the property the product claims) |
| Gate catch rate | seeded faults blocked or flagged ÷ all seeded faults; also reported for the faults the gate is designed to catch |
| False rejections | supported narratives the gate rejected |
| Tokens (all attempts) | summed across retries and repairs, not just the final call |
| Calculator reproduced | run re-executed from its saved input and archived program, same output hash |

Not measured: officer review time and corrections (needs real participants); decision accuracy
at any scale that supports a claim.

## Runs

| Date | File | What |
|---|---|---|
| 2026-10-21 | `REPORT-2026-10-21-live.md` | first 16-alert live run; its "16/16 valid" counted fallbacks (likely 14/16; see DECISIONS.md) |
| 2026-10-21 | `TAVILY-PROBE-2026-10-21.md` | Tavily live probe, 6/6 (topic queries) |
| 2026-10-21 | `RUN-20261021T074721Z-gate-only/` | holdout gate: 10/15 faults caught (10/12 designed), 0/11 false rejections |
| 2026-10-21 | `rerun-2026-10-21/` | 16 dev alerts live, Tavily injected: 16/16 model-valid (4 after repair, all truncation), agent 12/12 clear, 19 rejections |
| 2026-10-21 | `RUN-20261021T080109Z-live/` | holdout, three conditions: baseline 15 unsupported figures in 6/6 drafts; full product 3/6 drafts rejected by the gate, 0 unsupported in accepted |
