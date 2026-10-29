"""
Scale test (T12.15): the calculator of record and the signal rules on the IBM/ETH synthetic AML
datasets (NeurIPS 2023). The dataset is NOT in this repo and is not downloaded by this script.

    python -m scripts.run_scale_test --csv tests/fixtures/amlworld_sample.csv   # harness check
    python -m scripts.run_scale_test --csv /path/to/HI-Small_Trans.csv --max-rows 200000

Counts accounts by dataset label (laundering or not) and by the modeled signal level. Signal
mechanics only: not Indian data, not UPI, no registry flags, no declared income (see
ddp/scale/amlworld.py). A run on the fixture says nothing; it only checks the harness.
Writes evals/SCALE-<date>-<name>.md and .json.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ddp.compute import ComputeRunner  # noqa: E402
from ddp.scale.amlworld import load_accounts  # noqa: E402
from ddp.stress.signals import evaluate_signals, verdict  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--max-rows", type=int, default=None)
    ap.add_argument("--max-accounts", type=int, default=2000)
    ap.add_argument("--out", default=str(ROOT / "evals"))
    args = ap.parse_args(argv)
    path = Path(args.csv)
    accounts = load_accounts(path, max_rows=args.max_rows)
    runner = ComputeRunner(None)
    table: Counter = Counter()
    for i, (acct, a) in enumerate(sorted(accounts.items())):
        if i >= args.max_accounts:
            break
        facts = runner.run(acct, a["transactions"], {})["facts"]
        table[(a["laundering"], verdict(evaluate_signals(facts)))] += 1
    now = datetime.now(timezone.utc)
    fixture = "fixtures" in str(path)
    rep = {"generated_at": now.isoformat(timespec="seconds"), "file": path.name,
           "file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
           "fixture_only": fixture, "accounts_seen": len(accounts),
           "accounts_run": min(len(accounts), args.max_accounts),
           "by_label_and_level": {f"{'laundering' if k[0] else 'clean'}|{k[1]}": v
                                  for k, v in sorted(table.items())}}
    out = Path(args.out)
    stem = out / f"SCALE-{now:%Y-%m-%d}-{'fixture' if fixture else path.stem}"
    stem.with_suffix(".json").write_text(json.dumps(rep, indent=1))
    lines = [f"# Scale test — {rep['generated_at']} — {path.name}", ""]
    if fixture:
        lines += ["**FIXTURE: a hand-made 8-row file. Checks the harness only; do not quote.**", ""]
    lines += ["Signal mechanics only: the dataset is not Indian or UPI-shaped, amounts are in its "
              "own currencies, and there are no registry flags or declared incomes.", "",
              "| Dataset label | LOW | ELEVATED | HIGH |", "|---|---|---|---|"]
    for lab in (True, False):
        lines.append(f"| {'laundering' if lab else 'clean'} | "
                     + " | ".join(str(table[(lab, v)]) for v in ("LOW", "ELEVATED", "HIGH")) + " |")
    stem.with_suffix(".md").write_text("\n".join(lines) + "\n")
    print(json.dumps(rep["by_label_and_level"]))
    print(f"wrote {stem}.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
