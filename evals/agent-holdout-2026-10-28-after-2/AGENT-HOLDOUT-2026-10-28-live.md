# Agent on the holdout — 2026-10-28T13:56 UTC (LIVE)

- Dataset: `HOLDOUT-v1.json` (sha256 `e7aaad6ae4d9…`), 6 synthetic cases; labels author-assigned, not expert ground truth
- Agent prompt sha256 `da5a3d567297…` · code `0bac93c+uncommitted`
- Models: `{"triage": "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B", "reasoning": "nvidia/nemotron-3-super-120b-a12b", "disposition": "nvidia/Nemotron-3-Ultra-550b-a55b"}`

Clear cases agreeing with the expected disposition: **4 of 4** · contested cases filed: **2 of 2** · rejected submissions: **3**.

| case | expected | status | agent | tool calls | rejected | tokens | seconds |
|---|---|---|---|---|---|---|---|
| H-01 | FILE | submitted | FILE | 6 | 1 | 16554 | 30.373 |
| H-02 | NOT_FILE | submitted | NOT_FILE | 5 | 0 | 11132 | 15.286 |
| H-03 | CONTESTED | submitted | FILE | 5 | 0 | 10539 | 13.106 |
| H-04 | FILE | submitted | FILE | 7 | 2 | 25394 | 25.292 |
| H-05 | CONTESTED | submitted | FILE | 5 | 0 | 11481 | 11.062 |
| H-06 | NOT_FILE | submitted | NOT_FILE | 5 | 0 | 11552 | 11.512 |

Reproduce: `python -m scripts.run_agent_holdout`.
