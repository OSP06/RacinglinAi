# Full Streamlit file with all visual, weather, and predictive analysis included

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import matplotlib.pyplot as plt
from fastf1 import get_session
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import MinMaxScaler
import torch
import torch.nn as nn

# ---------------------- Config & Load ----------------------
st.set_page_config("RacingLineAI v8.3", layout="wide")

TEAM_COLORS = {
    'Red Bull Racing': '#1E41FF', 'Ferrari': '#DC0000', 'Mercedes': '#00D2BE',
    'McLaren': '#FF8700', 'Aston Martin': '#006F62', 'Alpine': '#0090FF',
    'AlphaTauri': '#2B4562', 'Alfa Romeo': '#900000', 'Williams': '#005AFF',
    'Haas F1 Team': '#B6BABD', 'Other': '#AAAAAA'
}

@st.cache_data
def load_data():
    all_dfs = []
    for year in range(2021, 2026):
        df = pd.read_csv(f"data/processed/all_races_combined_{year}.csv")
        df["SeasonYear"] = year
        all_dfs.append(df)
    df = pd.concat(all_dfs, ignore_index=True)
    df = df.dropna(subset=["LapTimeSeconds", "TyreLife", "Compound"])
    df["Team"] = df["Team"].fillna("Other")
    df["TeamColor"] = df["Team"].map(TEAM_COLORS).fillna(TEAM_COLORS["Other"])
    # Dynamically map driver colors per season
    driver_team_map = df.drop_duplicates(["Driver", "SeasonYear"])[["Driver", "SeasonYear", "Team"]]
    driver_team_map["Driver_Season"] = driver_team_map["Driver"] + " (" + driver_team_map["SeasonYear"].astype(str) + ")"
    driver_team_map["Color"] = driver_team_map["Team"].map(TEAM_COLORS).fillna(TEAM_COLORS["Other"])
    driver_colors = dict(zip(driver_team_map["Driver_Season"], driver_team_map["Color"]))

    df["Driver_Season"] = df["Driver"] + " (" + df["SeasonYear"].astype(str) + ")"
    df["DriverColor"] = df["Driver_Season"].map(driver_colors)
    df["BestSector"] = df[["Sector1TimeSeconds", "Sector2TimeSeconds", "Sector3TimeSeconds"]].idxmin(axis=1).str.extract(r'(\d)').astype(float).fillna(0).astype(int)
    df["IsDNF"] = df.groupby("Driver")["LapNumber"].transform('max') < df["LapNumber"].max() - 3
    df["DeltaToFastestLap"] = df.groupby("Driver")["LapTimeSeconds"].transform(lambda x: x - x.min())
    return df, driver_colors

df, driver_colors = load_data()

# ---------------------- Sidebar Filters ----------------------
st.sidebar.title("🏎️ RacingLineAI Filters")
seasons = sorted(df["SeasonYear"].unique())
selected_season = st.sidebar.selectbox("Season", ["All"] + list(map(str, seasons)))

gp_options = sorted(df[df["SeasonYear"] == int(selected_season)]["GrandPrix"].unique()) if selected_season != "All" else sorted(df["GrandPrix"].unique())
selected_gp = st.sidebar.selectbox("Grand Prix", ["All"] + gp_options)

def get_filtered_df(df, season, gp):
    if season != "All": df = df[df["SeasonYear"] == int(season)]
    if gp != "All": df = df[df["GrandPrix"] == gp]
    return df

driver_pool = get_filtered_df(df, selected_season, selected_gp)
available_drivers = sorted(driver_pool["Driver"].unique())
defaults = [d for d in ["VER", "LEC"] if d in available_drivers]
selected_drivers = st.sidebar.multiselect("Drivers", available_drivers, default=defaults or available_drivers[:2])

compound_map = {'SOFT': 'Soft', 'MEDIUM': 'Medium', 'HARD': 'Hard', 'INTERMEDIATE': 'Intermediate', 'WET': 'Wet'}
reverse_map = {v: k for k, v in compound_map.items()}
temp_df = get_filtered_df(df, selected_season, selected_gp)
used_compounds = sorted(temp_df["Compound"].dropna().unique())
compound_ui = [reverse_map.get(c, c.upper()) for c in used_compounds if c in reverse_map]
selected_compounds = st.sidebar.multiselect("Tyre Compounds", compound_ui, default=compound_ui)
final_compounds = [compound_map.get(c, c.title()) for c in selected_compounds]

filtered_df = temp_df[temp_df["Driver"].isin(selected_drivers) & temp_df["Compound"].isin(final_compounds)]
if filtered_df.empty:
    st.warning("⚠️ No data found. Adjust your filters.")
    st.stop()

# ---------------------- Circuit Layout ----------------------
def plot_circuit_map(season: int, gp: str):
    try:
        session = get_session(season, gp, 'R')
        session.load(telemetry=True, laps=True)
        lap = session.laps.pick_fastest()
        tel = lap.get_telemetry()
        fig, ax = plt.subplots(figsize=(6, 5))
        ax.plot(tel['X'], tel['Y'], color='blue')
        ax.axis('off')
        st.pyplot(fig)
    except Exception as e:
        st.error(f"Could not load circuit layout: {e}")

st.subheader("🗺️ Circuit Layout")
if selected_season != "All" and selected_gp != "All":
    plot_circuit_map(int(selected_season), selected_gp)

st.title("🏁 RacingLineAI v8.3: Full Analysis & AI Forecasts")

# ---------------------- Visual Analysis ----------------------
st.header("📊 Race Pace Summary")
summary = filtered_df.groupby("Driver").agg(
    AvgLap=("LapTimeSeconds", "mean"),
    FastestLap=("LapTimeSeconds", "min"),
    PitCount=("PitLap", lambda x: x.notna().sum())
).reset_index()
st.dataframe(summary.round(2))

with st.expander("📉 Driver Gap to Leader"):
    gap_df = filtered_df.copy()
    gap_df["LeaderLap"] = gap_df.groupby("LapNumber")["LapTimeSeconds"].transform("min")
    gap_df["GapToLeader"] = gap_df["LapTimeSeconds"] - gap_df["LeaderLap"]
    fig = px.line(gap_df, x="LapNumber", y="GapToLeader", color="Driver_Season",
            template="plotly_dark", color_discrete_map=driver_colors)
    st.plotly_chart(fig, use_container_width=True)

with st.expander("📉 Grip Degradation (Driver-Colored)"):
    slope_df = filtered_df.dropna(subset=["TrackTemp"])
    grouped = slope_df.groupby(["Driver_Season", "TyreLife"]).LapTimeSeconds.mean().reset_index()
    fig = px.line(grouped, x="TyreLife", y="LapTimeSeconds", color="Driver_Season",
                template="plotly_dark", color_discrete_map=driver_colors)
    st.plotly_chart(fig, use_container_width=True)

with st.expander("📊 Sector Dominance per Driver (Team Colors)"):
    sector_pref = filtered_df.groupby(["Driver", "BestSector"]).size().reset_index(name="Count")
    sector_pref["BestSector"] = sector_pref["BestSector"].map({1: "S1", 2: "S2", 3: "S3"})

    # Get team for each driver
    driver_teams = filtered_df.drop_duplicates("Driver")[["Driver", "Team"]].set_index("Driver")["Team"].to_dict()
    sector_pref["Team"] = sector_pref["Driver"].map(driver_teams)
    sector_pref["Color"] = sector_pref["Team"].map(TEAM_COLORS).fillna(TEAM_COLORS["Other"])
    fig = go.Figure()
    for sector in ["S1", "S2", "S3"]:
        data = sector_pref[sector_pref["BestSector"] == sector]
        fig.add_trace(go.Bar(
            x=data["Driver"],
            y=data["Count"],
            name=sector,
            marker_color=data["Color"]
        ))
    fig.update_layout(
        barmode="stack",
        template="plotly_dark",
        title="Best Sector Count per Driver (Colored by Team)",
        xaxis_title="Driver",
        yaxis_title="Best Sector Count"
    )
    st.plotly_chart(fig, use_container_width=True)

with st.expander("🏋️ DNF Drivers"):
    dnf_summary = filtered_df[filtered_df["IsDNF"]].groupby("Driver").size().reset_index(name="DNF Count")
    if not dnf_summary.empty:
        st.dataframe(dnf_summary, use_container_width=True)
    else:
        st.info("🔍 No DNF drivers in current selection.")

with st.expander("🔢 Delta to Fastest Lap"):
    fig = px.line(filtered_df, x="LapNumber", y="DeltaToFastestLap", color="Driver_Season",
            template="plotly_dark", color_discrete_map=driver_colors)
    fig.update_layout(title="Delta to Fastest Lap Over Race")
    st.plotly_chart(fig, use_container_width=True)

with st.expander("🛋️ Stint Type Pace (Team Colors)"):
    if "Stint" in filtered_df.columns:
        stint_max = filtered_df.groupby("Driver")["Stint"].transform("max")
        filtered_df["StintType"] = np.where(filtered_df["Stint"] == 1, "Opening",
                                            np.where(filtered_df["Stint"] == stint_max, "Closing", "Mid"))
        fig = px.box(filtered_df, x="StintType", y="LapTimeSeconds", color="Driver_Season",
                    template="plotly_dark", color_discrete_map=driver_colors)
        fig.update_layout(title="Lap Time Distribution by Stint Type")
        st.plotly_chart(fig, use_container_width=True)

# ---------------------- Predictive Intelligence ----------------------
st.header("🧠 Predictive Intelligence")
model_option = st.selectbox("Choose Forecasting Model", ["LSTM Tyre Forecast", "Lap Time Regressor", "Strategy Predictor"])

if model_option == "LSTM Tyre Forecast":
    sel_driver = st.selectbox("Driver", sorted(filtered_df["Driver_Season"].unique()))
    sel_comp = st.selectbox("Compound", sorted(filtered_df["Compound"].unique()))
    df_model = filtered_df[(filtered_df["Driver_Season"] == sel_driver) & (filtered_df["Compound"] == sel_comp)]
    if df_model.shape[0] > 20:
        series = df_model.sort_values("TyreLife")["LapTimeSeconds"].values.reshape(-1, 1)
        scaler = MinMaxScaler(); scaled = scaler.fit_transform(series)
        window = 5; X, y = [], []
        for i in range(len(scaled) - window):
            X.append(scaled[i:i+window]); y.append(scaled[i+window])
        X = torch.tensor(X).float(); y = torch.tensor(y).float()
        class LSTMModel(nn.Module):
            def __init__(self):
                super().__init__()
                self.lstm = nn.LSTM(input_size=1, hidden_size=64, batch_first=True)
                self.fc = nn.Linear(64, 1)
            def forward(self, x):
                x, _ = self.lstm(x)
                return self.fc(x[:, -1, :])
        model = LSTMModel(); loss_fn = nn.MSELoss(); optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
        for _ in range(20):
            optimizer.zero_grad()
            output = model(X).squeeze()
            loss = loss_fn(output, y.squeeze())
            loss.backward(); optimizer.step()
        preds = []
        last_seq = scaled[-window:]
        for _ in range(15):
            input_tensor = torch.tensor(last_seq).float().unsqueeze(0)
            pred = model(input_tensor).detach().numpy()[0][0]
            preds.append(pred)
            last_seq = np.vstack([last_seq[1:], [[pred]]])
        pred_values = scaler.inverse_transform(np.array(preds).reshape(-1, 1)).flatten()
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_model["TyreLife"], y=df_model["LapTimeSeconds"], name="Actual"))
        future_laps = list(range(int(df_model["TyreLife"].max()) + 1, int(df_model["TyreLife"].max()) + 1 + len(preds)))
        fig.add_trace(go.Scatter(x=future_laps, y=pred_values, name="Forecast", line=dict(dash="dot")))
        st.plotly_chart(fig, use_container_width=True)

elif model_option == "Lap Time Regressor":
    df_reg = filtered_df.dropna(subset=["TrackTemp"])
    df_reg["CompoundCode"] = df_reg["Compound"].astype("category").cat.codes
    X = df_reg[["TrackTemp", "TyreLife", "CompoundCode"]]; y = df_reg["LapTimeSeconds"]
    model = LinearRegression().fit(X, y)
    preds = model.predict(X)
    fig = px.scatter(x=y, y=preds, labels={"x": "Actual LapTime", "y": "Predicted"}, title="Lap Time Regression")
    st.plotly_chart(fig, use_container_width=True)

elif model_option == "Strategy Predictor":
    st.markdown("Based on historical stints, this predicts optimal tyre change window.")
    stint_df = filtered_df.groupby(["Compound", "Stint"]).agg(
        AvgLap=("LapTimeSeconds", "mean"), StintLen=("TyreLife", "max")
    ).reset_index()
    fig = px.box(stint_df, x="Compound", y="StintLen", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.caption("🔧 RacingLineAI v8.3 | Built by Om Patel | Powered by PyTorch & FastF1")
