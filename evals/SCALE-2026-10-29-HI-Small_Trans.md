# Scale test — 2026-10-29T04:26:52+00:00 — HI-Small_Trans.csv

File `HI-Small_Trans.csv` sha256 `b19d39f515523373…`; first 1000000 rows (time-ordered); accounts with at least 2 transactions in that window: 592 with a laundering transaction, 198711 without. **Stratified sample** (seed 20261029): 500 + 500, so the table shows how the signals behave per label, not how common either is.

Signal mechanics only: the dataset is not Indian or UPI-shaped, amounts are in its own currencies, there are no registry flags (the strongest signal cannot fire) and no declared incomes. An account is 'laundering' if any of its transactions in the window is labelled laundering.

| Dataset label | LOW | ELEVATED | HIGH |
|---|---|---|---|
| laundering (500) | 496 | 4 | 0 |
| clean (500) | 500 | 0 | 0 |

| Signal fired | laundering | clean |
|---|---|---|
| S-FAN-IN | 32 | 3 |
| S-PASSTHROUGH | 196 | 119 |
