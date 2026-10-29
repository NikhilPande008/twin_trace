# Agent on the holdout — 2026-10-28T13:54 UTC (LIVE)

- Dataset: `HOLDOUT-v1.json` (sha256 `e7aaad6ae4d9…`), 6 synthetic cases; labels author-assigned, not expert ground truth
- Agent prompt sha256 `da5a3d567297…` · code `0bac93c+uncommitted`
- Models: `{"triage": "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B", "reasoning": "nvidia/nemotron-3-super-120b-a12b", "disposition": "nvidia/Nemotron-3-Ultra-550b-a55b"}`

Clear cases agreeing with the expected disposition: **3 of 4** · contested cases filed: **1 of 2** · rejected submissions: **2**.

| case | expected | status | agent | tool calls | rejected | tokens | seconds |
|---|---|---|---|---|---|---|---|
| H-01 | FILE | submitted | FILE | 5 | 0 | 12229 | 14.262 |
| H-02 | NOT_FILE | submitted | FILE | 7 | 1 | 18985 | 31.007 |
| H-03 | CONTESTED | submitted | FILE | 5 | 0 | 10479 | 11.515 |
| H-04 | FILE | submitted | FILE | 7 | 1 | 23036 | 22.839 |
| H-05 | CONTESTED | submitted | NEEDS_MORE_INFO | 4 | 0 | 8374 | 12.656 |
| H-06 | NOT_FILE | submitted | NOT_FILE | 4 | 0 | 8430 | 13.625 |

Reproduce: `python -m scripts.run_agent_holdout`.
