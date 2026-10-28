# Evaluation report — 2026-10-21 04:59 UTC (LIVE)

- Alerts: 16 (all synthetic) · compute backend: `local`
- Models: `{"triage": "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B", "reasoning": "nvidia/nemotron-3-super-120b-a12b", "disposition": "nvidia/Nemotron-3-Ultra-550b-a55b"}`

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

Schema-valid after at most one repair retry: **16 of 16**.

| alert | result | mode | seconds |
|---|---|---|---|
| ALERT-01 | valid | — | 71.74 |
| ALERT-02 | valid | json_object | 99.5 |
| ALERT-03 | valid | json_object | 47.34 |
| ALERT-04 | valid | — | 97.32 |
| ALERT-05 | valid | json_object | 20.44 |
| ALERT-06 | valid | json_object | 32.34 |
| ALERT-07 | valid | json_object | 21.74 |
| ALERT-08 | valid | json_object | 29.27 |
| ALERT-09 | valid | json_object | 20.3 |
| ALERT-10 | valid | json_object | 11.0 |
| ALERT-11 | valid | json_object | 16.97 |
| ALERT-12 | valid | json_object | 18.05 |
| ALERT-13 | valid | json_object | 17.04 |
| ALERT-14 | valid | json_object | 21.88 |
| ALERT-15 | valid | json_object | 27.84 |
| ALERT-16 | valid | json_object | 42.14 |

## 3. Agentic investigator

Accepted submissions: **16 of 16** · agreeing with gold: **12 of 16** · rejected submissions (caught by validation): **10**.

| alert | gold | status | agent | tool calls | rejected | tokens | seconds |
|---|---|---|---|---|---|---|---|
| ALERT-01 | FILE | submitted | FILE | 5 | 0 | 11636 | 74.035 |
| ALERT-02 | FILE | submitted | FILE | 7 | 1 | 20809 | 105.263 |
| ALERT-03 | CONTESTED | submitted | FILE | 5 | 0 | 10695 | 29.183 |
| ALERT-04 | FILE | submitted | FILE | 5 | 0 | 11390 | 13.607 |
| ALERT-05 | FILE | submitted | FILE | 5 | 0 | 9686 | 17.513 |
| ALERT-06 | FILE | submitted | FILE | 6 | 1 | 13854 | 18.074 |
| ALERT-07 | NOT_FILE | submitted | NOT_FILE | 5 | 0 | 9987 | 11.6 |
| ALERT-08 | NOT_FILE | submitted | NOT_FILE | 9 | 4 | 27259 | 68.915 |
| ALERT-09 | FILE | submitted | FILE | 6 | 1 | 12488 | 14.232 |
| ALERT-10 | FILE | submitted | FILE | 6 | 1 | 13516 | 12.662 |
| ALERT-11 | CONTESTED | submitted | FILE | 5 | 0 | 9955 | 9.167 |
| ALERT-12 | FILE | submitted | FILE | 6 | 1 | 12885 | 16.989 |
| ALERT-13 | CONTESTED | submitted | FILE | 5 | 0 | 10615 | 8.802 |
| ALERT-14 | CONTESTED | submitted | FILE | 5 | 0 | 9956 | 15.416 |
| ALERT-15 | FILE | submitted | FILE | 6 | 1 | 15042 | 20.418 |
| ALERT-16 | NOT_FILE | submitted | NOT_FILE | 5 | 0 | 11383 | 11.881 |

Reproduce: `python -m scripts.run_live_eval`. Raw rows in the matching .json file.
