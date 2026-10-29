# Evaluation report — 2026-10-28 13:32 UTC (DETERMINISTIC)

> **DETERMINISTIC RUN.** Calculator and stress test only; no model was called.

- Alerts: 16 (all synthetic) · compute backend: `local`
- Seed SHA-256: `969dda38cba7eb328e68403b06231272dd272188adec54a62f0110fec6e5e74e`

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

Reproduce: `python -m scripts.run_live_eval --deterministic`. Raw rows in the matching .json file.
