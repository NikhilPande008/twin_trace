"""FIU-IND enforcement record and inspector question bank (T12.2 / T12.3) — offline."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ddp.enforcement import COVERAGE, coverage_table, failures, orders, question_bank  # noqa: E402


def test_every_order_is_an_fiu_ind_publication_with_coded_findings():
    codes = set(failures())
    for o in orders():
        assert o["url"].startswith("https://fiuindia.gov.in/pdfs/judgements/")
        assert o["findings"]
        for f in o["findings"]:
            assert f["kind"] in {"charge", "observation", "direction", "warning"}
            assert set(f["codes"]) <= codes, (o["order_id"], f["codes"])


def test_every_failure_has_a_coverage_and_a_reason():
    for code, spec in failures().items():
        assert spec["coverage"] in COVERAGE
        assert spec.get("controls") or spec["coverage"] == "GAP", code
        if spec["coverage"] == "PARTIAL":
            assert spec.get("gap"), f"{code}: say what is not covered"


def test_every_question_cites_orders_that_exist_and_codes_it_answers():
    ids, codes = {o["order_id"] for o in orders()}, set(failures())
    qb = question_bank()
    assert re.fullmatch(r"[0-9a-f]{64}", qb["sha256"])
    for q in qb["questions"]:
        assert q["sources"] and set(q["sources"]) <= ids, q["id"]
        assert set(q["codes"]) <= codes, q["id"]


def test_questions_contain_no_rupee_figures():
    for q in question_bank()["questions"]:
        assert "₹" not in q["text"] and not re.search(r"\d{3,}", q["text"])


def test_closure_quality_is_sourced_from_three_orders():
    row = next(r for r in coverage_table() if r["code"] == "CLOSURE-QUALITY")
    assert set(row["orders"]) == {"FIU-13/2024-UBI", "FIU-09/2024-AXIS", "FIU-19/2022-HSBC"}
    assert row["coverage"] == "ADDRESSED"


def test_enforcement_files_are_not_in_the_regulatory_corpus():
    from ddp.bootstrap import open_store
    store = open_store(":memory:")
    assert not store.query("SELECT 1 FROM REGULATORY_CORPUS WHERE RULE_ID LIKE 'FIU-%'")
