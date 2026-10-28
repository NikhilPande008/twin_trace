"""
Corpus loader — domain/corpus/rules/*.yaml -> row dicts for Store.upsert_corpus().

parse_rule() converts domain/corpus/rules/*.yaml entries to Store-compatible row dicts.
"""

import glob
import json
import sys
from datetime import date
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
RULES_DIR = REPO_ROOT / "domain" / "corpus" / "rules"

SNAPSHOT_DATE = date(2026, 9, 11)

# ── YAML → row ────────────────────────────────────────────────────────────────

def parse_rule(rule: dict, source_file: str) -> dict:
    """Convert one YAML rule entry to a flat dict matching REGULATORY_CORPUS columns."""
    ps = rule.get("primary_source", {}) or {}

    # dates
    def to_date(val):
        if val is None:
            return None
        if isinstance(val, date):
            return val
        try:
            return date.fromisoformat(str(val))
        except ValueError:
            return None

    return {
        "RULE_ID":              rule["id"],
        "CATEGORY":             rule.get("category", "UNKNOWN"),
        "SUBCATEGORY":          rule.get("subcategory"),
        "RULE_TEXT":            rule.get("rule", "").strip(),
        "APPLIES_TO":           json.dumps(rule.get("applies_to") or []),
        "SOURCE_DOCUMENT":      ps.get("document"),
        "SOURCE_URL":           ps.get("url"),
        "SOURCE_URL_VERIFIED":  bool(ps.get("url_verified", False)),
        "SOURCE_SECTION":       ps.get("section"),
        "SOURCE_ACCESSED_DATE": to_date(ps.get("accessed_date")),
        "EFFECTIVE_DATE":       to_date(rule.get("effective_date")),
        "SNAPSHOT_DATE":        to_date(rule.get("snapshot_date")) or SNAPSHOT_DATE,
        "LAST_VERIFIED":        to_date(rule.get("last_verified")),
        "EVIDENCE_LEVEL":       rule.get("evidence_level", "NEEDS-VERIFICATION"),
        "MY_SYNTHESIS":         (rule.get("my_synthesis") or "").strip() or None,
        "GAP_NOTES":            (rule.get("gap_notes") or "").strip() or None,
        "RELATED_RULES":        json.dumps(rule.get("related_rules") or []),
    }


def load_yaml_files() -> list[dict]:
    rows = []
    files = sorted(glob.glob(str(RULES_DIR / "*.yaml")))
    if not files:
        print(f"ERROR: No YAML files found in {RULES_DIR}", file=sys.stderr)
        sys.exit(1)

    for fpath in files:
        fname = Path(fpath).name
        with open(fpath, "r") as f:
            data = yaml.safe_load(f)
        rules = data.get("rules", [])
        for rule in rules:
            try:
                rows.append(parse_rule(rule, fname))
            except KeyError as e:
                print(f"WARNING: Skipping {rule.get('id', '?')} in {fname} — missing field {e}")
        print(f"  {fname}: {len(rules)} rules")

    return rows
