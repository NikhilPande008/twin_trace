"""The stakes shown in the app cite only PROVEN/ASSUMED corpus rules, and so does every rule ID
written into the UI source."""

from __future__ import annotations

import glob
import re
from pathlib import Path

import yaml

from ddp.stakes import RULE_IDS, STAKES

ROOT = Path(__file__).resolve().parent.parent
ALLOWED = {"PROVEN", "ASSUMED"}


def _levels() -> dict[str, str]:
    out = {}
    for f in glob.glob(str(ROOT / "domain" / "corpus" / "rules" / "*.yaml")):
        for r in yaml.safe_load(open(f))["rules"]:
            out[r["id"]] = r["evidence_level"]
    return out


def test_every_stake_cites_a_proven_or_assumed_rule():
    levels = _levels()
    for rid in RULE_IDS:
        assert levels.get(rid) in ALLOWED, (rid, levels.get(rid))


def test_stakes_add_no_figures_beyond_their_rule():
    levels_text = {}
    for f in glob.glob(str(ROOT / "domain" / "corpus" / "rules" / "*.yaml")):
        for r in yaml.safe_load(open(f))["rules"]:
            levels_text[r["id"]] = r["rule"]
    for s in STAKES:
        for n in re.findall(r"\d+", s["claim"]):
            assert n in levels_text[s["rule_id"]], (s["rule_id"], n)


def test_ui_source_never_cites_a_needs_verification_rule():
    levels = _levels()
    prefixes = {rid.split("-")[0] for rid in levels}
    from ddp.ui import source_files   # app.py and every ddp/ui module
    for path in [*source_files(), ROOT / "ddp" / "stakes.py", ROOT / "ddp" / "glossary.py"]:
        for rid in set(re.findall(r"\b([A-Z]{2,4}-\d{3})\b", path.read_text())):
            if rid.split("-")[0] not in prefixes:
                continue                     # not a corpus ID (e.g. DG-19 gap notes)
            assert rid in levels, f"{path.name}: {rid} is not in the corpus"
            assert levels[rid] in ALLOWED, f"{path.name}: {rid} is {levels[rid]}"
