# Agent filing lean: before and after the 2026-10-28 stress-summary framing fix

Same agent prompt in every run. The only change is the stress-test summary the agent's `stress_test` tool returns: a FILE on LOW signals (or a closure on HIGH) is no longer summarised as robust. Dev set: 16 seeded alerts, current seed. Holdout: 6 frozen cases, author-assigned labels, not expert ground truth. Two runs per condition; a change counts only if both runs show it. Numbers are read from the linked run files by `scripts/agent_lean_report.py --framing`.

## Development set (16 alerts: 12 clear, 4 contested)

| condition | run | agent prompt | stress engine | clear cases agreeing | contested filed | contested dispositions | clear cases missed | rejected submissions |
|---|---|---|---|---|---|---|---|---|
| before | [`live-2026-10-28-seed`](live-2026-10-28-seed/) | `9e7cba49cc89…` | previous (not recorded) | 12 / 12 | 4 / 4 | ALERT-03 FILE, ALERT-11 FILE, ALERT-13 FILE, ALERT-14 FILE | — | 14 |
| before | [`agent-dev-2026-10-28-before-2`](agent-dev-2026-10-28-before-2/) | `9e7cba49cc89…` | previous (not recorded) | 12 / 12 | 4 / 4 | ALERT-03 FILE, ALERT-11 FILE, ALERT-13 FILE, ALERT-14 FILE | — | 13 |
| framing fix | [`agent-dev-2026-10-28-framing-1`](agent-dev-2026-10-28-framing-1/) | `9e7cba49cc89…` | `70f878781abf…` | 12 / 12 | 4 / 4 | ALERT-03 FILE, ALERT-11 FILE, ALERT-13 FILE, ALERT-14 FILE | — | 12 |
| framing fix | [`agent-dev-2026-10-28-framing-2`](agent-dev-2026-10-28-framing-2/) | `9e7cba49cc89…` | `70f878781abf…` | 12 / 12 | 4 / 4 | ALERT-03 FILE, ALERT-11 FILE, ALERT-13 FILE, ALERT-14 FILE | — | 13 |

## Holdout (6 cases: 4 clear, 2 contested)

| condition | run | agent prompt | stress engine | clear cases agreeing | contested filed | contested dispositions | clear cases missed | rejected submissions |
|---|---|---|---|---|---|---|---|---|
| before | [`agent-holdout-2026-10-28-before-1`](agent-holdout-2026-10-28-before-1/) | `9e7cba49cc89…` | previous (not recorded) | 4 / 4 | 2 / 2 | H-03 FILE, H-05 FILE | — | 4 |
| before | [`agent-holdout-2026-10-28-before-2`](agent-holdout-2026-10-28-before-2/) | `9e7cba49cc89…` | previous (not recorded) | 4 / 4 | 2 / 2 | H-03 FILE, H-05 FILE | — | 4 |
| framing fix | [`agent-holdout-2026-10-28-framing-1`](agent-holdout-2026-10-28-framing-1/) | `9e7cba49cc89…` | `70f878781abf…` | 3 / 4 | 2 / 2 | H-03 FILE, H-05 FILE | H-02 NOT_FILE→FILE | 6 |
| framing fix | [`agent-holdout-2026-10-28-framing-2`](agent-holdout-2026-10-28-framing-2/) | `9e7cba49cc89…` | `70f878781abf…` | 4 / 4 | 2 / 2 | H-03 FILE, H-05 FILE | — | 2 |

The disposition stays advisory and is shown last in the app; the officer decides.
