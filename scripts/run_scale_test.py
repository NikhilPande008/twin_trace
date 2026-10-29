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
import random
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
    ap.add_argument("--per-label", type=int, default=500,
                    help="stratified sample: up to N laundering and N clean accounts")
    ap.add_argument("--seed", type=int, default=20261029)
    ap.add_argument("--out", default=str(ROOT / "evals"))
    args = ap.parse_args(argv)
    path = Path(args.csv)
    accounts = load_accounts(path, max_rows=args.max_rows)
    rng = random.Random(args.seed)
    by_label = {lab: sorted(k for k, a in accounts.items() if a["laundering"] is lab)
                for lab in (True, False)}
    sample = {lab: sorted(rng.sample(ks, min(args.per_label, len(ks))))
              for lab, ks in by_label.items()}
    runner = ComputeRunner(None)
    table: Counter = Counter()
    fired: Counter = Counter()
    for lab, keys in sample.items():
        for acct in keys:
            sigs = evaluate_signals(runner.run(acct, accounts[acct]["transactions"], {})["facts"])
            table[(lab, verdict(sigs))] += 1
            for s_ in sigs:
                if s_.fired:
                    fired[(lab, s_.signal_id)] += 1
    now = datetime.now(timezone.utc)
    fixture = "fixtures" in str(path)
    rep = {"generated_at": now.isoformat(timespec="seconds"), "file": path.name,
           "file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
           "fixture_only": fixture, "accounts_seen": len(accounts),
           "max_rows": args.max_rows, "seed": args.seed,
           "accounts_by_label": {"laundering": len(by_label[True]), "clean": len(by_label[False])},
           "sampled_by_label": {"laundering": len(sample[True]), "clean": len(sample[False])},
           "signals_fired": {f"{'laundering' if k[0] else 'clean'}|{k[1]}": v
                             for k, v in sorted(fired.items())},
           "by_label_and_level": {f"{'laundering' if k[0] else 'clean'}|{k[1]}": v
                                  for k, v in sorted(table.items())}}
    out = Path(args.out)
    stem = out / f"SCALE-{now:%Y-%m-%d}-{'fixture' if fixture else path.stem}"
    stem.with_suffix(".json").write_text(json.dumps(rep, indent=1))
    lines = [f"# Scale test — {rep['generated_at']} — {path.name}", ""]
    if fixture:
        lines += ["**FIXTURE: a hand-made 8-row file. Checks the harness only; do not quote.**", ""]
    lines += [f"File `{path.name}` sha256 `{rep['file_sha256'][:16]}…`; first "
              f"{args.max_rows or 'all'} rows (time-ordered); accounts with at least 2 transactions "
              f"in that window: {len(by_label[True])} with a laundering transaction, "
              f"{len(by_label[False])} without. **Stratified sample** (seed {args.seed}): "
              f"{len(sample[True])} + {len(sample[False])}, so the table shows how the signals "
              "behave per label, not how common either is.", "",
              "Signal mechanics only: the dataset is not Indian or UPI-shaped, amounts are in its "
              "own currencies, there are no registry flags (the strongest signal cannot fire) and "
              "no declared incomes. An account is 'laundering' if any of its transactions in the "
              "window is labelled laundering.", "",
              "| Dataset label | LOW | ELEVATED | HIGH |", "|---|---|---|---|"]
    for lab in (True, False):
        lines.append(f"| {'laundering' if lab else 'clean'} ({len(sample[lab])}) | "
                     + " | ".join(str(table[(lab, v)]) for v in ("LOW", "ELEVATED", "HIGH")) + " |")
    sig_ids = sorted({k[1] for k in fired})
    lines += ["", "| Signal fired | laundering | clean |", "|---|---|---|"]
    lines += [f"| {sid} | {fired[(True, sid)]} | {fired[(False, sid)]} |" for sid in sig_ids]
    stem.with_suffix(".md").write_text("\n".join(lines) + "\n")
    print(json.dumps(rep["by_label_and_level"]))
    print(f"wrote {stem}.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
