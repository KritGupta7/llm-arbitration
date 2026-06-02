import requests
import streamlit as st

API_BASE_URL = "http://127.0.0.1:8000"


# ── helpers ──────────────────────────────────────────────────────────────────

def api_get(path: str) -> dict | list | None:
    try:
        resp = requests.get(f"{API_BASE_URL}{path}", timeout=60)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error(
            "FastAPI backend is not running. "
            "Start it with:  `uvicorn app.api:app --reload`"
        )
        return None
    except requests.exceptions.HTTPError as exc:
        st.error(f"API error {exc.response.status_code}: {exc.response.text}")
        return None


def api_post(path: str, payload: dict) -> dict | None:
    try:
        resp = requests.post(f"{API_BASE_URL}{path}", json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error(
            "FastAPI backend is not running. "
            "Start it with:  `uvicorn app.api:app --reload`"
        )
        return None
    except requests.exceptions.HTTPError as exc:
        st.error(f"API error {exc.response.status_code}: {exc.response.text}")
        return None


def severity_badge(severity: int) -> str:
    colors = {1: "🟢", 2: "🟡", 3: "🟠", 4: "🔴", 5: "🔴"}
    return colors.get(severity, "⚪")


def render_issues(issues: list[dict], label: str) -> None:
    st.markdown(f"**{label}**")
    if not issues:
        st.caption(f"No {label.lower()}.")
        return
    for i, issue in enumerate(issues, 1):
        sev = issue.get("severity", "?")
        with st.expander(f"{severity_badge(sev)} Issue {i} — severity {sev}"):
            st.markdown(f"> *\"{issue.get('quote', '')}\"*")
            st.markdown(f"**Problem:** {issue.get('problem', '')}")


def render_critic_block(critic: dict, title: str) -> None:
    with st.expander(title):
        col1, col2 = st.columns(2)
        col1.metric("Score", f"{critic.get('score', '—')} / 5")
        col2.metric("Confidence", f"{critic.get('confidence', 0):.0%}")
        st.markdown(f"**Explanation:** {critic.get('explanation', '')}")
        issues = critic.get("issues", [])
        if issues:
            render_issues(issues, "Issues flagged by this critic")
        else:
            st.caption("No issues flagged.")


def render_verdict(data: dict) -> None:
    result = data.get("result", data)

    st.markdown(f"### Summary")
    st.info(result.get("summary", ""))

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Final Score", f"{result.get('final_score', 0):.2f} / 5")
    c2.metric("Confidence", result.get("confidence_level", "—").capitalize())
    c3.metric("Accuracy", f"{result.get('accuracy', {}).get('score', '—')} / 5")
    c4.metric("Logic", f"{result.get('logic', {}).get('score', '—')} / 5")
    c5.metric("Completeness", f"{result.get('completeness', {}).get('score', '—')} / 5")

    st.divider()
    render_issues(result.get("confirmed_issues", []), "Confirmed Issues")

    st.divider()
    render_issues(result.get("dismissed_issues", []), "Dismissed Issues")

    st.divider()
    disagreements = result.get("disagreements", [])
    st.markdown("**Disagreements**")
    if not disagreements:
        st.caption("No disagreements detected.")
    else:
        for d in disagreements:
            st.warning(
                f"**{d.get('type', '')}** (severity: {d.get('severity', '')})\n\n"
                f"{d.get('description', '')}"
            )

    warnings = result.get("warnings", [])
    st.markdown("**Warnings**")
    if not warnings:
        st.caption("No warnings.")
    else:
        for w in warnings:
            st.warning(w)

    st.divider()
    st.markdown("**Critic Details**")
    render_critic_block(result.get("accuracy", {}), "Accuracy Critic")
    render_critic_block(result.get("logic", {}), "Logic Critic")
    render_critic_block(result.get("completeness", {}), "Completeness Critic")


# ── page setup ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="LLM Output Arbitration System",
    page_icon="⚖️",
    layout="wide",
)

st.title("⚖️ LLM Output Arbitration System")
st.caption(
    "Evaluate LLM-generated answers using multiple critic agents, "
    "disagreement detection, and an LLM adjudicator."
)

tab_arbitrate, tab_history, tab_analytics = st.tabs(
    ["Arbitrate", "History", "Analytics"]
)


# ── TAB 1: ARBITRATE ─────────────────────────────────────────────────────────

with tab_arbitrate:
    st.subheader("Submit for Arbitration")

    question = st.text_area("Question", placeholder="e.g. What causes tides?", height=80)
    answer = st.text_area(
        "Answer",
        placeholder="e.g. Tides are caused by the Moon's gravitational pull…",
        height=120,
    )

    if st.button("Run Arbitration", type="primary"):
        if not question.strip():
            st.error("Please enter a question.")
        elif not answer.strip():
            st.error("Please enter an answer.")
        else:
            with st.spinner("Running arbitration — this may take 10–20 seconds…"):
                data = api_post("/arbitrate", {"question": question, "answer": answer})

            if data:
                st.success(f"Arbitration complete — saved as record **#{data.get('id')}**")
                render_verdict(data)


# ── TAB 2: HISTORY ───────────────────────────────────────────────────────────

with tab_history:
    st.subheader("Recent Arbitrations")

    records = api_get("/arbitrations?limit=20")

    if records:
        rows = [
            {
                "ID": r["id"],
                "Question": r["question"][:80] + ("…" if len(r["question"]) > 80 else ""),
                "Final Score": r["final_score"],
                "Confidence": r["confidence_level"].capitalize(),
                "Created At": r["created_at"],
            }
            for r in records
        ]
        st.dataframe(rows, use_container_width=True, hide_index=True)
    elif records is not None:
        st.info("No arbitrations stored yet.")

    st.divider()
    st.subheader("Load a Specific Arbitration")

    record_id = st.number_input("Arbitration ID", min_value=1, step=1, value=1)
    if st.button("Load Arbitration"):
        with st.spinner("Loading…"):
            detail = api_get(f"/arbitrations/{int(record_id)}")
        if detail:
            st.markdown(f"**Question:** {detail.get('question', '')}")
            st.markdown(f"**Answer:** {detail.get('answer', '')}")
            render_verdict(detail)


# ── TAB 3: ANALYTICS ─────────────────────────────────────────────────────────

with tab_analytics:
    st.subheader("Analytics Summary")

    if st.button("Refresh Analytics"):
        st.rerun()

    stats = api_get("/analytics")

    if stats:
        # Top-level metrics
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total Arbitrations", stats["total_arbitrations"])
        c2.metric("Avg Final Score", stats["average_final_score"])
        c3.metric("Confirmed Issues", stats["total_confirmed_issues"])
        c4.metric("Disagreements", stats["disagreement_count"])
        c5.metric("Warnings", stats["warning_count"])

        st.divider()
        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown("**Confidence Distribution**")
            conf = stats["confidence_counts"]
            if any(conf.values()):
                st.bar_chart(conf)
            else:
                st.caption("No data yet.")

            st.markdown("**Quality Distribution**")
            qual = stats["quality_counts"]
            if any(qual.values()):
                st.bar_chart(qual)
            else:
                st.caption("No data yet.")

        with col_right:
            st.markdown("**Average Critic Scores**")
            critic_scores = stats["average_critic_scores"]
            if any(v > 0 for v in critic_scores.values()):
                st.bar_chart(critic_scores)
            else:
                st.caption("No data yet.")

            st.markdown("**Other Metrics**")
            st.table(
                {
                    "Metric": [
                        "Dismissed Issues",
                        "Most Common Severity",
                        "Invalid Records",
                    ],
                    "Value": [
                        stats["total_dismissed_issues"],
                        stats.get("most_common_confirmed_issue_severity") or "—",
                        stats.get("invalid_record_count", 0),
                    ],
                }
            )
