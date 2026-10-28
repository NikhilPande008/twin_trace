# Agent filing lean: before and after the 2026-10-28 prompt change

Dev set: the 16 seeded alerts on the current seed (gold labels by the scenario authors). Holdout: 6 frozen cases (`holdout/HOLDOUT-v1.json`, author-assigned labels, not expert ground truth). Agent: Nemotron reasoning tier via Token Factory, live. Two runs per condition; model output varies between runs, so a change counts only if both runs show it. Every number below is read from the linked run files by `scripts/agent_lean_report.py`.

## Development set (16 alerts: 12 clear, 4 contested)

| condition | run | agent prompt | clear cases agreeing | contested filed | contested dispositions | clear cases missed | rejected submissions |
|---|---|---|---|---|---|---|---|
| before | [`live-2026-10-28-seed`](live-2026-10-28-seed/) | `9e7cba49cc89…` | 12 / 12 | 4 / 4 | ALERT-03 FILE, ALERT-11 FILE, ALERT-13 FILE, ALERT-14 FILE | — | 14 |
| before | [`agent-dev-2026-10-28-before-2`](agent-dev-2026-10-28-before-2/) | `9e7cba49cc89…` | 12 / 12 | 4 / 4 | ALERT-03 FILE, ALERT-11 FILE, ALERT-13 FILE, ALERT-14 FILE | — | 13 |
| after | [`agent-dev-2026-10-28-after-1`](agent-dev-2026-10-28-after-1/) | `da5a3d567297…` | 10 / 12 | 3 / 4 | ALERT-03 FILE, ALERT-11 NEEDS_MORE_INFO, ALERT-13 FILE, ALERT-14 FILE | ALERT-12 FILE→NEEDS_MORE_INFO, ALERT-15 FILE→NEEDS_MORE_INFO | 11 |
| after | [`agent-dev-2026-10-28-after-2`](agent-dev-2026-10-28-after-2/) | `da5a3d567297…` | 12 / 12 | 3 / 4 | ALERT-03 FILE, ALERT-11 NEEDS_MORE_INFO, ALERT-13 FILE, ALERT-14 FILE | — | 12 |

## Holdout (6 cases: 4 clear, 2 contested)

| condition | run | agent prompt | clear cases agreeing | contested filed | contested dispositions | clear cases missed | rejected submissions |
|---|---|---|---|---|---|---|---|
| before | [`agent-holdout-2026-10-28-before-1`](agent-holdout-2026-10-28-before-1/) | `9e7cba49cc89…` | 4 / 4 | 2 / 2 | H-03 FILE, H-05 FILE | — | 4 |
| before | [`agent-holdout-2026-10-28-before-2`](agent-holdout-2026-10-28-before-2/) | `9e7cba49cc89…` | 4 / 4 | 2 / 2 | H-03 FILE, H-05 FILE | — | 4 |
| after | [`agent-holdout-2026-10-28-after-1`](agent-holdout-2026-10-28-after-1/) | `da5a3d567297…` | 3 / 4 | 1 / 2 | H-03 FILE, H-05 NEEDS_MORE_INFO | H-02 NOT_FILE→FILE | 2 |
| after | [`agent-holdout-2026-10-28-after-2`](agent-holdout-2026-10-28-after-2/) | `da5a3d567297…` | 4 / 4 | 2 / 2 | H-03 FILE, H-05 FILE | — | 3 |

The disposition stays advisory and is shown last in the app; the officer decides.
