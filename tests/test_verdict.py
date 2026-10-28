"""Verdict card and Twin Cases data come only from deterministic stress-test reports."""

from __future__ import annotations

import pytest

from ddp import verdict as V
from ddp.bootstrap import build, compute_params, open_store
from ddp.config import Settings
from ddp.stress import StressTester


class _NoModel:
    def __getattr__(self, name):
        raise AssertionError(f"verdict data must not touch the model ({name})")


@pytest.fixture(scope="module")
def env():
    store, _, runner, _ = build(Settings(api_key=None), store=open_store(":memory:"))
    tester = StressTester(runner, store, _NoModel())
    reps = {a: V.readings(tester, store, a, compute_params(store, a)) for a in V.TWIN_PAIR}
    return store, reps


def test_card_shows_both_readings_for_each_twin(env):
    _, reps = env
    c1, c16 = V.card(reps["ALERT-01"]), V.card(reps["ALERT-16"])
    assert c1["level"] == "HIGH" and c16["level"] == "ELEVATED"
    assert c1["file"]["title"] == "This FILE rests on exactly one fact."
    assert c1["file"]["chips"][0] == "registry flag on UPI handle C (I4C-flagged) is correct"
    assert "against HIGH" in c1["close"]["title"]
    assert "reopen" in c16["close"]["title"].lower()
    assert any("Brother" in c for c in c16["close"]["chips"])
    assert not any("Sister" in c for c in c16["close"]["chips"])
    # a FILE on ELEVATED signals carries the engine's own caveat
    assert any("ELEVATED" in n for n in c16["file"]["notes"])


def test_chips_come_from_the_report_hypotheses(env):
    _, reps = env
    r = reps["ALERT-16"]["NOT_FILE"]
    targets = {h["target"] for h in r["hypotheses"]}
    for chip in V.reading(r)["chips"]:
        assert any(t in chip for t in targets), chip


def test_twins_look_identical_except_the_flagged_counterparty_signal(env):
    store, reps = env
    facts = {a: V.base_facts(store, reps[a]["FILE"]) for a in V.TWIN_PAIR}
    same = V.shared_features(store.get_alert("ALERT-01"), store.get_alert("ALERT-16"),
                             facts["ALERT-01"], facts["ALERT-16"])
    assert all(f["same"] for f in same), same
    assert facts["ALERT-01"]["F-TOTAL-CREDIT"] == 345000
    diff = [s["signal_id"] for s in V.signal_contrast(reps["ALERT-01"]["FILE"],
                                                      reps["ALERT-16"]["FILE"]) if s["differs"]]
    assert diff == ["S-FLAGGED-COUNTERPARTY"]


def test_readings_have_no_memo(env):
    _, reps = env
    assert all("memo" not in r for rr in reps.values() for r in rr.values())
