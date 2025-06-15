# streamlit_app.py - RacingLineAI v7.2 (Enhanced Data Safety + Pit Fallbacks + Heatmap Sorting)
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from fastf1 import get_session
import matplotlib.pyplot as plt

def plot_circuit_map(season: int, gp_name: str):
    try:
        session = get_session(season, gp_name, 'R')
        session.load(telemetry=True, laps=True)
        lap = session.laps.pick_fastest()
        telemetry = lap.get_telemetry()
        # Check if 'X' and 'Y' columns are present
        if not {'X', 'Y'}.issubset(telemetry.columns):
            st.warning(f"⚠️ Positional telemetry not available for {gp_name} {season}.")
            return
        fig, ax = plt.subplots(figsize=(6, 5))
        ax.plot(telemetry['X'], telemetry['Y'], color='blue', linewidth=2, label='Fastest Lap')
        # Optional: add sector markers
        if hasattr(lap, "sector1_time") and hasattr(lap, "sector2_time"):
            try:
                s1_distance = lap.sector1_distance
                s2_distance = lap.sector2_distance
                s1_point = telemetry[telemetry['Distance'] >= s1_distance].iloc[0]
                s2_point = telemetry[telemetry['Distance'] >= s2_distance].iloc[0]
                ax.scatter(s1_point['X'], s1_point['Y'], color='green', s=80, label='S1')
                ax.text(s1_point['X'], s1_point['Y'], 'S1', color='green', weight='bold')
                ax.scatter(s2_point['X'], s2_point['Y'], color='orange', s=80, label='S2')
                ax.text(s2_point['X'], s2_point['Y'], 'S2', color='orange', weight='bold')
            except Exception as e:
                st.warning(f"Could not plot sector markers: {e}")
        ax.set_title(f"{gp_name.title()} Circuit Layout ({season})")
        ax.axis('off')
        st.pyplot(fig)
    except Exception as e:
        st.error(f"❌ Failed to load circuit layout for {gp_name} {season}: {e}")


st.set_page_config(page_title="🏁 RacingLineAI v8.0", layout="wide", initial_sidebar_state="expanded")

TEAM_COLORS = {
    'Red Bull Racing': '#1E41FF', 'Ferrari': '#DC0000', 'Mercedes': '#00D2BE',
    'McLaren': '#FF8700', 'Aston Martin': '#006F62', 'Alpine': '#0090FF',
    'AlphaTauri': '#2B4562', 'Alfa Romeo': '#900000', 'Williams': '#005AFF',
    'Haas F1 Team': '#B6BABD', 'Other': '#AAAAAA'
}

@st.cache_data

def load_data():
    path_2023 = os.path.join("data", "processed", "all_races_combined_2023.csv")
    path_2024 = os.path.join("data", "processed", "all_races_combined_2024.csv")
    df_2023 = pd.read_csv(path_2023)
    df_2023["SeasonYear"] = 2023
    df_2024 = pd.read_csv(path_2024)
    df_2024["SeasonYear"] = 2024
    df = pd.concat([df_2023, df_2024], ignore_index=True)
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

df, driver_colors = load_data()

st.sidebar.title("🏎️ RacingLineAI Filters")

# --- Smart season & GP filtering ---
seasons = sorted(df["SeasonYear"].unique())
selected_season = st.sidebar.selectbox("Season", ["All"] + list(map(str, seasons)))

gps = sorted(df["GrandPrix"].unique())
selected_gp = st.sidebar.selectbox("Grand Prix", ["All"] + gps)

# --- Dynamically filter drivers who raced in selected Season + GP ---
driver_pool_df = df.copy()
if selected_season != "All":
    driver_pool_df = driver_pool_df[driver_pool_df["SeasonYear"] == int(selected_season)]
if selected_gp != "All":
    driver_pool_df = driver_pool_df[driver_pool_df["GrandPrix"] == selected_gp]

available_drivers = sorted(driver_pool_df["Driver"].unique())

# Set default drivers dynamically if VER or LEC are in the filtered list
default_driver_set = [d for d in ["VER", "LEC"] if d in available_drivers]
selected_drivers = st.sidebar.multiselect(
    "Drivers", options=available_drivers, default=default_driver_set or available_drivers[:2]
)
# Filter data early to allow proper driver/compound lists
temp_df = df.copy()
if selected_season != "All":
    temp_df = temp_df[temp_df["SeasonYear"] == int(selected_season)]
if selected_gp != "All":
    temp_df = temp_df[temp_df["GrandPrix"] == selected_gp]

# --- Compound dropdowns mapped to user-friendly labels --

# --- 1. Define compound maps ---
compound_map = {
    'SOFT': 'Soft', 'MEDIUM': 'Medium', 'HARD': 'Hard',
    'INTERMEDIATE': 'Intermediate', 'WET': 'Wet'
}
reverse_map = {v: k for k, v in compound_map.items()}
# --- 2. Filter early for season + GP ---
temp_df = df.copy()
if selected_season != "All":
    temp_df = temp_df[temp_df["SeasonYear"] == int(selected_season)]
if selected_gp != "All":
    temp_df = temp_df[temp_df["GrandPrix"] == selected_gp]
# --- 3. Extract only available compounds in current selection ---
used_compounds = sorted(temp_df["Compound"].dropna().unique())
compound_ui_options = [reverse_map.get(c, c.upper()) for c in used_compounds if c in reverse_map]
# --- 4. UI for compound filter (based on filtered options) ---
selected_compound_ui = st.sidebar.multiselect(
    "Tyre Compounds", options=compound_ui_options, default=compound_ui_options
)
# --- 5. Final compound values in actual dataset form ---
selected_compounds = [compound_map.get(c, c.title()) for c in selected_compound_ui]
# --- 6. Final filtered dataframe ---
filtered_df = temp_df[
    (temp_df["Driver"].isin(selected_drivers)) &
    (temp_df["Compound"].isin(selected_compounds))
]
# --- Safe exit on empty ---
if filtered_df.empty:
    st.warning("⚠️ No data found for this combination. Try adjusting the filters.")
    st.stop()

# --- 🗺️ Dynamic Circuit Layout from Telemetry ---
st.subheader("🗺️ Circuit Layout (Telemetry-Based)")

if selected_gp != "All" and selected_season != "All":
    season_val = int(selected_season)
    gp_val = selected_gp.replace("_", " ").title()
    # 🗺️ Circuit Layout Plot
    plot_circuit_map(season_val, gp_val)
    
    # # 📍 Circuit Metadata Panel
    # try:
    #     metadata_session = get_session(season_val, gp_val, 'R')  # ✅ Reusing proper formatting
    #     metadata_session.load()
    #     track = metadata_session.track
    #     if track is None:
    #         raise ValueError("Track data not available")

    #     with st.expander("📍 Circuit Info", expanded=True):
    #         st.markdown(f"""
    #             **Name:** {track.get('Name', 'Unknown')}  
    #             **Location:** {track.get('Location', 'Unknown')}, {track.get('Country', 'Unknown')}  
    #             **Length:** {track.get('Length', 0) / 1000:.2f} km  
    #             **Altitude:** {track.get('Altitude', 'N/A')} m  
    #         """)
    # except Exception as e:
    #     st.warning("⚠️ Circuit metadata not available.")
else:
    st.info("🎯 Select both a Season and a Grand Prix to view the circuit layout and info.")

st.title("🏁 RacingLineAI v8.0 - AI Insights + Strategy Intelligence")

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


# Get available drivers just for the simulator dropdown
sim_available_drivers = sorted(temp_df["Driver"].dropna().unique())

st.sidebar.markdown("🧪 **Strategy Simulator**")
sim_driver = st.sidebar.selectbox("Simulate for Driver", sim_available_drivers)
sim_compound = st.sidebar.selectbox("Compound", used_compounds)
sim_temp = st.sidebar.slider("Track Temp (°C)", 15, 45, 30)
sim_stint = st.sidebar.slider("Stint Length (laps)", 5, 30, 15)

sim_df = temp_df[
    (temp_df["Compound"] == sim_compound) &
    (temp_df["TrackTemp"].between(sim_temp - 2, sim_temp + 2))
]

if sim_df.empty:
    st.warning("🚫 Not enough matching data for simulation (tyre + temp).")
else:
    fit = sim_df.groupby("TyreLife")["LapTimeSeconds"].mean().reset_index()
    fig = px.line(fit[fit["TyreLife"] <= sim_stint], x="TyreLife", y="LapTimeSeconds", title=f"{sim_compound} Degradation at ~{sim_temp}°C")
    st.subheader("📊 Simulated Tyre Stint Projection")
    st.plotly_chart(fig, use_container_width=True)


# --- Driver Gap Chart ---
st.header("📉 Driver Gap to Leader (per lap)")
gap_df = filtered_df.copy()
gap_df["LeaderLap"] = gap_df.groupby("LapNumber")["LapTimeSeconds"].transform("min")
gap_df["GapToLeader"] = gap_df["LapTimeSeconds"] - gap_df["LeaderLap"]

if not gap_df.empty:
    fig = px.line(
        gap_df,
        x="LapNumber",
        y="GapToLeader",
        color="Driver_Season",
        template="plotly_dark",
        color_discrete_map=driver_colors
    )
    fig.update_layout(yaxis_title="Gap to Leader (s)")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No gap data available for selected filters.")

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

# --- SC/VSC/Red Flag Overlay Helper ---
def add_flag_regions(fig, df):
    for flag, color, label in [("IsSC", "grey", "SC"), ("IsVSC", "orange", "VSC"), ("IsRedFlag", "red", "Red Flag")]:
        if df[flag].any():
            for lap in df[df[flag]]["LapNumber"].unique():
                fig.add_vrect(
                    x0=lap - 0.5, x1=lap + 0.5,
                    fillcolor=color, opacity=0.3, line_width=0,
                    annotation_text=label, annotation_position="top left"
                )
    return fig

# Example usage:
st.header("📈 Lap Time Evolution with Flags")
fig = px.line(filtered_df, x="LapNumber", y="LapTimeSeconds", color="Driver_Season",
            line_group="Stint", hover_data=["TyreLife", "Compound"],
            template="plotly_dark", color_discrete_map=driver_colors)
fig = add_flag_regions(fig, filtered_df)
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
