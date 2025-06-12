# streamlit_app.py

import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIG ---
st.set_page_config(page_title="RacingLineAI - F1 Strategy Dashboard", layout="wide")

st.title("🏎️ RacingLineAI – F1 Strategy Dashboard")
st.markdown("Analyze tyre degradation and pit strategy based on FastF1 data.")

# --- LOAD DATA ---
@st.cache_data
def load_data():
    df = pd.read_csv("data/processed/race_summary_2023_monza.csv")
    df = df.dropna(subset=["LapTimeSeconds", "TyreLife", "Compound"])
    return df

df = load_data()

# --- SIDEBAR FILTERS ---
st.sidebar.header("📊 Filters")
drivers = sorted(df["Driver"].unique())
compounds = sorted(df["Compound"].unique())

selected_driver = st.sidebar.selectbox("Select Driver", drivers)
selected_compound = st.sidebar.selectbox("Select Tyre Compound", compounds)

filtered_df = df[
    (df["Driver"] == selected_driver) &
    (df["Compound"] == selected_compound)
]

# --- PLOT: Lap Time vs Tyre Age ---
st.subheader(f"Lap Time Degradation for {selected_driver} on {selected_compound} tyres")

fig = px.line(
    filtered_df,
    x="TyreLife",
    y="LapTimeSeconds",
    title="Lap Time vs Tyre Age",
    labels={"TyreLife": "Tyre Age (Laps)", "LapTimeSeconds": "Lap Time (s)"},
    markers=True,
    template="plotly_dark"
)
st.plotly_chart(fig, use_container_width=True)

# --- METRICS ---
avg_lap = filtered_df["LapTimeSeconds"].mean()
stint_len = filtered_df["TyreLife"].max()

col1, col2 = st.columns(2)
col1.metric("📉 Average Lap Time", f"{avg_lap:.2f} sec")
col2.metric("🔁 Stint Length", f"{stint_len} laps")

# --- Footer ---
st.markdown("---")
st.caption("Built by Om Patel | Powered by FastF1 + Streamlit")