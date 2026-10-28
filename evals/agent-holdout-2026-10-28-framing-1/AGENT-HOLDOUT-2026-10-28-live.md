# Agent on the holdout — 2026-10-28T14:17 UTC (LIVE)

- Dataset: `HOLDOUT-v1.json` (sha256 `e7aaad6ae4d9…`), 6 synthetic cases; labels author-assigned, not expert ground truth
- Agent prompt sha256 `9e7cba49cc89…` · code `0bac93c+uncommitted`
- Models: `{"triage": "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B", "reasoning": "nvidia/nemotron-3-super-120b-a12b", "disposition": "nvidia/Nemotron-3-Ultra-550b-a55b"}`

Clear cases agreeing with the expected disposition: **3 of 4** · contested cases filed: **2 of 2** · rejected submissions: **6**.

| case | expected | status | agent | tool calls | rejected | tokens | seconds |
|---|---|---|---|---|---|---|---|
| H-01 | FILE | submitted | FILE | 7 | 2 | 20609 | 19.743 |
| H-02 | NOT_FILE | submitted | FILE | 5 | 0 | 10220 | 9.094 |
| H-03 | CONTESTED | submitted | FILE | 8 | 3 | 21049 | 23.06 |
| H-04 | FILE | submitted | FILE | 6 | 1 | 19612 | 20.555 |
| H-05 | CONTESTED | submitted | FILE | 5 | 0 | 10255 | 8.597 |
| H-06 | NOT_FILE | submitted | NOT_FILE | 5 | 0 | 10642 | 10.644 |

Reproduce: `python -m scripts.run_agent_holdout`.
