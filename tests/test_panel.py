"""Tier panel (T12.7) — offline with scripted per-tier replies."""
import json
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ddp.bootstrap import open_store  # noqa: E402
from ddp.llm import FunctionLLM  # noqa: E402
from ddp.panel import TierPanel, panel_verdict, splitting_fact  # noqa: E402
from ddp.skills import POE_FACTORS, CoPilotSkills  # noqa: E402

CASE = {"customer_kyc": "Salaried", "transactions": [{"txn_id": "T1", "amount_inr": 100}],
        "signal_tags": ["I4C_FLAG"]}


def _reply(n_triggered: int) -> str:
    return json.dumps({"factors": [
        {"factor_id": f, "factor_name": n,
         "assessment": "triggered" if i < n_triggered else "clear",
         "evidence": "x", "evidence_txn_ids": [], "rules_cited": []}
        for i, (f, n) in enumerate(POE_FACTORS)]})


class TieredLLM(FunctionLLM):
    """Answers by tier, records which tiers were asked and on which thread."""
    def __init__(self, by_tier, seen):
        super().__init__(lambda p: "")
        self.by_tier, self.seen = by_tier, seen

    def complete(self, prompt, tier="reasoning", **kw):
        self.seen.append((tier, threading.get_ident()))
        self.last_call = {"provider": "test", "tier": tier, "model_requested": f"m-{tier}"}
        out = self.by_tier[tier]
        if isinstance(out, Exception):
            raise out
        return out


def _panel(by_tier, seen=None, parallel=True):
    seen = [] if seen is None else seen
    return TierPanel(lambda: CoPilotSkills(llm=TieredLLM(by_tier, seen)), parallel=parallel), seen


def test_unanimous_file_is_not_contested():
    panel, seen = _panel({t: _reply(5) for t in ("triage", "reasoning", "disposition")})
    r = panel.run(CASE)
    assert r["unanimous"] == "FILE" and not r["contested"] and r["complete"]
    assert sorted(t for t, _ in seen) == ["disposition", "reasoning", "triage"]


def test_disagreement_is_contested_and_names_the_split_factors():
    panel, _ = _panel({"triage": _reply(5), "reasoning": _reply(1), "disposition": _reply(5)})
    r = panel.run(CASE)
    assert r["contested"] and r["unanimous"] is None
    assert r["recommendations"] == {"triage": "FILE", "reasoning": "REVIEW", "disposition": "FILE"}
    assert r["split_factors"] == [f for f, _ in POE_FACTORS[1:5]]


def test_a_failed_tier_is_reported_and_the_panel_is_incomplete():
    panel, _ = _panel({"triage": _reply(5), "reasoning": RuntimeError("503"),
                       "disposition": _reply(5)})
    r = panel.run(CASE)
    assert not r["complete"] and r["tiers_failed"] == ["reasoning"]
    assert "503" in r["errors"]["reasoning"]
    assert r["unanimous"] == "FILE"                     # two answering tiers agree


def test_one_answering_tier_is_never_called_unanimous():
    panel, _ = _panel({"triage": _reply(5), "reasoning": RuntimeError("x"),
                       "disposition": RuntimeError("y")})
    r = panel.run(CASE)
    assert r["unanimous"] is None and not r["contested"]


def test_tiers_run_in_parallel_threads():
    barrier = threading.Barrier(3, timeout=5)   # sequential calls would time out here

    class Waiting(TieredLLM):
        def complete(self, prompt, tier="reasoning", **kw):
            barrier.wait()
            return super().complete(prompt, tier, **kw)

    seen = []
    panel = TierPanel(lambda: CoPilotSkills(llm=Waiting(
        {t: _reply(0) for t in ("triage", "reasoning", "disposition")}, seen)))
    r = panel.run(CASE)
    assert r["complete"] and len({tid for _, tid in seen}) == 3


def test_panel_is_recorded_as_evidence():
    store = open_store(":memory:")
    panel, _ = _panel({t: _reply(5) for t in ("triage", "reasoning", "disposition")},
                      parallel=False)
    r = panel.run(CASE, store=store, alert_id="ALERT-01")
    ev = store.get_evidence(r["evidence_id"])
    assert ev["TYPE"] == "tier_panel" and json.loads(ev["CONTENT_JSON"])["unanimous"] == "FILE"


def test_splitting_fact_is_the_smallest_flip_set():
    rep = {"minimal_flip_sets": [[{"label": "a"}, {"label": "b"}], [{"label": "only c"}]]}
    assert splitting_fact(rep) == "only c"
    assert splitting_fact({"minimal_flip_sets": []}) is None


def test_verdict_is_deterministic_over_assessments():
    sk = CoPilotSkills()
    a = json.loads(_reply(3))["factors"]
    v1 = panel_verdict({"triage": a, "reasoning": a}, sk.evidence_sufficiency_summary)
    v2 = panel_verdict({"triage": a, "reasoning": a}, sk.evidence_sufficiency_summary)
    assert v1 == v2 and v1["unanimous"] == "FILE"


def test_contested_chip_does_not_reveal_the_lean():
    from ddp.watch import alert_reasons
    store = open_store(":memory:")
    panel, _ = _panel({"triage": _reply(5), "reasoning": _reply(0), "disposition": _reply(5)},
                      parallel=False)
    panel.run(CASE, store=store, alert_id="ALERT-03")
    (chip,) = [r for r in alert_reasons(store, "ALERT-03") if r["kind"] == "contested"]
    assert "FILE" not in chip["text"] and "NOT" not in chip["text"]


def test_recorded_panel_renders_in_the_ai_section_offline():
    import tempfile
    from tests.test_app_smoke import _app, _proof_on
    with tempfile.TemporaryDirectory() as tmp:
        db = str(Path(tmp) / "p.sqlite3")
        store = open_store(db)
        panel, _ = _panel({"triage": _reply(5), "reasoning": _reply(1), "disposition": _reply(5)},
                          parallel=False)
        panel.run(CASE, store=store, alert_id="ALERT-01")
        at = _app(db)
        at.run()
        at.sidebar.radio[0].set_value("Disposition Panel").run()
        _proof_on(at)
        assert not at.exception, at.exception
        text = " ".join(m.value for m in at.markdown)
        assert "CONTESTED" in text and "Models split on" in text



def test_demo_panel_spends_the_session_budget(monkeypatch):
    from ddp.bootstrap import build_panel
    from ddp.config import Settings
    from ddp.llm import CallBudget
    monkeypatch.setenv("NEBIUS_API_KEY", "k")
    monkeypatch.setenv("DDP_DEMO_MODE", "1")
    s, store = Settings(), open_store(":memory:")
    assert build_panel(store, s) is None                      # no session budget: no panel
    budget = CallBudget(FunctionLLM(lambda p: _reply(5)), 2)
    panel = build_panel(store, s, session_llm=budget)
    assert panel.make_skills()._llm is budget and panel.make_skills()._llm is budget
    assert panel.parallel is False
