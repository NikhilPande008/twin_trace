"""The stress-test headline says only what the deterministic report found (T9.6)."""

from __future__ import annotations

import pytest

from ddp.bootstrap import build, compute_params
from ddp.config import Settings
from ddp.stress import StressTester
from ddp.stress.headline import headline


@pytest.fixture(scope="module")
def env():
    store, _, runner, _ = build(Settings(api_key=None), store=None)
    return store, StressTester(runner, store)


def _report(env, alert, disposition):
    store, tester = env
    return tester.run(alert, store.transactions_for(alert), compute_params(store, alert),
                      disposition=disposition)


def test_alert01_file_rests_on_exactly_one_fact(env):
    h = headline(_report(env, "ALERT-01", "FILE"))
    assert h["title"] == "This FILE rests on exactly one fact."
    assert "I4C-flagged" in h["detail"] and "HIGH" in h["detail"]


def test_alert16_closure_names_reopen_conditions(env):
    h = headline(_report(env, "ALERT-16", "NOT_FILE"))
    assert "reopen" in h["title"].lower()
    assert "Brother" in h["detail"] or "Hospital" in h["detail"]
    assert "Sister" not in h["detail"]               # flagging the sister alone does not reopen it


def test_low_signal_file_does_not_claim_calculator_support(env):
    h = headline(_report(env, "ALERT-04", "FILE"))
    assert h["tone"] == "warning" and "do not support" in h["title"]
    assert "exactly one fact" not in h["title"]


def test_closure_against_high_signals_is_not_called_stable(env):
    h = headline(_report(env, "ALERT-01", "NOT_FILE"))
    assert h["tone"] == "warning" and "against HIGH" in h["title"]
    assert "would change this closure" not in h["title"]
    assert "flagged counterparty" in h["detail"].lower()


def test_headline_uses_only_report_labels(env):
    r = _report(env, "ALERT-01", "FILE")
    labels = {x["label"] for f in r["minimal_flip_sets"] for x in f}
    h = headline(r)
    assert any(l in h["detail"] for l in labels)
