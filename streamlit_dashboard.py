# Note: This script requires Streamlit. If you're running in an environment without it,
# you must switch to a local Python environment where `streamlit` is installed.

try:
    import streamlit as st
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns
except ModuleNotFoundError as e:
    raise ImportError("This script requires the 'streamlit' package. Please run it in a local environment where Streamlit is installed.") from e

st.set_page_config(page_title="BNPL Risk Monitoring Dashboard", layout="wide")
st.title("📊 BNPL Risk Monitoring Dashboard")

# --- 1. File Upload ---
st.sidebar.header("Upload Data Files")
segment_file = st.sidebar.file_uploader("Upload segment_score_summary.csv", type=["csv"])
override_file = st.sidebar.file_uploader("Upload override_df.csv", type=["csv"])

if segment_file and override_file:
    segment_df = pd.read_csv(segment_file)
    override_df = pd.read_csv(override_file)

    # --- 2. Plot Default Rate by Score Bin ---
    st.subheader("1. 📈 Default Rate by Score Bin")
    fig, ax = plt.subplots()
    sns.lineplot(
        data=segment_df,
        x="score_bin",
        y="default_rate",
        hue="risk_segment",
        style="risk_segment",
        markers=True,
        dashes=False,
        ax=ax
    )
    ax.set_ylabel("Default Rate")
    ax.set_xlabel("Score Bin")
    ax.set_title("Default Rate by Score Bin and Risk Segment")
    st.pyplot(fig)

    # --- 3. Policy Trigger Status ---
    st.subheader("2. 📌 Policy Trigger Status")
    policy_status = segment_df["policy_trigger"].iloc[0]
    if policy_status:
        st.success("✅ Adaptive Policy Triggered")
    else:
        st.info("🟢 No Policy Triggered")

    # --- 4. Anomalies Table ---
    st.subheader("3. 🔍 Anomaly Detection")
    anomaly_table = segment_df[segment_df["low_risk_anomaly"] == True][["score_bin", "risk_segment", "default_rate"]]
    st.dataframe(anomaly_table, use_container_width=True)

    # --- 5. Override Simulation Table ---
    st.subheader("4. ⚙️ Override Simulation")
    st.dataframe(override_df, use_container_width=True)

    # --- 6. Optional: Strategy Brief Toggle ---
    with st.expander("🧠 Strategy Brief"):
        st.markdown("""
        - Several low-risk segments show higher default rates than high-risk ones.
        - Adaptive override has been simulated for affected bins.
        - Recommended action: retrain model or review risk thresholds.
        """)
else:
    st.warning("⬅️ Please upload both data files to proceed.")

    # --- 7. Trend Over Time (Line Chart) ---
    st.subheader("5. 📈 Trend Over Time by Segment")
    if "date" in segment_df.columns:
        segment_df["date"] = pd.to_datetime(segment_df["date"])
        segments = segment_df["risk_segment"].unique().tolist()
        selected_segments = st.multiselect("Select segments", segments, default=segments)

        trend_data = segment_df[segment_df["risk_segment"].isin(selected_segments)]
        fig, ax = plt.subplots()
        sns.lineplot(data=trend_data, x="date", y="score", hue="risk_segment", ax=ax)
        ax.set_title("Score Trend Over Time")
        ax.set_ylabel("Average Score")
        ax.set_xlabel("Date")
        st.pyplot(fig)
    else:
        st.info("No `date` column found in segment data. Skipping trend chart.")

    # --- 8. Override Volume (Bar Chart) ---
    st.subheader("6. 📊 Override Volume by Segment")
    if "risk_segment" in override_df.columns:
        override_counts = override_df["risk_segment"].value_counts().reset_index()
        override_counts.columns = ["risk_segment", "override_count"]
        fig, ax = plt.subplots()
        sns.barplot(data=override_counts, x="risk_segment", y="override_count", ax=ax)
        ax.set_title("Override Volume by Segment")
        ax.set_ylabel("Number of Overrides")
        ax.set_xlabel("Risk Segment")
        st.pyplot(fig)
    else:
        st.info("`risk_segment` column missing in override_df. Skipping override volume chart.")

    # --- 9. Approval Rate by Segment ---
    st.subheader("7. ✅ Approval Rate by Segment")
    if "approved" in override_df.columns:
        approval_rate = override_df.groupby("risk_segment")["approved"].mean().reset_index()
        approval_rate.columns = ["risk_segment", "approval_rate"]
        fig, ax = plt.subplots()
        sns.barplot(data=approval_rate, x="risk_segment", y="approval_rate", ax=ax)
        ax.set_title("Approval Rate by Risk Segment")
        ax.set_ylabel("Approval Rate")
        ax.set_xlabel("Risk Segment")
        ax.set_ylim(0, 1)
        st.pyplot(fig)
    else:
        st.info("`approved` column missing in override_df. Cannot calculate approval rates.")

    # --- 10. Risk Alerts ---
    st.subheader("8. ⚠️ Risk Alerts")
    high_risk_flags = segment_df[
        (segment_df["default_rate"] > 0.15) & (segment_df["risk_segment"].isin(["low", "medium"]))
    ][["score_bin", "risk_segment", "default_rate"]]
    if not high_risk_flags.empty:
        st.warning("🚨 Segments with unexpected high default rates:")
        st.dataframe(high_risk_flags)
    else:
        st.success("✅ No abnormal segments detected.")


