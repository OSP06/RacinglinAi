# streamlit_app.py

import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- CONFIG ---
st.set_page_config(page_title="RacingLineAI - F1 Strategy Dashboard", layout="wide")
st.title("🏎️ RacingLineAI – F1 Strategy Dashboard")
st.markdown("Analyze tyre degradation, pit strategy, and sector performance for 2023 races.")

# --- LOAD DATA ---
@st.cache_data
def load_all_race_data():
    data_path = "data/processed"
    dfs = []
    for file in os.listdir(data_path):
        if file.endswith(".csv") and "race_summary" in file:
            df = pd.read_csv(os.path.join(data_path, file))
            gp_name = file.replace("race_summary_2023_", "").replace(".csv", "")
            df["GrandPrix"] = gp_name
            dfs.append(df)
    return pd.concat(dfs, ignore_index=True)

df = load_all_race_data()
df = df.dropna(subset=["LapTimeSeconds", "TyreLife", "Compound"])

# --- SIDEBAR FILTERS ---
st.sidebar.header("📊 Filters")
gp_list = sorted(df["GrandPrix"].unique())
drivers = sorted(df["Driver"].unique())
compounds = sorted(df["Compound"].unique())

selected_gp = st.sidebar.selectbox("Select Grand Prix", gp_list)
selected_drivers = st.sidebar.multiselect("Select Driver(s)", drivers, default=drivers[:2])
selected_compound = st.sidebar.selectbox("Select Tyre Compound", compounds)

filtered_df = df[
    (df["GrandPrix"] == selected_gp) &
    (df["Driver"].isin(selected_drivers)) &
    (df["Compound"] == selected_compound)
]

# --- PLOT 1: Lap Time vs Tyre Age ---
st.subheader(f"Lap Time Degradation at {selected_gp.title()} on {selected_compound} tyres")
fig1 = px.line(
    filtered_df,
    x="TyreLife",
    y="LapTimeSeconds",
    color="Driver",
    markers=True,
    title="Lap Time vs Tyre Age",
    labels={"TyreLife": "Tyre Age (Laps)", "LapTimeSeconds": "Lap Time (s)"},
    template="plotly_dark"
)
st.plotly_chart(fig1, use_container_width=True)

# --- METRICS ---
st.write("### 📈 Stint Metrics")
metrics_df = filtered_df.groupby("Driver")["LapTimeSeconds"].agg(["mean", "count"]).reset_index()
metrics_df.columns = ["Driver", "Avg Lap Time", "Stint Length"]
st.dataframe(metrics_df.style.format({"Avg Lap Time": "{:.2f}", "Stint Length": "{:.0f}"}))

# --- PLOT 2: Sector Heatmap ---
st.subheader("🔥 Sector Performance Heatmap (Avg Sector Times in Seconds)")

# Ensure sector data exists
if all(col in df.columns for col in ["Sector1TimeSeconds", "Sector2TimeSeconds", "Sector3TimeSeconds"]):
    sector_df = df[
        (df["GrandPrix"] == selected_gp) & 
        (df["Driver"].isin(selected_drivers))
    ].groupby("Driver")[[
        "Sector1TimeSeconds", "Sector2TimeSeconds", "Sector3TimeSeconds"
    ]].mean().round(3).reset_index()

    sector_df = sector_df.rename(columns={
        "Sector1TimeSeconds": "Sector 1",
        "Sector2TimeSeconds": "Sector 2",
        "Sector3TimeSeconds": "Sector 3"
    })

    sector_melted = sector_df.melt(id_vars="Driver", var_name="Sector", value_name="Time (s)")

    fig2 = px.density_heatmap(
        sector_melted,
        x="Sector", y="Driver", z="Time (s)",
        color_continuous_scale="Viridis_r",
        title="Sector Heatmap: Lower Time = Better",
        height=400
    )
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.warning("Sector data not found in current dataset.")

# Pit Stop Time Saved vs Undercut Effect
st.subheader("⏱️ Pit Stop Time Saved & Undercut Opportunities")

if "PitInTime" in df.columns and "LapTimeSeconds" in df.columns:
    pit_data = df[
        (df["GrandPrix"] == selected_gp) &
        (df["Driver"].isin(selected_drivers))
    ].copy()

    pit_data = pit_data[pit_data["PitInTime"].notna()]
    pit_data["PitLap"] = pit_data["LapNumber"]

    undercut_df = []

    for driver in selected_drivers:
        driver_pits = pit_data[pit_data["Driver"] == driver].sort_values("PitLap")
        for pitlap in driver_pits["PitLap"]:
            pre_pit = df[(df["Driver"] == driver) & (df["LapNumber"] == pitlap - 1)]
            post_pit = df[(df["Driver"] == driver) & (df["LapNumber"] == pitlap + 1)]
            if not pre_pit.empty and not post_pit.empty:
                undercut_df.append({
                    "Driver": driver,
                    "PitLap": pitlap,
                    "PrePitLapTime": pre_pit["LapTimeSeconds"].values[0],
                    "PostPitLapTime": post_pit["LapTimeSeconds"].values[0],
                    "TimeSaved": pre_pit["LapTimeSeconds"].values[0] - post_pit["LapTimeSeconds"].values[0]
                })

    undercut_df = pd.DataFrame(undercut_df)
    fig3 = px.bar(
        undercut_df,
        x="Driver", y="TimeSaved",
        color="PitLap",
        title="Estimated Time Saved After Pit (Undercut Effect)",
        labels={"TimeSaved": "Time Gained (sec)", "PitLap": "Lap #"},
        color_continuous_scale="Plasma"
    )
    st.plotly_chart(fig3, use_container_width=True)
else:
    st.warning("PitInTime or LapTime data missing. Cannot calculate undercut.")

# Driver Lap Consistency Plot (Lap Deltas)
st.subheader("📊 Driver Lap Time Consistency by Tyre Compound")

consistency_compound_df = df[
    (df["GrandPrix"] == selected_gp) &
    (df["Driver"].isin(selected_drivers)) &
    (df["Compound"] == selected_compound)
].copy()

consistency_compound_df.sort_values(["Driver", "LapNumber"], inplace=True)
consistency_compound_df["LapDelta"] = consistency_compound_df.groupby("Driver")["LapTimeSeconds"].diff().round(2)

fig5 = px.line(
    consistency_compound_df,
    x="LapNumber", y="LapDelta", color="Driver",
    line_dash="Compound",
    title=f"Lap-to-Lap Delta by Tyre Compound ({selected_compound})",
    labels={"LapDelta": "Δ Lap Time (s)", "LapNumber": "Lap"},
    markers=True,
    template="plotly_white"
)
st.plotly_chart(fig5, use_container_width=True)

# --- Footer ---
st.markdown("---")
st.caption("Built by Om Patel | Powered by FastF1 + Streamlit")
