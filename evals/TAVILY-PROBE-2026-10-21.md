# Tavily live probe — 2026-10-21 07:33 UTC

Synthetic seed alerts only; in-memory store. Reproduce: `python3 -m scripts.probes.probe_tavily`.

| case | status | expected | HTTP | results | seconds | pass |
|---|---|---|---|---|---|---|
| adverse_media:ALERT-01 | ok | no_results/ok | 200 | 5 | 0.79 | ✓ |
| adverse_media:ALERT-16 | ok | no_results/ok | 200 | 5 | 0.71 | ✓ |
| regulator_search | ok | no_results/ok | 200 | 5 | 0.79 | ✓ |
| regulator_search_refused | refused | refused | — | 0 | 0.0 | ✓ |
| forced_failure:invalid_key | http_error | http_error | 401 | 0 | 0.78 | ✓ |
| forced_failure:timeout | timeout | network_error/timeout | — | 0 | 0.01 | ✓ |

## Queries sent

- **adverse_media:ALERT-01**: `UPI money mule account pass-through fraud India`
- **adverse_media:ALERT-16**: `UPI money mule account pass-through fraud India`
- **regulator_search**: `RBI master direction KYC customer due diligence amendment`
- **regulator_search_refused**: (none sent)
- **forced_failure:invalid_key**: `UPI money mule account pass-through fraud India`
- **forced_failure:timeout**: `UPI money mule account pass-through fraud India`

## Results returned

- adverse_media:ALERT-01: [Combating Money Mule Fraud for Safer Banking in India](https://risk.lexisnexis.com/global/en/insights-resources/article/stopping-money-mules-in-india)
- adverse_media:ALERT-01: [Detection of Mule Accounts and Fraudsters in UPI Transactions Using AI and Machine Learnin](https://www.irejournals.com/paper-details/1716166)
- adverse_media:ALERT-01: [Don’t Be a Money Mule Protect Yourself from Fraud - Indian Bank](https://indianbank.bank.in/en/don-t-be-a-money-mule-protect-yourself-from-fraud)
- adverse_media:ALERT-01: [UPI Fraud: Common Types and Methods to Prevent UPI Payment Scams](https://razorpay.com/blog/upi-frauds-types-tactics)
- adverse_media:ALERT-01: [Don't Become a Money Mule! Your bank account should ...](https://www.facebook.com/SSOIndia2/posts/dont-become-a-money-mule-your-bank-account-should-never-be-used-to-receive-or-tr/1053262484236093)
- adverse_media:ALERT-16: [Combating Money Mule Fraud for Safer Banking in India](https://risk.lexisnexis.com/global/en/insights-resources/article/stopping-money-mules-in-india)
- adverse_media:ALERT-16: [Detection of Mule Accounts and Fraudsters in UPI Transactions Using AI and Machine Learnin](https://www.irejournals.com/paper-details/1716166)
- adverse_media:ALERT-16: [Don’t Be a Money Mule Protect Yourself from Fraud - Indian Bank](https://indianbank.bank.in/en/don-t-be-a-money-mule-protect-yourself-from-fraud)
- adverse_media:ALERT-16: [UPI Fraud: Common Types and Methods to Prevent UPI Payment Scams](https://razorpay.com/blog/upi-frauds-types-tactics)
- adverse_media:ALERT-16: [Don't Become a Money Mule! Your bank account should ...](https://www.facebook.com/SSOIndia2/posts/dont-become-a-money-mule-your-bank-account-should-never-be-used-to-receive-or-tr/1053262484236093)
- regulator_search: [Master Directions | Official Website of Reserve Bank of India](https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=12896)
- regulator_search: [Notifications| Official Website of Reserve Bank of India](https://m.rbi.org.in/Scripts/NotificationUser.aspx?Id=12746&Mode=0)
- regulator_search: [Database| Official Website of Reserve Bank of India](https://m.rbi.org.in/scripts/BS_ViewMasDirections.aspx?id=13141)
- regulator_search: [Reserve Bank of India - Master Directions](https://m.rbi.org.in/Scripts/BS_ViewMasterDirections.aspx?id=10201)
- regulator_search: [Know Your Customer (KYC) Direction, 2016 (Updated as ...](https://www.rbi.org.in/CommonPerson/english/scripts/notification.aspx?id=2607)
