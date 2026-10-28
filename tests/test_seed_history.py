"""
Seeded case histories (2026-10-28): every alert has a multi-transaction record taken from its
scenario file, the gold labels did not move, and every scenario's gold draft passes the figure
gate against its alert's transactions and calculator facts.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from ddp import CoPilotSkills
from ddp import seed_data as seed
from ddp.bootstrap import compute_params, open_store
from ddp.compute import ComputeRunner

ROOT = Path(__file__).resolve().parent.parent
SCENARIOS = ROOT / "domain" / "scenarios"

GOLD = {"ALERT-01": "FILE", "ALERT-02": "FILE", "ALERT-03": "CONTESTED", "ALERT-04": "FILE",
        "ALERT-05": "FILE", "ALERT-06": "FILE", "ALERT-07": "NOT_FILE", "ALERT-08": "NOT_FILE",
        "ALERT-09": "FILE", "ALERT-10": "FILE", "ALERT-11": "CONTESTED", "ALERT-12": "FILE",
        "ALERT-13": "CONTESTED", "ALERT-14": "CONTESTED", "ALERT-15": "FILE",
        "ALERT-16": "NOT_FILE"}


def test_gold_labels_unchanged():
    assert {a["ALERT_ID"]: a["GOLD_DISPOSITION"] for a in seed.ALERTS} == GOLD


def test_every_alert_has_a_multi_transaction_history():
    for a in seed.ALERTS:
        rows = [t for t in seed.TRANSACTIONS if t["ALERT_ID"] == a["ALERT_ID"]]
        assert len(rows) >= 3, a["ALERT_ID"]
        assert not any(t["COUNTERPARTY"].startswith("Multiple counterparties") for t in rows), \
            f"{a['ALERT_ID']} still has a summary row"


def test_twins_share_the_credit_total():
    total = {aid: sum(t["AMOUNT_INR"] for t in seed.TRANSACTIONS
                      if t["ALERT_ID"] == aid and t["TXN_TYPE"] == "CREDIT")
             for aid in ("ALERT-01", "ALERT-16")}
    assert total == {"ALERT-01": 345000.0, "ALERT-16": 345000.0}


def _gold_drafts():
    for f in sorted(SCENARIOS.glob("[01][0-9]-*.md")):
        n = int(f.name[:2])
        if not 1 <= n <= 15:                 # 16-21 are eval scenarios with no seeded alert
            continue
        for m in re.finditer(r"^### \d+\. Draft [^\n]*\n(.*?)(?=^### |\Z)", f.read_text(), re.M | re.S):
            yield f"ALERT-{n:02d}", f.name, m.group(1)


@pytest.fixture(scope="module")
def env():
    store = open_store(":memory:")
    return store, ComputeRunner(store), CoPilotSkills(None)


@pytest.mark.parametrize("alert_id, name, draft", list(_gold_drafts()), ids=lambda x: x[:24])
def test_gold_draft_passes_the_figure_gate(env, alert_id, name, draft):
    store, runner, gate = env
    txns = store.transactions_for(alert_id)
    facts = runner.run(alert_id, txns, compute_params(store, alert_id))["facts"]
    res = gate.validate_gos_evidence(draft, txns, facts)
    assert res["passed"], (name, res["unsupported_claims"], res.get("unparsed_amounts"))


def test_gold_drafts_found_for_all_fifteen_scenarios():
    assert {a for a, _, _ in _gold_drafts()} == {f"ALERT-{i:02d}" for i in range(1, 16)}
