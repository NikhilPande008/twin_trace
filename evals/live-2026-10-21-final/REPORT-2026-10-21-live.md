# Evaluation report — 2026-10-21 09:12 UTC (LIVE)

- Alerts: 16 (all synthetic) · compute backend: `local`
- Models: `{"triage": "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B", "reasoning": "nvidia/nemotron-3-super-120b-a12b", "disposition": "nvidia/Nemotron-3-Ultra-550b-a55b"}`
- Tavily adapter in the agent: **injected**

## 1. Calculator and stress test (deterministic)

Gold FILE alerts whose calculator signals are HIGH: **1 of 9**. The rest rest on evidence the calculator does not see (PEP status, narrative, RFI responses); the stress test says so in its notes.

| alert | type | gold | signals | smallest flip set | branch runs |
|---|---|---|---|---|---|
| ALERT-01 | MULE_PASSTHROUGH | FILE | HIGH | 1 | 23 |
| ALERT-02 | STRUCTURING | FILE | ELEVATED | 1 | 8 |
| ALERT-03 | DORMANT_REACTIVATION | CONTESTED | LOW | 1 | 1 |
| ALERT-04 | PEP_INCONSISTENCY | FILE | LOW | — | 41 |
| ALERT-05 | CROSS_BORDER_FATF | FILE | LOW | — | 1 |
| ALERT-06 | NPO_MISUSE | FILE | LOW | — | 1 |
| ALERT-07 | LARGE_CASH_DEPOSIT | NOT_FILE | LOW | — | 1 |
| ALERT-08 | LARGE_CREDIT | NOT_FILE | LOW | 1 | 1 |
| ALERT-09 | DEVICE_IDENTITY_LINKAGE | FILE | LOW | — | 1 |
| ALERT-10 | BENEFICIARY_CONCENTRATION | FILE | ELEVATED | 1 | 2 |
| ALERT-11 | INCOME_INCONSISTENCY | CONTESTED | LOW | 1 | 1 |
| ALERT-12 | ATTEMPTED_SWIFT | FILE | LOW | — | 1 |
| ALERT-13 | MF_LAYERING | CONTESTED | LOW | 1 | 1 |
| ALERT-14 | NRI_KYC_MISMATCH | CONTESTED | LOW | 1 | 1 |
| ALERT-15 | FIDUCIARY_DIVERSION | FILE | LOW | — | 1 |
| ALERT-16 | MULE_PASSTHROUGH | NOT_FILE | ELEVATED | 1 | 4 |

## 2. Structured output — 11-factor assessment

Model output schema-valid: **16 of 16** (first try 14, after one repair 2). Fallback placeholders (not model output): 0. Errors: 0.

| alert | outcome | parse failures | mode | seconds |
|---|---|---|---|---|
| ALERT-01 | success | 0 | json_object | 26.46 |
| ALERT-02 | repaired | 1 | json_object | 36.59 |
| ALERT-03 | success | 0 | json_object | 12.94 |
| ALERT-04 | success | 0 | json_object | 27.11 |
| ALERT-05 | success | 0 | json_object | 21.77 |
| ALERT-06 | success | 0 | json_object | 16.02 |
| ALERT-07 | success | 0 | json_object | 29.01 |
| ALERT-08 | success | 0 | json_object | 28.52 |
| ALERT-09 | success | 0 | json_object | 27.39 |
| ALERT-10 | success | 0 | json_object | 19.37 |
| ALERT-11 | success | 0 | json_object | 25.52 |
| ALERT-12 | success | 0 | json_object | 14.39 |
| ALERT-13 | success | 0 | json_object | 26.96 |
| ALERT-14 | success | 0 | json_object | 25.04 |
| ALERT-15 | success | 0 | json_object | 21.26 |
| ALERT-16 | repaired | 1 | json_object | 56.94 |

## 3. Agentic investigator

Accepted submissions: **16 of 16** · agreeing with gold: **12 of 16** · rejected submissions (caught by validation): **16**.

| alert | gold | status | agent | tool calls | rejected | tokens | seconds |
|---|---|---|---|---|---|---|---|
| ALERT-01 | FILE | submitted | FILE | 5 | 0 | 11731 | 11.323 |
| ALERT-02 | FILE | submitted | FILE | 6 | 1 | 16491 | 23.54 |
| ALERT-03 | CONTESTED | submitted | FILE | 7 | 2 | 18374 | 21.582 |
| ALERT-04 | FILE | submitted | FILE | 5 | 0 | 11403 | 14.018 |
| ALERT-05 | FILE | submitted | FILE | 5 | 0 | 9583 | 15.043 |
| ALERT-06 | FILE | submitted | FILE | 6 | 1 | 13530 | 22.01 |
| ALERT-07 | NOT_FILE | submitted | NOT_FILE | 7 | 2 | 17772 | 25.703 |
| ALERT-08 | NOT_FILE | submitted | NOT_FILE | 7 | 2 | 17920 | 28.751 |
| ALERT-09 | FILE | submitted | FILE | 6 | 1 | 12725 | 19.01 |
| ALERT-10 | FILE | submitted | FILE | 6 | 1 | 13736 | 13.721 |
| ALERT-11 | CONTESTED | submitted | FILE | 7 | 2 | 18082 | 34.408 |
| ALERT-12 | FILE | submitted | FILE | 6 | 1 | 13115 | 15.635 |
| ALERT-13 | CONTESTED | submitted | FILE | 6 | 1 | 14569 | 21.394 |
| ALERT-14 | CONTESTED | submitted | FILE | 6 | 1 | 13315 | 12.288 |
| ALERT-15 | FILE | submitted | FILE | 6 | 1 | 14423 | 22.22 |
| ALERT-16 | NOT_FILE | submitted | NOT_FILE | 5 | 0 | 11248 | 12.559 |

Reproduce: `python -m scripts.run_live_eval`. Raw rows in the matching .json file.
