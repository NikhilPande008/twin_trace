# Evaluation report — 2026-10-21 07:47 UTC (LIVE)

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

Model output schema-valid: **16 of 16** (first try 12, after one repair 4). Fallback placeholders (not model output): 0. Errors: 0.

| alert | outcome | parse failures | mode | seconds |
|---|---|---|---|---|
| ALERT-01 | repaired | 1 | json_object | 56.96 |
| ALERT-02 | success | 0 | json_object | 18.12 |
| ALERT-03 | success | 0 | json_object | 24.04 |
| ALERT-04 | repaired | 1 | json_object | 42.37 |
| ALERT-05 | success | 0 | json_object | 17.5 |
| ALERT-06 | success | 0 | json_object | 31.27 |
| ALERT-07 | success | 0 | json_object | 23.05 |
| ALERT-08 | success | 0 | json_object | 22.5 |
| ALERT-09 | success | 0 | json_object | 11.64 |
| ALERT-10 | success | 0 | json_object | 22.21 |
| ALERT-11 | success | 0 | json_object | 20.11 |
| ALERT-12 | success | 0 | json_object | 22.08 |
| ALERT-13 | repaired | 1 | json_object | 46.0 |
| ALERT-14 | success | 0 | json_object | 44.26 |
| ALERT-15 | repaired | 1 | json_object | 59.0 |
| ALERT-16 | success | 0 | json_object | 37.49 |

## 3. Agentic investigator

Accepted submissions: **16 of 16** · agreeing with gold: **12 of 16** · rejected submissions (caught by validation): **19**.

| alert | gold | status | agent | tool calls | rejected | tokens | seconds |
|---|---|---|---|---|---|---|---|
| ALERT-01 | FILE | submitted | FILE | 5 | 0 | 11729 | 10.108 |
| ALERT-02 | FILE | submitted | FILE | 7 | 2 | 21314 | 23.417 |
| ALERT-03 | CONTESTED | submitted | FILE | 6 | 1 | 14186 | 13.503 |
| ALERT-04 | FILE | submitted | FILE | 6 | 1 | 15711 | 17.099 |
| ALERT-05 | FILE | submitted | FILE | 5 | 0 | 9484 | 8.61 |
| ALERT-06 | FILE | submitted | FILE | 6 | 1 | 13834 | 14.995 |
| ALERT-07 | NOT_FILE | submitted | NOT_FILE | 6 | 1 | 13605 | 12.444 |
| ALERT-08 | NOT_FILE | submitted | NOT_FILE | 8 | 3 | 23418 | 38.899 |
| ALERT-09 | FILE | submitted | FILE | 6 | 1 | 13057 | 14.007 |
| ALERT-10 | FILE | submitted | FILE | 6 | 1 | 14050 | 16.696 |
| ALERT-11 | CONTESTED | submitted | FILE | 5 | 0 | 10085 | 14.279 |
| ALERT-12 | FILE | submitted | FILE | 6 | 1 | 13343 | 25.6 |
| ALERT-13 | CONTESTED | submitted | FILE | 6 | 1 | 14303 | 20.385 |
| ALERT-14 | CONTESTED | submitted | FILE | 10 | 5 | 33478 | 56.331 |
| ALERT-15 | FILE | submitted | FILE | 6 | 1 | 14756 | 18.425 |
| ALERT-16 | NOT_FILE | submitted | NOT_FILE | 5 | 0 | 11458 | 13.461 |

Reproduce: `python -m scripts.run_live_eval`. Raw rows in the matching .json file.
