# Evaluation report — 2026-10-28 13:54 UTC (LIVE)

- Alerts: 16 (all synthetic) · compute backend: `local`
- Seed SHA-256: `969dda38cba7eb328e68403b06231272dd272188adec54a62f0110fec6e5e74e`
- Models: `{"triage": "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B", "reasoning": "nvidia/nemotron-3-super-120b-a12b", "disposition": "nvidia/Nemotron-3-Ultra-550b-a55b"}`
- Tavily adapter in the agent: **not injected**

## 1. Calculator and stress test (deterministic)

Gold FILE alerts whose calculator signals are HIGH: **3 of 9**. The rest rest on evidence the calculator does not see (PEP status, narrative, RFI responses); the stress test says so in its notes.

| alert | type | gold | signals | smallest flip set | branch runs |
|---|---|---|---|---|---|
| ALERT-01 | MULE_PASSTHROUGH | FILE | HIGH | 1 | 23 |
| ALERT-02 | STRUCTURING | FILE | ELEVATED | — | 64 |
| ALERT-03 | DORMANT_REACTIVATION | CONTESTED | LOW | 1 | 4 |
| ALERT-04 | PEP_INCONSISTENCY | FILE | LOW | — | 41 |
| ALERT-05 | CROSS_BORDER_FATF | FILE | LOW | — | 63 |
| ALERT-06 | NPO_MISUSE | FILE | HIGH | 1 | 64 |
| ALERT-07 | LARGE_CASH_DEPOSIT | NOT_FILE | ELEVATED | 1 | 1 |
| ALERT-08 | LARGE_CREDIT | NOT_FILE | LOW | 1 | 4 |
| ALERT-09 | DEVICE_IDENTITY_LINKAGE | FILE | LOW | — | 64 |
| ALERT-10 | BENEFICIARY_CONCENTRATION | FILE | HIGH | 1 | 64 |
| ALERT-11 | INCOME_INCONSISTENCY | CONTESTED | LOW | 1 | 4 |
| ALERT-12 | ATTEMPTED_SWIFT | FILE | LOW | — | 25 |
| ALERT-13 | MF_LAYERING | CONTESTED | LOW | — | 14 |
| ALERT-14 | NRI_KYC_MISMATCH | CONTESTED | LOW | 1 | 2 |
| ALERT-15 | FIDUCIARY_DIVERSION | FILE | LOW | — | 64 |
| ALERT-16 | MULE_PASSTHROUGH | NOT_FILE | ELEVATED | 1 | 4 |

## 3. Agentic investigator

Accepted submissions: **16 of 16** · agreeing with gold: **10 of 16** · rejected submissions (caught by validation): **11**.

| alert | gold | status | agent | tool calls | rejected | tokens | seconds |
|---|---|---|---|---|---|---|---|
| ALERT-01 | FILE | submitted | FILE | 5 | 0 | 12607 | 11.585 |
| ALERT-02 | FILE | submitted | FILE | 6 | 1 | 35966 | 30.889 |
| ALERT-03 | CONTESTED | submitted | FILE | 6 | 1 | 15939 | 21.347 |
| ALERT-04 | FILE | submitted | FILE | 5 | 0 | 12334 | 14.876 |
| ALERT-05 | FILE | submitted | FILE | 6 | 1 | 16693 | 26.048 |
| ALERT-06 | FILE | submitted | FILE | 6 | 1 | 23334 | 21.922 |
| ALERT-07 | NOT_FILE | submitted | NOT_FILE | 7 | 2 | 32841 | 39.059 |
| ALERT-08 | NOT_FILE | submitted | NOT_FILE | 8 | 2 | 23949 | 31.101 |
| ALERT-09 | FILE | submitted | FILE | 5 | 0 | 20944 | 11.8 |
| ALERT-10 | FILE | submitted | FILE | 5 | 0 | 23095 | 12.08 |
| ALERT-11 | CONTESTED | submitted | NEEDS_MORE_INFO | 5 | 0 | 13479 | 11.205 |
| ALERT-12 | FILE | submitted | NEEDS_MORE_INFO | 6 | 1 | 16343 | 18.551 |
| ALERT-13 | CONTESTED | submitted | FILE | 5 | 0 | 24435 | 12.752 |
| ALERT-14 | CONTESTED | submitted | FILE | 6 | 1 | 16583 | 19.114 |
| ALERT-15 | FILE | submitted | NEEDS_MORE_INFO | 5 | 1 | 21772 | 15.133 |
| ALERT-16 | NOT_FILE | submitted | NOT_FILE | 5 | 0 | 11958 | 10.384 |

Reproduce: `python -m scripts.run_live_eval`. Raw rows in the matching .json file.
