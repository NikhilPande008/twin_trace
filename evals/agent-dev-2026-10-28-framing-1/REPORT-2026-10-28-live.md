# Evaluation report — 2026-10-28 14:17 UTC (LIVE)

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

Accepted submissions: **16 of 16** · agreeing with gold: **12 of 16** · rejected submissions (caught by validation): **12**.

| alert | gold | status | agent | tool calls | rejected | tokens | seconds |
|---|---|---|---|---|---|---|---|
| ALERT-01 | FILE | submitted | FILE | 5 | 0 | 11789 | 9.174 |
| ALERT-02 | FILE | submitted | FILE | 6 | 1 | 35771 | 19.915 |
| ALERT-03 | CONTESTED | submitted | FILE | 6 | 1 | 13997 | 12.309 |
| ALERT-04 | FILE | submitted | FILE | 5 | 0 | 11613 | 10.421 |
| ALERT-05 | FILE | submitted | FILE | 5 | 0 | 11615 | 11.414 |
| ALERT-06 | FILE | submitted | FILE | 6 | 1 | 21862 | 17.269 |
| ALERT-07 | NOT_FILE | submitted | NOT_FILE | 7 | 2 | 30403 | 29.415 |
| ALERT-08 | NOT_FILE | submitted | NOT_FILE | 8 | 3 | 23111 | 21.732 |
| ALERT-09 | FILE | submitted | FILE | 5 | 0 | 20752 | 11.964 |
| ALERT-10 | FILE | submitted | FILE | 5 | 0 | 22133 | 13.569 |
| ALERT-11 | CONTESTED | submitted | FILE | 5 | 0 | 12349 | 9.755 |
| ALERT-12 | FILE | submitted | FILE | 6 | 1 | 14672 | 19.919 |
| ALERT-13 | CONTESTED | submitted | FILE | 6 | 1 | 32428 | 24.119 |
| ALERT-14 | CONTESTED | submitted | FILE | 5 | 0 | 11680 | 11.364 |
| ALERT-15 | FILE | submitted | FILE | 6 | 1 | 27967 | 22.543 |
| ALERT-16 | NOT_FILE | submitted | NOT_FILE | 6 | 1 | 15726 | 15.416 |

Reproduce: `python -m scripts.run_live_eval`. Raw rows in the matching .json file.
