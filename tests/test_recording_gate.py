"""
T7.2: the evidence gate is enforced at the recording boundary. A direct recorder call with an
unsupported figure, an unknown run, or another alert's run raises and writes nothing. Offline.
"""
from __future__ import annotations

import json

import pytest

from ddp.bootstrap import compute_params, open_store
from ddp.compute import ComputeRunner
from ddp.skills import POE_FACTORS, CoPilotSkills

POE = [{"factor_id": f, "factor_name": n, "assessment": "clear"} for f, n in POE_FACTORS]


def _setup():
    store = open_store(":memory:")
    return store, CoPilotSkills(store)


def _record(skills, rationale, alert_id="ALERT-01", **kw):
    return skills.alert_disposition_recorder(
        alert_id=alert_id, customer_ref="CUST-01", disposition=kw.pop("disposition", "FILE"),
        rationale_text=rationale, rules_cited=[], rfi_triggers=[], poe_assessment=POE, **kw)


def _ledger_count(store):
    return store.query("SELECT COUNT(*) AS n FROM DECISION_LEDGER")[0]["n"]


def _run(store, alert_id):
    return ComputeRunner(store).run(alert_id, store.transactions_for(alert_id),
                                    compute_params(store, alert_id))


def _status(store, alert_id):
    return store.get_alert(alert_id)["ALERT_STATUS"]


def test_unsupported_amount_is_not_recorded():
    store, skills = _setup()
    before = _status(store, "ALERT-01")
    with pytest.raises(ValueError, match="evidence gate failed"):
        _record(skills, "Funds totalling ₹32,50,000 were passed to the flagged handle.")
    assert _ledger_count(store) == 0
    assert _status(store, "ALERT-01") == before


@pytest.mark.parametrize("disposition", ["NOT_FILE", "ESCALATE", "DEFERRED"])
def test_gate_applies_to_every_disposition(disposition):
    store, skills = _setup()
    with pytest.raises(ValueError):
        _record(skills, "Closing: the ₹32,50,000 inflow was explained by salary.",
                disposition=disposition)
    assert _ledger_count(store) == 0


def test_transaction_amount_records():
    store, skills = _setup()
    amt = store.transactions_for("ALERT-01")[0]["amount_inr"]
    res = _record(skills, f"Credit of ₹{amt:,} from an unknown handle was moved on the same day.")
    assert res["status"] == "recorded"
    meta = json.loads(store.query("SELECT METADATA_JSON FROM DECISION_LEDGER")[0]["METADATA_JSON"])
    assert meta["evidence_check"]["passed"] is True


def _total_debit_text(run):
    total = next(f["value"] for f in run["facts"] if f["fact_id"] == "F-TOTAL-DEBIT")
    return f"Debits totalled ₹{total:,} (F-TOTAL-DEBIT), mostly to the flagged handle."


def test_aggregate_without_a_run_is_rejected():
    store, skills = _setup()
    with pytest.raises(ValueError):
        _record(skills, _total_debit_text(_run(store, "ALERT-01")))


def test_aggregate_with_this_alerts_run_records():
    store, skills = _setup()
    run = _run(store, "ALERT-01")
    res = _record(skills, _total_debit_text(run), compute_run_id=run["run_id"])
    meta = json.loads(store.query("SELECT METADATA_JSON FROM DECISION_LEDGER")[0]["METADATA_JSON"])
    assert res["status"] == "recorded"
    assert "F-TOTAL-DEBIT" in sum(meta["evidence_check"]["fact_citations"].values(), [])


def test_another_alerts_run_is_rejected():
    store, skills = _setup()
    other = _run(store, "ALERT-16")
    with pytest.raises(ValueError, match="belongs to ALERT-16"):
        _record(skills, "Formed suspicion on the pass-through to the flagged handle.",
                compute_run_id=other["run_id"])
    assert _ledger_count(store) == 0


def test_unknown_run_is_rejected():
    store, skills = _setup()
    with pytest.raises(ValueError, match="does not exist"):
        _record(skills, "Formed suspicion on the pass-through to the flagged handle.",
                compute_run_id="RUN-doesnotexist")


def test_run_with_mismatched_output_hash_is_rejected():
    store, skills = _setup()
    run = _run(store, "ALERT-01")
    row = dict(store.get_compute_run(run["run_id"]))
    forged = json.loads(row["OUTPUT_JSON"])
    forged["facts"].append({"fact_id": "F-FORGED", "value": 3250000, "unit": "INR"})
    row.update(RUN_ID="RUN-forged", OUTPUT_JSON=json.dumps(forged))   # hash left unchanged
    store.append_compute_run(row)
    with pytest.raises(ValueError, match="does not match its recorded hash"):
        _record(skills, "Funds totalling ₹32,50,000 (F-FORGED) moved out.",
                compute_run_id="RUN-forged")
    assert _ledger_count(store) == 0


@pytest.mark.parametrize("figure", ["Rs. 32,50,000", "INR 3250000", "₹32.5 lakh", "32.5 lakh"])
def test_other_rupee_forms_are_refused_at_recording(figure):
    """T7.1 + T7.2: the phrasings that used to slip past the gate cannot reach the ledger."""
    store, skills = _setup()
    with pytest.raises(ValueError, match="evidence gate failed"):
        _record(skills, f"Funds totalling {figure} were passed to the flagged handle.")
    assert _ledger_count(store) == 0


# ── T1: stale validation, idempotency, policy, transactional write ────────────

def test_stale_validation_is_refused():
    import hashlib
    store, skills = _setup()
    checked = "Formed suspicion on the pass-through to the flagged handle."
    edited = checked + " Added later."
    with pytest.raises(ValueError, match="changed after it was checked"):
        _record(skills, edited, validated_draft_sha256=hashlib.sha256(checked.encode()).hexdigest())
    assert _ledger_count(store) == 0


def test_repeated_submission_records_once():
    store, skills = _setup()
    text = "Formed suspicion on the pass-through to the flagged handle."
    first = _record(skills, text, suspicion_formed_at="2026-10-01T10:00:00Z")
    again = _record(skills, text, suspicion_formed_at="2026-10-01T10:00:00Z")
    assert first["status"] == "recorded" and again["status"] == "already_recorded"
    assert again["decision_id"] == first["decision_id"]
    assert _ledger_count(store) == 1
    assert store.verify_ledger_chain()["ok"]


def test_retry_without_suspicion_time_is_still_idempotent():
    store, skills = _setup()
    text = "Formed suspicion on the pass-through to the flagged handle."
    _record(skills, text)
    assert _record(skills, text)["status"] == "already_recorded"
    assert _ledger_count(store) == 1


def test_different_disposition_is_a_new_decision():
    store, skills = _setup()
    text = "Formed suspicion on the pass-through to the flagged handle."
    _record(skills, text)
    _record(skills, text, disposition="ESCALATE")
    assert _ledger_count(store) == 2


def test_customer_disclosure_blocks_recording():
    store, skills = _setup()
    with pytest.raises(ValueError, match="tipping_off_customer"):
        _record(skills, "We have informed the customer that an STR has been filed on the account.")
    assert _ledger_count(store) == 0


def test_validation_binding_is_stored():
    store, skills = _setup()
    _record(skills, "Formed suspicion on the pass-through to the flagged handle.")
    meta = json.loads(store.query("SELECT METADATA_JSON FROM DECISION_LEDGER")[0]["METADATA_JSON"])
    v = meta["validation"]
    assert len(v["draft_sha256"]) == 64 and len(v["txn_input_sha256"]) == 64
    assert v["gate_version"].startswith("deterministic-")
    assert meta["decision_maker_id_basis"].startswith("self-asserted")


def test_failed_write_leaves_no_partial_decision():
    """If the status update fails, the ledger row is rolled back too."""
    store, skills = _setup()
    store._conn.execute("CREATE TRIGGER FAIL_STATUS BEFORE UPDATE ON ALERTS "
                        "BEGIN SELECT RAISE(ABORT, 'simulated failure'); END;")
    with pytest.raises(Exception, match="simulated failure"):
        _record(skills, "Formed suspicion on the pass-through to the flagged handle.")
    assert _ledger_count(store) == 0
    assert store.verify_ledger_chain()["ok"]
