
import httpx
import pandas as pd
import streamlit as st

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="AgentOps | Observability",
    page_icon="📊",
    layout="wide",
)

st.title("AgentOps")
st.caption("Local-first AI agent observability")

if st.button("Refresh data"):
    st.rerun()

try:
    events_response = httpx.get(API_URL + "/events", timeout=5.0)
    events_response.raise_for_status()
    events = events_response.json()

    analytics_response = httpx.get(API_URL + "/analytics", timeout=5.0)
    analytics_response.raise_for_status()
    analytics = analytics_response.json()

except httpx.HTTPError as exc:
    st.error("Could not connect to the AgentOps API.")
    st.code(str(exc))
    st.info("Start the API with: uvicorn app.main:app --reload")
    st.stop()

df = pd.DataFrame(events)

# Summary metrics
a, b, c, d = st.columns(4)
a.metric("Total events", analytics["total_events"])
b.metric("Successful", analytics["success_events"])
c.metric("Failed", analytics["failed_events"])

average = analytics["average_duration_ms"]
d.metric(
    "Average duration",
    "N/A" if average is None else "{:.1f} ms".format(average),
)

st.divider()

if df.empty:
    st.info("No events yet. Run: python -m app.simulate_agent")
    st.stop()

# Filters
st.subheader("Explore events")

filter1, filter2 = st.columns(2)

with filter1:
    event_types = sorted(df["event_type"].dropna().unique().tolist())
    selected_types = st.multiselect(
        "Event type",
        event_types,
        default=event_types,
    )

with filter2:
    statuses = sorted(df["status"].dropna().unique().tolist())
    selected_statuses = st.multiselect(
        "Status",
        statuses,
        default=statuses,
    )

filtered = df[
    df["event_type"].isin(selected_types)
    & df["status"].isin(selected_statuses)
].copy()

st.dataframe(filtered, use_container_width=True, hide_index=True)

# Duration chart
st.divider()
st.subheader("Event duration")

duration_df = filtered.dropna(subset=["duration_ms"]).copy()

if duration_df.empty:
    st.info("No duration measurements match these filters.")
else:
    duration_df["label"] = (
        duration_df["name"].astype(str)
        + " · "
        + duration_df["trace_id"].astype(str).str.slice(0, 12)
    )
    st.bar_chart(
        duration_df.set_index("label")[["duration_ms"]]
    )

# Trace explorer
st.divider()
st.subheader("Trace explorer")

trace_ids = sorted(df["trace_id"].dropna().unique().tolist())

selected_trace = st.selectbox("Select a trace", trace_ids)

if st.button("Load trace summary"):
    try:
        response = httpx.get(
            API_URL + "/traces/" + selected_trace,
            timeout=5.0,
        )
        response.raise_for_status()
        trace = response.json()

        status = trace["status"]
        if status == "success":
            st.success("Trace status: success")
        elif status == "error":
            st.error("Trace status: error")
        else:
            st.warning("Trace status: running")

        x, y, z = st.columns(3)
        x.metric("Events", trace["event_count"])
        y.metric("Failed events", trace["failed_event_count"])
        z.metric(
            "Sum of event durations",
            "{} ms".format(trace["total_event_duration_ms"]),
        )

        st.json(trace["events"])

    except httpx.HTTPError as exc:
        st.error("Could not load this trace.")
        st.code(str(exc))
