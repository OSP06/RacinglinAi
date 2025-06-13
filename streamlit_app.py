# streamlit_app.py - RacingLineAI v7.2 (Enhanced Data Safety + Pit Fallbacks + Heatmap Sorting)

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(page_title="🏁 RacingLineAI v7.2", layout="wide", initial_sidebar_state="expanded")

TEAM_COLORS = {
    'Red Bull Racing': '#1E41FF', 'Ferrari': '#DC0000', 'Mercedes': '#00D2BE',
    'McLaren': '#FF8700', 'Aston Martin': '#006F62', 'Alpine': '#0090FF',
    'AlphaTauri': '#2B4562', 'Alfa Romeo': '#900000', 'Williams': '#005AFF',
    'Haas F1 Team': '#B6BABD', 'Other': '#AAAAAA'
}

@st.cache_data

def load_data():
    path_2023 = os.path.join("data", "processed", "all_races_combined_with_sectors.csv")
    path_2024 = os.path.join("data", "processed", "all_races_combined_2024.csv")
    df_2023 = pd.read_csv(path_2023)
    df_2023["SeasonYear"] = 2023
    df_2024 = pd.read_csv(path_2024)
    df_2024["SeasonYear"] = 2024
    df = pd.concat([df_2023, df_2024], ignore_index=True)
    # Only drop rows where core time data is missing — retain Pit columns even if NaN
    df = df.dropna(subset=["LapTimeSeconds", "TyreLife", "Compound"])
    df["SeasonYear"] = df["SeasonYear"].astype(int)
    df["Team"] = df["Team"].fillna("Other")
    df["TeamColor"] = df["Team"].map(TEAM_COLORS).fillna(TEAM_COLORS['Other'])
    driver_team = df.drop_duplicates("Driver")[["Driver", "Team"]].set_index("Driver")["Team"].to_dict()
    driver_colors = {driver: TEAM_COLORS.get(driver_team.get(driver, "Other"), TEAM_COLORS['Other']) for driver in df['Driver'].unique()}
    df["DriverColor"] = df["Driver"].map(driver_colors)
    df["Driver_Season"] = df["Driver"] + " (" + df["SeasonYear"].astype(str) + ")"
    df["GP_Season"] = df["GrandPrix"] + " (" + df["SeasonYear"].astype(str) + ")"
    return df, driver_colors

st.sidebar.title("🏎️ RacingLineAI Filters")
df, driver_colors = load_data()

seasons = sorted(df["SeasonYear"].unique())
drivers = sorted(df["Driver"].unique())
compounds = sorted(df["Compound"].dropna().unique())
gps = sorted(df["GrandPrix"].unique())

selected_season = st.sidebar.selectbox("Season", ["All"] + list(map(str, seasons)))
selected_gp = st.sidebar.selectbox("Grand Prix", ["All"] + gps)
default_drivers = [d for d in ["VER", "LEC"] if d in drivers]
selected_drivers = st.sidebar.multiselect("Drivers", drivers, default=default_drivers)
compound_map = {
    'SOFT': 'Soft', 'MEDIUM': 'Medium', 'HARD': 'Hard',
    'INTERMEDIATE': 'Intermediate', 'WET': 'Wet'
}
compound_options_ui = list(compound_map.keys())
selected_compounds_ui = st.sidebar.multiselect(
    "Tyre Compounds", options=compound_options_ui, default=compound_options_ui
)
selected_compound = [compound_map[c] for c in selected_compounds_ui]

#Apply Filters
filtered_df = df[df["Driver"].isin(selected_drivers)]
if selected_season != "All":
    filtered_df = filtered_df[filtered_df["SeasonYear"] == int(selected_season)]
if selected_gp != "All":
    filtered_df = filtered_df[filtered_df["GrandPrix"] == selected_gp]
if selected_compound:
    filtered_df = filtered_df[filtered_df["Compound"].isin(selected_compound)]

st.title("🏁 RacingLineAI v7.2 - AI Insights + Tyre-Weather Intelligence")

# --- Driver Summary ---
st.header("📌 Driver Performance Summary Table")
summary = filtered_df.groupby("Driver").agg(
    AvgLap=("LapTimeSeconds", "mean"),
    FastestLap=("LapTimeSeconds", "min"),
    PitCount=("PitLap", lambda x: x.notna().sum()),
    BestStint=("AvgLapTime", "min"),
    Consistency=("LapTimeSeconds", "std")
).reset_index()
wet = filtered_df[filtered_df["IsWetLap"] == True].groupby("Driver")["LapTimeSeconds"].mean()
dry = filtered_df[filtered_df["IsWetLap"] == False].groupby("Driver")["LapTimeSeconds"].mean()
summary["WetDryDelta"] = wet - dry
st.dataframe(summary.round(2))

# --- Weather Impact Index ---
st.header("🌧️ Weather Impact Index")
wii = (dry - wet) / filtered_df.groupby("Driver")["LapTimeSeconds"].std()
wii_df = wii.reset_index(name="WeatherImpactIndex").dropna().sort_values("WeatherImpactIndex", ascending=False)
fig = px.bar(wii_df, x="Driver", y="WeatherImpactIndex", color="Driver", color_discrete_map=driver_colors)
fig.update_layout(title="WII: Who performs best in the wet")
st.plotly_chart(fig, use_container_width=True)

# --- Tyre vs Weather Synergy Map ---
st.header("🌡️ Tyre vs Weather Synergy Map")
synergy_df = filtered_df.copy()
synergy_df = synergy_df.dropna(subset=["TrackTemp"])
synergy_df["TrackBand"] = pd.cut(synergy_df["TrackTemp"], bins=[0, 20, 25, 30, 35, 100], labels=["<20°C", "20-25°C", "25-30°C", "30-35°C", ">35°C"])
heat = synergy_df.groupby(["Compound", "TrackBand"])["LapTimeSeconds"].mean().reset_index()
heat_pivot = heat.pivot(index="Compound", columns="TrackBand", values="LapTimeSeconds")
st.dataframe(heat_pivot.round(3))
fig = px.imshow(heat_pivot, text_auto=True, aspect="auto", color_continuous_scale="YlGnBu",
                labels=dict(color="Avg Lap Time (s)"))
fig.update_layout(title="Avg Lap Time by Tyre Compound vs Track Temperature")
st.plotly_chart(fig, use_container_width=True)

# --- Stint Evolution ---
st.header("📈 Stint Evolution")
fig = px.line(filtered_df, x="LapNumber", y="LapTimeSeconds", color="Driver_Season",
                line_group="Stint", hover_data=["TyreLife", "Compound"],
                template="plotly_dark", color_discrete_map=driver_colors)
fig.update_layout(title="Lap Time Progression per Stint")
st.plotly_chart(fig, use_container_width=True)

# --- Grip Degradation vs TrackTemp ---
st.header("📉 Grip Degradation Slope vs TrackTemp")
slope_df = filtered_df.copy().dropna(subset=["TrackTemp"])
slope_df["TrackTempBand"] = pd.cut(slope_df["TrackTemp"], bins=[0, 20, 25, 30, 35, 100], labels=["<20°C", "20-25°C", "25-30°C", "30-35°C", ">35°C"])
degradation_slopes = slope_df.groupby(["TrackTempBand", "TyreLife"]).LapTimeSeconds.mean().reset_index()
fig = px.line(degradation_slopes, x="TyreLife", y="LapTimeSeconds", color="TrackTempBand",
                template="plotly_dark", markers=True)
fig.update_layout(title="Degradation Slope Grouped by Track Temp Band", xaxis_title="Tyre Life", yaxis_title="Avg Lap Time")
st.plotly_chart(fig, use_container_width=True)

# --- Tyre Wear Projection ---
st.header("🔮 Tyre Wear Projection")
deg_df = filtered_df[filtered_df["IsWetLap"] == False].groupby(["Driver_Season", "TyreLife"]).LapTimeSeconds.mean().reset_index()
if deg_df.empty:
    st.warning("No dry laps available for tyre degradation projection.")
else:
    fig = px.scatter(deg_df, x="TyreLife", y="LapTimeSeconds", color="Driver_Season", trendline="ols",
                    template="plotly_dark", color_discrete_map=driver_colors)
    fig.update_layout(title="Tyre Degradation Curve (Dry Laps Only)")
    st.plotly_chart(fig, use_container_width=True)

# --- Dry vs Wet Compound ---
st.header("🌦️ Dry vs Wet Comparison by Compound")
compare_df = filtered_df.copy()
compare_df["Condition"] = compare_df["IsWetLap"].map(lambda x: "Wet" if x else "Dry")
fig = px.box(compare_df, x="Compound", y="LapTimeSeconds", color="Condition",
            points="all", template="plotly_dark")
st.plotly_chart(fig, use_container_width=True)

# --- Pit Timeline ---
st.header("🛠️ Pit Strategy Timeline")
pit_df = filtered_df[filtered_df["PitLap"].notna()].drop_duplicates(subset=["Driver", "PitLap"])
fig = px.scatter(pit_df, x="PitLap", y="Driver_Season", color="Compound",
                symbol="Compound", template="plotly_dark")
fig.update_layout(title="Pit Stop Lap Timing", xaxis_title="Lap Number", yaxis_title="Driver")
st.plotly_chart(fig, use_container_width=True)

# --- Pit Loss Time ---
st.header("⏱️ Pit Stop Time Loss")
# Handle missing drivers
pit_loss = filtered_df[filtered_df["PitDuration"].notna()].groupby("Driver")["PitDuration"].mean().reset_index()
missing_drivers = [d for d in selected_drivers if d not in pit_loss["Driver"].unique()]
if missing_drivers:
    st.info(f"Note: No valid pit stop data found for: {', '.join(missing_drivers)}")
if pit_loss.empty:
    st.warning("No pit duration data available for selected filters. Please check if 'PitInTime' and 'PitOutTime' were correctly exported.")
else:
    # Optional: Fill 0s to show all selected drivers
    all_drivers_df = pd.DataFrame({"Driver": selected_drivers})
    pit_loss = all_drivers_df.merge(pit_loss, on="Driver", how="left").fillna(0)
    fig = px.bar(pit_loss, x="Driver", y="PitDuration", color="Driver", color_discrete_map=driver_colors)
    fig.update_layout(title="Average Pit Stop Time Lost (s)")
    st.plotly_chart(fig, use_container_width=True)

# --- Race Start ---
st.header("🚦 Race Start Analysis (Lap 1–3 Avg)")
start_df = filtered_df[filtered_df["LapNumber"] <= 3]
start_summary = start_df.groupby("Driver")["LapTimeSeconds"].mean().reset_index(name="StartAvgLap")
fig = px.bar(start_summary, x="Driver", y="StartAvgLap", color="Driver",
            color_discrete_map=driver_colors, template="plotly")
fig.update_layout(title="Lap 1–3 Average Lap Times")
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.caption("🔧 RacingLineAI v7.2 | Built by Om Patel | Enhanced AI + Weather-Grip Analysis")
