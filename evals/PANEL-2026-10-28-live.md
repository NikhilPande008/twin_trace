# Tier panel evaluation — 2026-10-28T18:41:12+00:00 (LIVE)

Seed `969dda38cba7eb32…` · holdout `e7aaad6ae4d9b05e…` · wall time 1450.8 s

Models: triage `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`, reasoning `nvidia/nemotron-3-super-120b-a12b`, disposition `nvidia/Nemotron-3-Ultra-550b-a55b`

Labels are author-assigned (synthetic scenarios), not expert ground truth. Contested = the tiers' recommendations differ (deterministic count rule over each tier's 11 factor assessments).

| Set | Cases | CONTESTED caught | False alarms on clear cases | Unanimous and matching gold (clear) | Incomplete panels |
|---|---|---|---|---|---|
| dev | 16 | 0 / 4 | 2 / 12 | 10 / 12 | 0 |
| holdout | 6 | 0 / 2 | 2 / 4 | 2 / 4 | 0 |

| Case | Gold | Nano | Super | Ultra | Contested | Split factors |
|---|---|---|---|---|---|---|
| ALERT-01 | FILE | FILE | FILE | FILE | no | 2 |
| ALERT-02 | FILE | FILE | FILE | FILE | no | 2 |
| ALERT-03 | CONTESTED | FILE | FILE | FILE | no | 5 |
| ALERT-04 | FILE | FILE | FILE | FILE | no | 3 |
| ALERT-05 | FILE | FILE | FILE | FILE | no | 3 |
| ALERT-06 | FILE | FILE | FILE | FILE | no | 5 |
| ALERT-07 | NOT_FILE | NOT_FILE | NOT_FILE | NOT_FILE | no | 1 |
| ALERT-08 | NOT_FILE | FILE | FILE | NOT_FILE | yes | 5 |
| ALERT-09 | FILE | FILE | FILE | FILE | no | 3 |
| ALERT-10 | FILE | FILE | FILE | FILE | no | 4 |
| ALERT-11 | CONTESTED | FILE | FILE | FILE | no | 5 |
| ALERT-12 | FILE | FILE | FILE | FILE | no | 6 |
| ALERT-13 | CONTESTED | FILE | FILE | FILE | no | 3 |
| ALERT-14 | CONTESTED | FILE | FILE | FILE | no | 4 |
| ALERT-15 | FILE | FILE | FILE | FILE | no | 3 |
| ALERT-16 | NOT_FILE | FILE | FILE | REVIEW | yes | 3 |
| H-01 | FILE | FILE | FILE | FILE | no | 3 |
| H-02 | NOT_FILE | FILE | NOT_FILE | NOT_FILE | yes | 7 |
| H-03 | CONTESTED | FILE | FILE | FILE | no | 6 |
| H-04 | FILE | FILE | FILE | FILE | no | 4 |
| H-05 | CONTESTED | FILE | FILE | FILE | no | 4 |
| H-06 | NOT_FILE | FILE | FILE | NOT_FILE | yes | 4 |

Completion tokens by tier: triage 124458, reasoning 89135, disposition 102032
