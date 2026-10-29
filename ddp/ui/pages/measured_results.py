"""Page: Measured Results (from dated reports in evals/ only)."""

from __future__ import annotations

import streamlit as st

from ...evidence_view import (deterministic_reports, latest_live_holdout, live_eval_reports,
                              summarise_live, summarise_stress)


# ── page: Measured Results ────────────────────────────────────────────────────
def page_measured_results():
    st.header("Measured Results")
    st.markdown(
        "Every number on this page is computed from a dated report committed in `evals/`. "
        "Nothing is typed in by hand, and each section names the file, date and code revision it "
        "came from. **All cases are synthetic. The set is small, and its labels were assigned by "
        "the author, not by an expert panel, so none of this is an accuracy claim.**")

    h = latest_live_holdout()
    st.subheader("1. The same model, with and without the controls")
    if not h:
        st.info("No live holdout run is committed in `evals/`.")
    else:
        c = h["conditions"]
        base, full = c["C2_baseline_no_controls"], c["C3_full_product"]
        st.markdown("**Drafts containing at least one figure that is not a transaction amount or "
                    "a calculator fact**")
        m1, m2, m3 = st.columns(3)
        m1.metric("Same model, no controls",
                  f"{base['drafts_with_unsupported']} of {base['drafts']}",
                  help=f"{base['unsupported_figures_total']} unsupported figures among "
                       f"{base['figures_total']} figures written.")
        m2.metric("Full product",
                  f"{full['drafts_with_unsupported']} of {full['drafts']}",
                  help=f"{full['unsupported_figures_total']} unsupported figures among "
                       f"{full['figures_total']} figures written. The drafter is the same "
                       "model; the gate decides what is accepted.")
        m3.metric("In drafts the product accepted",
                  f"{full['unsupported_in_accepted']} figures",
                  help=f"Unsupported figures found in the {full['accepted_by_gate']} drafts the "
                       "gate accepted.")
        st.caption(
            f"Same {h['cases']} synthetic cases and inputs in every condition. The product's own "
            "drafter still put model-computed figures into half the drafts; the gate stopped "
            "those drafts from being accepted. Run `" + str(h["dir"]) + f"`, {str(h['started_utc'])[:16]} "
            f"UTC, code revision `{h['git_rev']}`, dataset `{h['dataset']}` "
            f"(sha256 `{str(h['dataset_sha256'])[:12]}…`).")

        st.subheader("2. Does the gate catch seeded faults?")
        g1, g2, g3 = st.columns(3)
        g1.metric("Faults caught (all seeded)", f"{h['caught']} of {h['faults_total']}")
        g2.metric("…of the kinds it is designed to catch", f"{h['caught_designed']} of {h['designed_total']}")
        g3.metric("Supported narratives wrongly rejected", f"{h['false_rejections']} of {h['supported_total']}")
        st.caption("The misses are shown, not tuned away: the gate checks figures, not whether the "
                   "sentence around a figure is true.")
        with st.expander(f"All {h['faults_total']} seeded faults and what the gate did"):
            st.dataframe([{"case": f["case"], "fault": f["fault"],
                           "outcome": "caught" if f["caught"] else "MISSED",
                           "labelled": f["expected"], "gate said": f["got"], "text": f["text"]}
                          for f in h["faults"]], hide_index=True, width="stretch")
        if h["label_mismatches"]:
            st.warning("Where the gate disagreed with the author's label: " + " · ".join(
                f"{m['case']} {m['fault'].replace('_', ' ')}: “{m['text']}”"
                for m in h["label_mismatches"]))

    st.subheader("3. Live Nemotron run over 16 synthetic alerts")
    reports = live_eval_reports()
    if not reports:
        st.info("No live 16-alert report is committed in `evals/`.")
    else:
        path, rep = reports[0]
        r = summarise_live(rep, path)
        a1, a2, a3, a4 = st.columns(4)
        a1.metric("11-factor output valid", f"{r['assess_model_valid']} of {r['alerts']}",
                  help="Schema-valid model output, first try or after one repair. Fallback "
                       f"placeholders are never counted. Outcomes: {r['assess_outcomes']}.")
        a2.metric("Agent agrees on clear cases", f"{r['clear_agree']} of {r['clear_cases']}",
                  help=f"An always-FILE rule would get {r['clear_gold_file']} of "
                       f"{r['clear_cases']} right.")
        a3.metric("Rejected submissions", r["agent_rejections"],
                  help=f"Agent submissions rejected by validation, across "
                       f"{r['agent_alerts_with_rejection']} alerts; each was returned to the "
                       "model, which corrected it.")
        a4.metric("Contested cases filed", f"{r['contested_filed']} of {r['contested']}",
                  help="Ambiguous by design. The agent leans towards filing.")
        st.caption(
            f"Median time per alert: {r['median_assess_s']} s for the 11-factor assessment and "
            f"{r['median_agent_s']} s for the agent. `{r['source']}`, "
            f"{str(r['started_utc'])[:16]} UTC, compute backend `{r['compute_backend']}`. "
            f"{r['assess_truncated']} assessments were cut off at the token limit and repaired.")
        if not r["current_seed"]:
            st.caption("**Earlier run on the old seed.** The alerts were given multi-transaction "
                       "histories on 2026-10-28, after this run; its figures describe the old seed.")
    _stress_line(reports)


def _stress_line(live_reports):
    """Gold-FILE alerts at HIGH, from the newest report (deterministic or live) on this seed."""
    runs = sorted([(p, d) for p, d in deterministic_reports() + live_reports],
                  key=lambda x: x[1].get("started_utc", ""), reverse=True)
    stress = [summarise_stress(d, p) for p, d in runs]
    s = next((x for x in stress if x["current_seed"]), stress[0] if stress else None)
    if s is None:
        return
    st.caption(f"Stress test (deterministic, no model): {s['stress_high']} of {s['gold_file']} "
               "gold-FILE alerts reach a HIGH modeled level from calculator signals; the rest "
               "rest on evidence the calculator does not see. "
               f"`{s['source']}`, {str(s['started_utc'])[:16]} UTC"
               + ("." if s["current_seed"] else ", an earlier run on the old seed."))

    with st.expander("What these results do not show", expanded=True):
        st.markdown(
            "- **Small, author-labelled, synthetic.** Six holdout cases and sixteen development "
            "alerts support no general accuracy claim.  \n"
            "- **No officer study.** Review time, corrections and real-world error rates were "
            "not measured.  \n"
            "- **The gate checks figures only.** Wrong-party and invented-context statements "
            "built from real figures pass it and are listed for human review.  \n"
            "- **One model family; each live figure above is from one run.** Model output varies "
            "between runs. Repeat runs of the agent, two per condition, are in "
            "`evals/AGENT-LEAN-2026-10-28.md` and `evals/AGENT-FRAMING-2026-10-28.md`.  \n"
            "- **No cost figure is shown** because none was measured here.")
