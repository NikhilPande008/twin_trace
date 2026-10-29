"""
Twin Trace
Principal Officer workflow UI (Streamlit, runs locally or on any container host).

Data from ddp.store (SQLite); models from Nebius Token Factory (ddp.llm);
figures from the calculator of record (ddp.compute).

Pages (sidebar), in four areas:
  Inbox     Alert Queue · Twin Cases (ALERT-01 vs ALERT-16)
  Decide    Disposition Panel (verdict card first, proof behind a toggle, GoS drafting) · Proof Check
  Watch     decisions re-checked when the facts they rest on change
  Evidence  Decision Ledger · Measured Results · Dashboard · Regulatory Reference
"""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))

from ddp.config import get_settings  # noqa: E402
from ddp.glossary import GLOSSARY  # noqa: E402
from ddp.ui.pages.alert_queue import page_alert_queue  # noqa: E402
from ddp.ui.pages.dashboard import page_dashboard  # noqa: E402
from ddp.ui.pages.disposition import page_disposition  # noqa: E402
from ddp.ui.pages.ledger import page_ledger  # noqa: E402
from ddp.ui.pages.measured_results import page_measured_results  # noqa: E402
from ddp.ui.pages.proof_check import page_proof_check  # noqa: E402
from ddp.ui.pages.regulatory import page_regulatory  # noqa: E402
from ddp.ui.pages.twins import page_twins  # noqa: E402
from ddp.ui.pages.watch import page_watch  # noqa: E402
from ddp.ui.officer import sign_in_controls  # noqa: E402
from ddp.ui.runtime import get_skills  # noqa: E402
from ddp.ui.widgets import _style  # noqa: E402


def _service_status(kind: str) -> str:
    """'Configured · last call succeeded 12:03 UTC' / '… failed (rate_limited)' / 'Unavailable'."""
    cfg = get_settings()
    if kind == "model":
        if not cfg.llm_configured:
            return "Unavailable (no NEBIUS_API_KEY)"
        log = getattr(get_skills(), "call_log", [])
        if not log:
            return "Configured · no call yet this session"
        last = log[-1]
        when = st.session_state.get("_last_model_check", "")
        if last.get("failed"):
            return f"Configured · last call failed ({last.get('error_kind', 'error')})"
        return "Configured · last call succeeded" + (f" {when}" if when else "")
    if not cfg.tavily_api_key:
        return "Unavailable (no TAVILY_API_KEY)"
    return "Configured · " + st.session_state.get("_last_tavily", "no search yet this session")


def _glossary():
    for term, meaning in GLOSSARY:
        st.markdown(f"**{term}** — {meaning}")


# The officer's week in four areas (T12.14, D2). Twin Cases stays the opening story.
AREAS = [
    ("Inbox", ["Alert Queue", "Twin Cases"]),
    ("Decide", ["Disposition Panel", "Proof Check"]),
    ("Watch", ["Watch"]),
    ("Evidence", ["Decision Ledger", "Measured Results", "Dashboard", "Regulatory Reference"]),
]


# ── main shell ────────────────────────────────────────────────────────────────
def main():
    st.set_page_config(
        page_title="Twin Trace",
        page_icon="🏦",
        layout="wide",
        initial_sidebar_state="auto",   # collapses on narrow screens
    )

    # Sidebar branding
    with st.sidebar:
        st.markdown("### Twin Trace")
        _cfg = get_settings()
        st.caption(
            "AML alert decision support · **synthetic data only** · not affiliated with or "
            "approved by FIU-IND  \n"
            f"Models (Token Factory): {_service_status('model')}  \n"
            f"Web search (Tavily): {_service_status('tavily')}  \n"
            f"Compute: {_cfg.compute_backend}"
            + ("  \n**Public demo:** your session has its own data, reset on reload; "
               f"{_cfg.demo_max_model_calls} model calls per session." if _cfg.demo_mode else "")
        )
        sign_in_controls()
        st.divider()

        pages = [p for _, group in AREAS for p in group]
        area_of = {p: a for a, group in AREAS for p in group}
        # Allow page navigation via session_state (e.g. from Alert Queue buttons).
        # key="page" binds the radio directly to session_state — no index= needed,
        # which avoids the double-click issue caused by index= fighting widget state.
        if "_nav_to" in st.session_state:
            st.session_state["page"] = st.session_state.pop("_nav_to")
        if "page" not in st.session_state or st.session_state["page"] not in pages:
            st.session_state["page"] = pages[0]
        selected_page = st.radio(
            "Navigate", pages, key="page",
            format_func=lambda p: p if area_of[p] == p else f"{area_of[p]} · {p}",
            help="Inbox: what needs you. Decide: one alert. Watch: decisions re-checked when "
                 "their facts change. Evidence: the ledger, measurements and the corpus.")

        with st.expander("Glossary (all terms; hover a dotted term anywhere)"):
            _glossary()
        st.divider()
        st.caption("Corpus snapshot: 2026-09-17  \n"
                   "PROVEN: 15  ·  ASSUMED: 21  \n"
                   "NEEDS-VERIFICATION: 13 (excluded from output)  \n"
                   "POE framework: product-compiled (DG-19)")

    # Route to page
    _style()
    if selected_page == "Alert Queue":
        page_alert_queue()
    elif selected_page == "Twin Cases":
        page_twins()
    elif selected_page == "Proof Check":
        page_proof_check()
    elif selected_page == "Disposition Panel":
        page_disposition()
    elif selected_page == "Decision Ledger":
        page_ledger()
    elif selected_page == "Watch":
        page_watch()
    elif selected_page == "Dashboard":
        page_dashboard()
    elif selected_page == "Measured Results":
        page_measured_results()
    elif selected_page == "Regulatory Reference":
        page_regulatory()


if __name__ == "__main__":
    main()
