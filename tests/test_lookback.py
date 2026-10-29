"""Rule-change lookback (T12.12) — offline with a scripted page and model."""
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402

from ddp.bootstrap import open_store  # noqa: E402
from ddp.compute import ComputeRunner  # noqa: E402
from ddp.llm import FunctionLLM  # noqa: E402
from ddp.lookback import (check_rule, domain_allowed, fetch_page, promote,  # noqa: E402
                          verify_quote)
from ddp.skills import CoPilotSkills  # noqa: E402
from ddp.watch import DEMO_RATIONALES  # noqa: E402
from tests.test_watch import _record  # noqa: E402

PAGE = ("Header text. A suspicious transaction report shall be furnished not later than seven "
        "working days on being satisfied that the transaction is suspicious.   Footer.")
QUOTE = ("A suspicious transaction report shall be furnished not later than seven working days "
         "on being satisfied that the transaction is suspicious.")


class _Resp:
    def __init__(self, status, body):
        self.status_code, self._b = status, body

    def json(self):
        return self._b


def _post(page=PAGE):
    sent = []

    def post(url, headers, json, timeout):
        sent.append(json)
        return _Resp(200, {"results": [{"url": json["urls"][0], "raw_content": page}]})
    return post, sent


def _skills(store, quote=QUOTE, changed=False):
    return CoPilotSkills(store, llm=FunctionLLM(lambda p: json.dumps(
        {"changed": changed, "quote": quote, "summary": "Same 7-working-day deadline."})))


def test_only_regulator_domains_are_fetched():
    assert domain_allowed("https://fiuindia.gov.in/files/x.html")
    assert domain_allowed("https://www.rbi.org.in/Scripts/a.aspx")
    assert not domain_allowed("https://example.com/fiuindia.gov.in")
    assert fetch_page("k", "https://example.com/x")["status"] == "refused"


def test_verbatim_check_ignores_whitespace_but_not_words():
    assert verify_quote(QUOTE, PAGE)[0]
    assert verify_quote(QUOTE.replace("  ", " "), PAGE.replace(" ", "\n  "))[0]
    assert not verify_quote(QUOTE.replace("seven", "fifteen"), PAGE)[0]
    assert not verify_quote("seven working days", PAGE)[0]          # too short to mean anything


def test_verified_proposal_is_pending_and_never_indexed():
    store = open_store(":memory:")
    post, sent = _post()
    r = check_rule(store, _skills(store), "STR-002", tavily_key="k", _post=post)
    assert r["status"] == "ok" and r["STATUS"] == "PENDING" and r["QUOTE_VERIFIED"] == 1
    assert sent[0]["urls"] == [store.query("SELECT SOURCE_URL FROM REGULATORY_CORPUS WHERE "
                                           "RULE_ID='STR-002'")[0]["SOURCE_URL"]]
    page_ev = store.get_evidence(r["PAGE_EVIDENCE_ID"])
    assert page_ev["TYPE"] == "regulator_page" and page_ev["ALERT_ID"] is None
    hits = CoPilotSkills(store).regulatory_lookup("furnished not later than seven working days")
    assert all(h["rule_text"] != QUOTE for h in hits)


def test_invented_quote_is_rejected_and_cannot_be_promoted():
    store = open_store(":memory:")
    post, _ = _post()
    r = check_rule(store, _skills(store, quote=QUOTE.replace("seven", "five"), changed=True),
                   "STR-002", tavily_key="k", _post=post)
    assert r["STATUS"] == "REJECTED_UNVERIFIED" and r["CHANGED"] is None
    with pytest.raises(ValueError):
        promote(store, ComputeRunner(store), r["PROPOSAL_ID"], "PO-7", "self-asserted")


def test_promotion_flags_only_decisions_citing_the_rule():
    store = open_store(":memory:")
    runner = ComputeRunner(store)
    _record(store, runner, "ALERT-01", "FILE", DEMO_RATIONALES["ALERT-01"][1])     # cites STR-002
    _record(store, runner, "ALERT-16", "NOT_FILE", DEMO_RATIONALES["ALERT-16"][1])  # does not
    post, _ = _post()
    r = check_rule(store, _skills(store, changed=True), "STR-002", tavily_key="k", _post=post)
    assert r["affected"] == 1
    out = promote(store, runner, r["PROPOSAL_ID"], "PO-7", "self-asserted")
    assert [e["ALERT_ID"] for e in out["events"]] == ["ALERT-01"]
    assert out["events"][0]["OUTCOME"] == "needs_review"
    with pytest.raises(ValueError):
        promote(store, runner, r["PROPOSAL_ID"], "PO-7", "self-asserted")   # once only


def test_proposals_are_append_only():
    store = open_store(":memory:")
    post, _ = _post()
    check_rule(store, _skills(store), "STR-002", tavily_key="k", _post=post)
    with pytest.raises(sqlite3.DatabaseError):
        store._exec("UPDATE RULE_PROPOSALS SET STATUS = 'PENDING'")


def test_no_tavily_key_fetches_nothing():
    store = open_store(":memory:")
    assert check_rule(store, _skills(store), "STR-002", tavily_key=None)["status"] == "no_key"


def test_review_screen_lists_proposals_offline():
    import tempfile
    from tests.test_app_smoke import _app
    with tempfile.TemporaryDirectory() as tmp:
        db = str(Path(tmp) / "l.sqlite3")
        store = open_store(db)
        post, _ = _post()
        check_rule(store, _skills(store), "STR-002", tavily_key="k", _post=post)
        at = _app(db)
        at.run()
        at.sidebar.radio[0].set_value("Regulatory Reference").run()
        assert not at.exception, at.exception
        labels = [e.label for e in at.expander]
        assert any(lbl.startswith("STR-002 · PENDING") for lbl in labels), labels


def test_unchanged_rule_cannot_be_promoted():
    store = open_store(":memory:")
    post, _ = _post()
    r = check_rule(store, _skills(store, changed=False), "STR-002", tavily_key="k", _post=post)
    assert r["STATUS"] == "PENDING" and r["CHANGED"] == 0
    with pytest.raises(ValueError, match="nothing to promote"):
        promote(store, ComputeRunner(store), r["PROPOSAL_ID"], "PO-7", "self-asserted")
    assert not store.query("SELECT 1 FROM DECISION_EVENTS")


def test_domain_check_reads_the_real_host():
    assert domain_allowed("https://fiuindia.gov.in:443/files/x.html")
    assert not domain_allowed("https://fiuindia.gov.in.evil.example/x")
    assert not domain_allowed("not a url")
