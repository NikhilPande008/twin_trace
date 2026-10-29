"""
Practitioner review packet (T12.1): blind drafts for AML practitioners to rate, plus the holdout
labels for them to review.

    python -m scripts.export_practitioner_packet            # writes docs/practitioner/ (local-only)

Source: the three drafts per holdout case recorded in the dated live comparison run
(evals/RUN-20261021T080109Z-live/outputs.jsonl): C1 template, C2 same model without controls,
C3 full product. Each case's three drafts are shuffled with a fixed seed and labelled A/B/C. The
key that maps letters to conditions is written to a SEPARATE file; keep it away from raters.
docs/ is gitignored, so neither file reaches the public repository.

The human recruits the raters and sends the packet; nothing here contacts anyone.
"""

from __future__ import annotations

import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "evals" / "RUN-20261021T080109Z-live" / "outputs.jsonl"
HOLDOUT = ROOT / "evals" / "holdout" / "HOLDOUT-v1.json"
OUT = ROOT / "docs" / "practitioner"
SEED = 20261028

RUBRIC = """# Rating rubric (v1)

Rate each draft independently. You do not know which system wrote which draft.

| # | Question | Scale |
|---|---|---|
| R1 | Is it specific to THIS case (its customer, amounts, dates, counterparties), not generic? | 1 (generic) – 5 (fully specific) |
| R2 | Could you verify every amount it states from the case data shown? | yes / no — if no, list the amount |
| R3 | Would you sign it as the Principal Officer, after light edits? | 1 (no) – 5 (as is) |
| R4 | Would it hold up if an FIU-IND inspector asked about it months later? | 1 (no) – 5 (yes) |
| R5 | Anything wrong or risky (tipping-off, accusation without evidence, a wrong fact)? | free text |

Then, for the case as a whole:

| # | Question |
|---|---|
| L1 | The case is labelled FILE, NOT_FILE or CONTESTED (below). Do you agree? If not, what would you decide and why? |

Ratings are anonymous. The drafts and cases are synthetic; no real customer is described.
"""


def main() -> int:
    if not RUN.exists():
        print(f"missing {RUN}")
        return 2
    rows = [json.loads(line) for line in RUN.read_text().splitlines() if line.strip()]
    cases = {c["id"]: c for c in json.loads(HOLDOUT.read_text())["cases"]}
    rng = random.Random(SEED)
    key, md = {}, ["# Practitioner packet v1 — blind drafts", "",
                   "Read RUBRIC.md first. Six synthetic cases, three drafts each.", ""]
    csv = ["case,draft,R1,R2,R2_amount,R3,R4,R5,L1"]
    for cid in sorted({r["case"] for r in rows}):
        c = cases[cid]
        drafts = [r for r in rows if r["case"] == cid]
        rng.shuffle(drafts)
        key[cid] = {}
        md += [f"## Case {cid}", "", f"**Label:** {c['expected']}  ", f"**Customer:** {c['customer_profile']}  ",
               f"**Alert:** {c['alert_narrative']}", "", "| Txn | Date | Type | Amount (INR) | Counterparty | Flagged |",
               "|---|---|---|---|---|---|"]
        md += [f"| {t['txn_id']} | {t['date']} | {t['type']} | {t['amount_inr']:,.0f} | {t['counterparty']} | "
               f"{'yes' if t.get('is_flagged') else 'no'} |" for t in c["transactions"]]
        for letter, d in zip("ABC", drafts):
            key[cid][letter] = d["condition"]
            md += ["", f"### Draft {cid}-{letter}", "", d["draft"].strip()]
            csv.append(f"{cid},{letter},,,,,,,")
        md.append("")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "RUBRIC.md").write_text(RUBRIC)
    (OUT / "PACKET-v1.md").write_text("\n".join(md) + "\n")
    (OUT / "RATINGS-template.csv").write_text("\n".join(csv) + "\n")
    (OUT / "KEY-v1.json").write_text(json.dumps({
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": str(RUN.relative_to(ROOT)), "seed": SEED, "key": key}, indent=1))
    print(f"wrote {OUT}/PACKET-v1.md, RUBRIC.md, RATINGS-template.csv and KEY-v1.json "
          "(keep the key away from raters)")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT))
    raise SystemExit(main())
