from ddp.glossary import GLOSSARY


def test_glossary_defines_the_terms_the_ui_uses():
    terms = " ".join(t for t, _ in GLOSSARY)
    for needed in ("STR", "Ground of Suspicion", "FIU-IND", "I4C", "Calculator of record",
                   "Tipping-off", "Modeled signal level", "SLA"):
        assert needed in terms, needed


def test_glossary_makes_no_compliance_claims():
    text = " ".join(m for _, m in GLOSSARY).lower()
    for banned in ("approved", "compliant", "tamper-proof", "certified"):
        assert banned not in text.replace("not tamper-proof", "").replace("is not a", ""), banned


def test_tooltips_wrap_known_terms_once_and_keep_text_escaped():
    from ddp.glossary import with_tooltips
    out = with_tooltips("The PO files an STR; the PO &amp; I4C. SPOT is not a term.")
    assert out.count('<abbr title="') == 3                  # PO, STR, I4C: first occurrence only
    assert "SPOT" in out and "<abbr" not in out.split("SPOT")[0][-6:]
    assert "&amp;" in out
