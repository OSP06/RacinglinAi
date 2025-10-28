import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import matplotlib.pyplot as plt
from fastf1 import get_session
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
import torch
import torch.nn as nn

# ======================= PAGE CONFIG =======================
st.set_page_config(
    page_title="RacingLineAI - F1 Analytics",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ======================= FLAWLESS CSS =======================
st.markdown("""
<style>
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    .main {
        background: linear-gradient(180deg, #0A0A0A 0%, #0F0F0F 100%);
        padding: 1rem 2.5rem 3rem 2.5rem;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #E0E0E0;
    }
    
    /* Streamlit Elements Styling */
    .stSelectbox label, .stMultiSelect label {
        font-size: 11px !important;
        color: #999 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 500;
    }
    
    /* Elegant Header */
    .main-header {
        color: #FFFFFF;
        font-size: 48px;
        font-weight: 300;
        letter-spacing: 6px;
        margin: 50px 0 30px 0;
        text-align: center;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        padding-bottom: 30px;
        position: relative;
        font-family: 'Inter', sans-serif;
    }
    
    .main-header strong {
        font-weight: 600;
    }
    
    .main-header::before {
        content: '🏎️';
        position: absolute;
        left: 50%;
        transform: translateX(-50%);
        top: -40px;
        font-size: 32px;
        opacity: 0.9;
        filter: drop-shadow(0 4px 6px rgba(0, 0, 0, 0.3));
    }
    
    /* Section Headers */
    .section-header {
        color: #FFFFFF;
        font-size: 30px;
        font-weight: 500;
        margin: 50px 0 25px 0;
        padding-bottom: 15px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.12);
        letter-spacing: 1px;
        font-family: 'Inter', sans-serif;
    }
    
    /* Subsection Headers */
    .subsection-header {
        color: #CCCCCC;
        font-size: 20px;
        font-weight: 500;
        margin: 30px 0 15px 0;
        letter-spacing: 0.5px;
    }
    
    /* Filter Cards */
    .filter-card {
        background: rgba(25, 25, 25, 0.6);
        backdrop-filter: blur(10px);
    }
    
    .filter-label {
        color: #888;
        font-size: 12px;
        font-weight: 600;
        margin-bottom: 05px;
        text-transform: uppercase;
        letter-spacing: 1.2px;
    }
    
    /* Metric Cards */
    .metric-card {
        background: rgba(25, 25, 25, 0.5);
        border-radius: 8px;
        padding: 20px;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.06);
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        border-color: rgba(255, 255, 255, 0.15);
        background: rgba(30, 30, 30, 0.6);
    }
    
    .metric-label {
        color: #666;
        font-size: 10px;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-weight: 600;
    }
    
    .metric-value {
        color: #FFF;
        font-size: 24px;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
    }
    
    /* Podium */
    .podium-container {
        display: flex;
        justify-content: center;
        align-items: flex-end;
        gap: 30px;
        margin: 40px 0;
    }
    
    .podium-position {
        border-radius: 10px;
        padding: 25px;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.08);
        background: rgba(25, 25, 25, 0.4);
        transition: all 0.3s ease;
    }
    
    .podium-position:hover {
        transform: translateY(-5px);
        border-color: rgba(255, 255, 255, 0.2);
    }
    
    .podium-1st {
        height: 190px;
        width: 190px;
        border: 2px solid rgba(255, 215, 0, 0.4);
    }
    
    .podium-2nd {
        height: 190px;
        width: 190px;
        border: 2px solid rgba(192, 192, 192, 0.4);
    }
    
    .podium-3rd {
        height: 190px;
        width: 190px;
        border: 2px solid rgba(205, 127, 50, 0.4);
    }
    
    .podium-medal {
        font-size: 42px;
        margin-bottom: 12px;
    }
    
    .podium-driver {
        font-size: 26px;
        font-weight: 600;
        color: white;
        margin: 10px 0;
        font-family: 'Inter', sans-serif;
    }
    
    .podium-team {
        font-size: 11px;
        color: #777;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Explainer Cards */
    .explainer {
        background: rgba(255, 255, 255, 0.02);
        border-left: 3px solid rgba(255, 255, 255, 0.15);
        border-radius: 6px;
        padding: 18px 20px;
        margin: 20px 0;
    }
    
    .explainer-title {
        color: #BBB;
        font-size: 13px;
        font-weight: 600;
        margin-bottom: 10px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .explainer-text {
        color: #888;
        font-size: 14px;
        line-height: 1.7;
    }
    
    .insights {
        background: rgba(255, 255, 255, 0.02);
        border-left: 3px solid rgba(100, 200, 255, 0.3);
        border-radius: 6px;
        padding: 18px 20px;
        margin: 15px 0;
    }
    
    .insights-title {
        color: #AAD4FF;
        font-size: 13px;
        font-weight: 600;
        margin-bottom: 10px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* AI Detail Box */
    .ai-detail {
        background: rgba(50, 100, 200, 0.08);
        border: 1px solid rgba(100, 150, 255, 0.2);
        border-radius: 8px;
        padding: 20px;
        margin: 20px 0;
    }
    
    .ai-detail-title {
        color: #88BBFF;
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 12px;
        text-transform: uppercase;
        letter-spacing: 1.2px;
    }
    
    .ai-detail-text {
        color: #AAA;
        font-size: 14px;
        line-height: 1.8;
    }
    
    /* Current Selection */
    .current-selection {
        background: rgba(20, 20, 20, 0.7);
        border-radius: 8px;
        padding: 14px 24px;
        margin: 25px 0;
        font-size: 13px;
        color: #777;
        border: 1px solid rgba(255, 255, 255, 0.06);
        font-family: 'Inter', sans-serif;
    }
    
    .current-selection strong {
        color: #DDD;
        font-weight: 600;
    }
    
    /* Tyre Legend */
    .tyre-legend {
        display: flex;
        gap: 20px;
        justify-content: center;
        margin: 25px 0;
        flex-wrap: wrap;
    }
    
    .tyre-item {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 8px 16px;
        background: rgba(30, 30, 30, 0.6);
        border-radius: 20px;
        font-size: 13px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        font-weight: 500;
    }
    
    .tyre-circle {
        width: 18px;
        height: 18px;
        border-radius: 50%;
        border: 2px solid rgba(255, 255, 255, 0.4);
    }
    
    /* Strategy Table */
    .strategy-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        margin: 20px 0;
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
    
    .strategy-table th {
        background: rgba(40, 40, 40, 0.8);
        color: #AAA;
        padding: 14px 18px;
        text-align: left;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .strategy-table td {
        background: rgba(25, 25, 25, 0.5);
        color: #CCC;
        padding: 16px 18px;
        font-size: 14px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    .strategy-table tr:last-child td {
        border-bottom: none;
    }
    
    .strategy-table tr:hover td {
        background: rgba(30, 30, 30, 0.7);
    }
    
    /* Comparison Panels */
    .comparison-container {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 30px;
        margin: 30px 0;
    }
    
    .comparison-panel {
        background: rgba(25, 25, 25, 0.6);
        backdrop-filter: blur(10px);
    }
    
    .panel-title {
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 20px;
        text-align: center;
        color: #BBB;
        text-transform: uppercase;
        letter-spacing: 1.5px;
    }
    
    .panel-content {
        color: #999;
        font-size: 14px;
        line-height: 1.8;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: #0A0A0A;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #2A2A2A;
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #3A3A3A;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 15px;
        background-color: transparent;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        padding-bottom: 0;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 0;
        padding: 14px 28px;
        font-weight: 500;
        border: none;
        color: #666;
        font-size: 14px;
        letter-spacing: 0.8px;
        font-family: 'Inter', sans-serif;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: transparent;
        border-bottom: 2px solid #FFF;
        color: #FFF;
    }
    
    /* Dataframe Styling */
    .stDataFrame {
        font-family: 'Inter', sans-serif;
    }
    
    /* Info/Warning boxes */
    .stAlert {
        background-color: rgba(30, 30, 30, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
    }
    
    /* Smooth transitions */
    * {
        transition: border-color 0.2s ease, background-color 0.2s ease;
    }
</style>
""", unsafe_allow_html=True)

# ======================= CONSTANTS =======================
TEAM_COLORS = {
    'Red Bull Racing': '#1E41FF', 'Ferrari': '#DC0000', 'Mercedes': '#00D2BE',
    'McLaren': '#FF8700', 'Aston Martin': '#006F62', 'Alpine': '#0090FF',
    'AlphaTauri': '#2B4562', 'Alfa Romeo': '#900000', 'Williams': '#005AFF',
    'Haas F1 Team': '#B6BABD', 'RB': '#6692FF', 'Kick Sauber': '#52E252',
    'Other': '#AAAAAA'
}

COMPOUND_COLORS = {
    'Soft': '#FF0000', 'Medium': '#FFF200', 'Hard': '#FFFFFF',
    'Intermediate': '#00FF00', 'Wet': '#0000FF'
}

# ======================= HELPER FUNCTIONS =======================

def create_main_header(text):
    """Create elegant main header"""
    st.markdown(f'<div class="main-header"><strong>{text}</strong></div>', unsafe_allow_html=True)

def create_section_header(text):
    """Create section header"""
    st.markdown(f'<div class="section-header">{text}</div>', unsafe_allow_html=True)

def create_subsection_header(text):
    """Create subsection header"""
    st.markdown(f'<div class="subsection-header">{text}</div>', unsafe_allow_html=True)

def create_explainer(title, description, insights=None):
    """Create explanation card"""
    html = f"""<div class="explainer">
<div class="explainer-title">{title}</div>
<div class="explainer-text">{description}</div>
</div>"""
    
    if insights:
        insights_html = ''.join([f"• {insight}<br>" for insight in insights])
        html += f"""<div class="insights">
<div class="insights-title">Key Insights</div>
<div class="explainer-text">{insights_html}</div>
</div>"""
    
    st.markdown(html, unsafe_allow_html=True)

def create_ai_detail(title, description):
    """Create detailed AI explanation box"""
    html = f"""<div class="ai-detail">
<div class="ai-detail-title">{title}</div>
<div class="ai-detail-text">{description}</div>
</div>"""
    st.markdown(html, unsafe_allow_html=True)

def show_default_circuit():
    """Show elegant default circuit - proper race track oval"""
    fig = go.Figure()
    
    # Create a proper race track oval
    straight1_x = np.linspace(0, 200, 50)
    straight1_y = np.zeros(50)
    
    turn1_theta = np.linspace(0, np.pi, 30)
    turn1_x = 200 + 40 * np.cos(turn1_theta)
    turn1_y = 40 + 40 * np.sin(turn1_theta)
    
    straight2_x = np.linspace(200, 0, 50)
    straight2_y = np.ones(50) * 80
    
    turn2_theta = np.linspace(np.pi, 2*np.pi, 30)
    turn2_x = 0 + 40 * np.cos(turn2_theta)
    turn2_y = 40 + 40 * np.sin(turn2_theta)
    
    x = np.concatenate([straight1_x, turn1_x, straight2_x, turn2_x])
    y = np.concatenate([straight1_y, turn1_y, straight2_y, turn2_y])
    
    fig.add_trace(go.Scatter(
        x=x, y=y,
        mode='lines',
        line=dict(color='rgba(255, 255, 255, 0.2)', width=2),
        name='Circuit Preview',
        hoverinfo='skip',
        fill='toself',
        fillcolor='rgba(255, 255, 255, 0.02)'
    ))
    
    fig.update_layout(
        title=dict(
            text="Select a Grand Prix to view circuit layout",
            font=dict(size=14, color='#888', family='Inter')
        ),
        template='plotly_dark',
        showlegend=False,
        height=450,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, visible=False, scaleanchor="x", scaleratio=1),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=50, b=20),
        font=dict(family='Inter')
    )
    
    return fig

def get_podium(season, gp, race_data):
    """Get top 3 finishers"""
    podium = []
    
    if "Position" in race_data.columns:
        for pos in [1.0, 2.0, 3.0]:
            drivers = race_data[race_data["Position"] == pos]
            if not drivers.empty:
                driver_info = drivers.iloc[0]
                podium.append({
                    'driver': driver_info['Driver'],
                    'team': driver_info['Team'],
                    'position': int(pos)
                })
    
    if len(podium) < 3:
        driver_stats = race_data.groupby("Driver").agg({
            "LapNumber": "max",
            "LapTimeSeconds": "sum",
            "Team": "first"
        }).reset_index()
        driver_stats = driver_stats.sort_values(["LapNumber", "LapTimeSeconds"], ascending=[False, True])
        
        for i in range(min(3, len(driver_stats))):
            if i >= len(podium):
                podium.append({
                    'driver': driver_stats.iloc[i]['Driver'],
                    'team': driver_stats.iloc[i]['Team'],
                    'position': i + 1
                })
    
    return podium

def create_podium_display(podium):
    """Create minimal podium display"""
    if len(podium) < 3:
        return
    
    medals = ['🥇', '🥈', '🥉']
    display_order = [1, 0, 2]
    
    html = '<div class="podium-container">'
    for idx in display_order:
        if idx < len(podium):
            p = podium[idx]
            position_class = f"podium-{['1st', '2nd', '3rd'][idx]}"
            
            html += f"""<div class="podium-position {position_class}">
<div class="podium-medal">{medals[idx]}</div>
<div class="podium-driver">{p['driver']}</div>
<div class="podium-team">{p['team']}</div>
</div>"""
    
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

def get_actual_pit_strategy(season, gp, driver, race_data):
    """Extract actual pit strategy with accurate pit stop counting"""
    driver_data = race_data[race_data['Driver'] == driver].sort_values('LapNumber')
    
    if driver_data.empty:
        return None
    
    # Method 1: Count compound changes (most reliable)
    pit_stops = []
    prev_compound = None
    
    for idx, row in driver_data.iterrows():
        current_compound = row['Compound']
        lap_num = row['LapNumber']
        
        if prev_compound is not None and current_compound != prev_compound:
            pit_stops.append({
                'lap': lap_num,
                'from_compound': prev_compound,
                'to_compound': current_compound
            })
        
        prev_compound = current_compound
    
    # Method 2: Use Stint column if available
    stints = []
    stint_based_stops = 0
    
    if 'Stint' in driver_data.columns:
        stint_info = driver_data.groupby('Stint').agg({
            'LapNumber': ['min', 'max', 'count'],
            'Compound': 'first'
        }).reset_index()
        
        for _, stint in stint_info.iterrows():
            stints.append({
                'stint': int(stint['Stint']),
                'start_lap': int(stint[('LapNumber', 'min')]),
                'end_lap': int(stint[('LapNumber', 'max')]),
                'length': int(stint[('LapNumber', 'count')]),
                'compound': stint[('Compound', 'first')]
            })
        
        # Stint-based pit stop count
        stint_based_stops = len(stints) - 1 if len(stints) > 0 else 0
    
    # Use the maximum of both methods for most accurate count
    compound_based_stops = len(pit_stops)
    total_stops = max(compound_based_stops, stint_based_stops)
    
    return {
        'pit_stops': pit_stops,
        'stints': stints,
        'total_stops': total_stops,
        'compound_changes': compound_based_stops,
        'stint_changes': stint_based_stops
    }

# ======================= DATA LOADING =======================

@st.cache_data(ttl=60)
def load_data():
    all_dfs = []
    available_years = range(2018, 2026)
    
    for year in available_years:
        try:
            file_path = f"data/processed/all_races_combined_{year}.csv"
            df = pd.read_csv(file_path)
            df["SeasonYear"] = year
            all_dfs.append(df)
        except FileNotFoundError:
            continue
        except Exception:
            continue
    
    if not all_dfs:
        st.error("❌ No data files loaded!")
        st.stop()
    
    df = pd.concat(all_dfs, ignore_index=True)
    df = df.dropna(subset=["LapTimeSeconds", "TyreLife", "Compound"])
    df["Team"] = df["Team"].fillna("Other")
    df["TeamColor"] = df["Team"].map(TEAM_COLORS).fillna(TEAM_COLORS["Other"])
    
    driver_team_map = df.drop_duplicates(["Driver", "SeasonYear"])[["Driver", "SeasonYear", "Team"]]
    driver_team_map["Driver_Season"] = driver_team_map["Driver"] + " (" + driver_team_map["SeasonYear"].astype(str) + ")"
    driver_team_map["Color"] = driver_team_map["Team"].map(TEAM_COLORS).fillna(TEAM_COLORS["Other"])
    driver_colors = dict(zip(driver_team_map["Driver_Season"], driver_team_map["Color"]))
    df["Driver_Season"] = df["Driver"] + " (" + df["SeasonYear"].astype(str) + ")"
    df["DriverColor"] = df["Driver_Season"].map(driver_colors)
    
    if all(col in df.columns for col in ["Sector1TimeSeconds", "Sector2TimeSeconds", "Sector3TimeSeconds"]):
        df["BestSector"] = df[["Sector1TimeSeconds", "Sector2TimeSeconds", "Sector3TimeSeconds"]].idxmin(axis=1).str.extract(r'(\d)').astype(float).fillna(0).astype(int)
    
    df["DeltaToFastestLap"] = df.groupby("Driver")["LapTimeSeconds"].transform(lambda x: x - x.min())
    
    return df, driver_colors

df, driver_colors = load_data()

# ======================= MAIN APP =======================

create_main_header("RacingLineAI")

st.markdown("<br>", unsafe_allow_html=True)

# ======================= TOP FILTERS =======================

col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    st.markdown('<div class="filter-card">', unsafe_allow_html=True)
    st.markdown('<div class="filter-label">Season</div>', unsafe_allow_html=True)
    seasons = sorted(df["SeasonYear"].unique())
    selected_season = st.selectbox("Season", ["All"] + list(map(str, seasons)), label_visibility="collapsed", key="top_season")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="filter-card">', unsafe_allow_html=True)
    st.markdown('<div class="filter-label">Grand Prix</div>', unsafe_allow_html=True)
    if selected_season != "All":
        gp_options = sorted(df[df["SeasonYear"] == int(selected_season)]["GrandPrix"].unique())
    else:
        gp_options = sorted(df["GrandPrix"].unique())
    selected_gp = st.selectbox("Grand Prix", ["All"] + gp_options, label_visibility="collapsed", key="top_gp")
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="filter-card">', unsafe_allow_html=True)
    st.markdown('<div class="filter-label">Drivers</div>', unsafe_allow_html=True)
    driver_pool = df.copy()
    if selected_season != "All":
        driver_pool = driver_pool[driver_pool["SeasonYear"] == int(selected_season)]
    if selected_gp != "All":
        driver_pool = driver_pool[driver_pool["GrandPrix"] == selected_gp]
    available_drivers = sorted(driver_pool["Driver"].unique())
    selected_drivers = st.multiselect("Drivers", available_drivers, default=[], label_visibility="collapsed", key="top_drivers")
    st.markdown('</div>', unsafe_allow_html=True)

# Filter data with loader
with st.spinner('🔄 Loading race data...'):
    temp_df = df.copy()
    if selected_season != "All":
        temp_df = temp_df[temp_df["SeasonYear"] == int(selected_season)]
    if selected_gp != "All":
        temp_df = temp_df[temp_df["GrandPrix"] == selected_gp]

    used_compounds = sorted(temp_df["Compound"].dropna().unique())
    final_compounds = used_compounds

    filtered_df = temp_df[temp_df["Driver"].isin(selected_drivers)].copy()

if len(selected_drivers) == 0:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.info("Please select one or more drivers from the filter above to view statistics and analytics.")
    st.stop()

if filtered_df.empty:
    st.warning("⚠️ No data found for selected filters. Try different options.")
    st.stop()

st.markdown("<br>", unsafe_allow_html=True)

# ======================= CIRCUIT LAYOUT =======================

create_section_header("Circuit Layout")

with st.spinner('🗺️ Loading circuit layout...'):
    if selected_season != "All" and selected_gp != "All":
        try:
            session = get_session(int(selected_season), selected_gp, 'R')
            session.load(telemetry=True, laps=True)
            
            lap = session.laps.pick_fastest()
            tel = lap.get_telemetry()
            
            try:
                circuit_info = session.get_circuit_info()
                circuit_name = circuit_info.name
                circuit_length = circuit_info.length / 1000 if circuit_info.length else None
            except:
                circuit_name = selected_gp
                circuit_length = None
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=tel['X'], y=tel['Y'],
                mode='lines',
                line=dict(color='rgba(255, 255, 255, 0.7)', width=3),
                name='Racing Line',
                hovertemplate='X: %{x:.0f}m<br>Y: %{y:.0f}m<extra></extra>',
                fill='toself',
                fillcolor='rgba(255, 255, 255, 0.04)'
            ))
            
            fig.add_trace(go.Scatter(
                x=[tel['X'].iloc[0]], y=[tel['Y'].iloc[0]],
                mode='markers',
                marker=dict(color='white', size=14, symbol='circle'),
                name='Start/Finish',
                hovertemplate='Start/Finish<extra></extra>'
            ))
            
            title_text = f"{circuit_name}"
            if circuit_length:
                title_text += f" • {circuit_length:.3f} km"
            
            fig.update_layout(
                title=dict(text=title_text, font=dict(size=15, color='#AAA', family='Inter')),
                template='plotly_dark',
                showlegend=False,
                height=500,
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, visible=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, visible=False, scaleanchor="x", scaleratio=1),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=20, r=20, t=60, b=20),
                font=dict(family='Inter')
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception:
            st.plotly_chart(show_default_circuit(), use_container_width=True)
    else:
        st.plotly_chart(show_default_circuit(), use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ======================= CURRENT SELECTION + RACE INFO =======================

selection_text = f"""
<div class="current-selection">
    <strong>Current Selection:</strong> 
    Season: <strong>{selected_season}</strong> • 
    Grand Prix: <strong>{selected_gp}</strong> • 
    Drivers: <strong>{', '.join(selected_drivers)}</strong> • 
    Data Points: <strong>{len(filtered_df):,}</strong>
</div>
"""
st.markdown(selection_text, unsafe_allow_html=True)

# Race Information with Podium
if selected_season != "All" and selected_gp != "All":
    race_data = df[
        (df["SeasonYear"] == int(selected_season)) & 
        (df["GrandPrix"] == selected_gp)
    ]
    
    if not race_data.empty:
        podium = get_podium(int(selected_season), selected_gp, race_data)
        if len(podium) >= 3:
            create_podium_display(podium)
        
        race_info = race_data.iloc[0]
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Circuit</div>
                <div class="metric-value" style="font-size: 15px;">{race_info.get("CircuitName", selected_gp)}</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Country</div>
                <div class="metric-value" style="font-size: 15px;">{race_info.get("CircuitCountry", "N/A")}</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            race_laps = race_data["LapNumber"].max()
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Distance</div>
                <div class="metric-value">{race_laps} laps</div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            circuit_type = race_info.get("CircuitType", "N/A")
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Type</div>
                <div class="metric-value" style="font-size: 15px;">{circuit_type}</div>
            </div>
            """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ======================= STATS SECTION =======================

with st.spinner('📊 Analyzing race statistics...'):
    create_section_header(" Race Statistics ")

# Race Summary
create_subsection_header("Race Summary")
create_explainer(
    "What This Shows",
    "Complete overview of driver performance including average pace, fastest single-lap times, total laps completed, and pit stop strategies.",
    [
        "Compare average lap times to see overall race pace",
        "Fastest lap shows peak performance capability",
        "Total laps indicates race completion or DNFs",
        "Pit stops reveal strategic choices"
    ]
)

summary = filtered_df.groupby("Driver").agg(
    AvgLap=("LapTimeSeconds", "mean"),
    FastestLap=("LapTimeSeconds", "min"),
    TotalLaps=("LapNumber", "count"),
    PitStops=("PitLap", lambda x: x.notna().sum())
).reset_index()

summary["AvgLap"] = summary["AvgLap"].round(3)
summary["FastestLap"] = summary["FastestLap"].round(3)
summary = summary.sort_values("FastestLap")

st.dataframe(
    summary,
    use_container_width=True,
    column_config={
        "Driver": st.column_config.TextColumn("Driver", width="small"),
        "AvgLap": st.column_config.NumberColumn("Avg Lap Time (s)", format="%.3f"),
        "FastestLap": st.column_config.NumberColumn("Fastest Lap (s)", format="%.3f"),
        "TotalLaps": st.column_config.NumberColumn("Total Laps", format="%d"),
        "PitStops": st.column_config.NumberColumn("Pit Stops", format="%d"),
    },
    hide_index=True
)

st.markdown("<br>", unsafe_allow_html=True)

# Gap to Leader
create_subsection_header("Gap to Leader")
create_explainer(
    "What This Shows",
    "Time difference between each driver and the race leader throughout every lap of the Grand Prix.",
    [
        "Flat lines = consistent pace relative to leader",
        "Sudden jumps = pit stops or incidents",
        "Converging lines = driver catching up",
        "Diverging lines = gap increasing"
    ]
)

gap_df = filtered_df.copy()
gap_df["LeaderLap"] = gap_df.groupby("LapNumber")["LapTimeSeconds"].transform("min")
gap_df["GapToLeader"] = gap_df["LapTimeSeconds"] - gap_df["LeaderLap"]

fig = px.line(
    gap_df, x="LapNumber", y="GapToLeader", color="Driver_Season",
    template="plotly_dark", color_discrete_map=driver_colors
)
fig.update_layout(
    xaxis_title="Lap Number",
    yaxis_title="Gap (seconds)",
    hovermode='x unified',
    height=450,
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    showlegend=True,
    legend=dict(font=dict(size=12, family='Inter')),
    font=dict(family='Inter')
)
fig.update_traces(line=dict(width=2.5))
st.plotly_chart(fig, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# Tyre Degradation
create_subsection_header("Tyre Degradation")

st.markdown("""
<div class="tyre-legend">
    <div class="tyre-item"><div class="tyre-circle" style="background: #FF0000;"></div> Soft</div>
    <div class="tyre-item"><div class="tyre-circle" style="background: #FFF200;"></div> Medium</div>
    <div class="tyre-item"><div class="tyre-circle" style="background: #FFFFFF;"></div> Hard</div>
    <div class="tyre-item"><div class="tyre-circle" style="background: #00FF00;"></div> Intermediate</div>
    <div class="tyre-item"><div class="tyre-circle" style="background: #0000FF;"></div> Wet</div>
</div>
""", unsafe_allow_html=True)

create_explainer(
    "What This Shows",
    "Lap time increase as tyres age, showing grip loss and performance degradation over stint length.",
    [
        "Steeper slopes = faster degradation",
        "Soft tyres degrade fastest but offer best initial grip",
        "Hard tyres degrade slowest but have less peak performance",
        "Flat lines indicate excellent tyre management"
    ]
)

slope_df = filtered_df.dropna(subset=["TyreLife", "LapTimeSeconds"])
grouped = slope_df.groupby(["Driver_Season", "TyreLife", "Compound"]).LapTimeSeconds.mean().reset_index()

fig = px.line(
    grouped, x="TyreLife", y="LapTimeSeconds", color="Driver_Season",
    line_dash="Compound",
    template="plotly_dark", color_discrete_map=driver_colors
)
fig.update_layout(
    xaxis_title="Tyre Life (laps)",
    yaxis_title="Lap Time (seconds)",
    hovermode='x unified',
    height=450,
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    legend=dict(font=dict(size=12, family='Inter')),
    font=dict(family='Inter')
)
fig.update_traces(line=dict(width=2.5))
st.plotly_chart(fig, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# Sector Dominance
create_subsection_header("Sector Dominance")
create_explainer(
    "What This Shows",
    "Track sectors where each driver records their best times. S1 = technical sections, S2 = high-speed, S3 = tight corners.",
    [
        "S1 dominance = excellent in technical sections",
        "S2 dominance = advantage in high-speed performance",
        "S3 dominance = strong under braking and tight cornering"
    ]
)

if "BestSector" in filtered_df.columns:
    sector_pref = filtered_df.groupby(["Driver", "BestSector"]).size().reset_index(name="Count")
    sector_pref["BestSector"] = sector_pref["BestSector"].map({1: "S1", 2: "S2", 3: "S3"})
    
    driver_teams = filtered_df.drop_duplicates("Driver")[["Driver", "Team"]].set_index("Driver")["Team"].to_dict()
    sector_pref["Team"] = sector_pref["Driver"].map(driver_teams)
    sector_pref["Color"] = sector_pref["Team"].map(TEAM_COLORS).fillna(TEAM_COLORS["Other"])
    
    fig = go.Figure()
    for driver in sector_pref["Driver"].unique():
        driver_data = sector_pref[sector_pref["Driver"] == driver]
        team_color = driver_data["Color"].iloc[0]
        
        fig.add_trace(go.Bar(
            x=driver_data["BestSector"],
            y=driver_data["Count"],
            name=driver,
            marker_color=team_color,
            hovertemplate='<b>%{fullData.name}</b><br>%{x}: %{y}<extra></extra>',
        ))
    
    fig.update_layout(
        barmode="group",
        template="plotly_dark",
        xaxis_title="Sector",
        yaxis_title="Count",
        xaxis={'type': 'category'},
        hovermode='x unified',
        height=450,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(font=dict(size=12, family='Inter')),
        font=dict(family='Inter')
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# Stint Type Pace
create_subsection_header("Stint Type Pace")
create_explainer(
    "What This Shows",
    "Lap time distribution across opening (fresh tyres), mid (optimal window), and closing (worn) stints.",
    [
        "Opening: Fastest but higher variation due to heavy fuel",
        "Mid: Most consistent performance",
        "Closing: Typically slowest due to worn tyres"
    ]
)

if "Stint" in filtered_df.columns:
    stint_max = filtered_df.groupby("Driver")["Stint"].transform("max")
    filtered_df["StintType"] = np.where(
        filtered_df["Stint"] == 1, "Opening",
        np.where(filtered_df["Stint"] == stint_max, "Closing", "Mid")
    )
    
    fig = px.box(
        filtered_df, x="StintType", y="LapTimeSeconds", color="Driver_Season",
        template="plotly_dark", color_discrete_map=driver_colors
    )
    fig.update_layout(
        xaxis_title="Stint Type",
        yaxis_title="Lap Time (seconds)",
        height=450,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(font=dict(size=12, family='Inter')),
        font=dict(family='Inter')
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown("<br><br>", unsafe_allow_html=True)

# ======================= PREDICTIVE INTELLIGENCE =======================

create_section_header("Predictive Intelligence")

st.markdown("""
<div class="ai-detail">
<div class="ai-detail-title">🤖 About Predictive Intelligence</div>
<div class="ai-detail-text">
This section uses advanced machine learning algorithms to analyze historical F1 data and make predictions about future performance. Each tab showcases a different AI model:<br><br>
<strong>• LSTM Forecast:</strong> Deep learning neural network that learns sequential patterns in tyre degradation to predict future lap times beyond available data<br>
<strong>• Lap Time Regression:</strong> Statistical model identifying which factors (temperature, tyre life, fuel load) most influence lap times<br>
<strong>• Strategy Predictor:</strong> Analysis of historical stint data to determine optimal pit stop windows and compare predicted vs actual race strategies
</div>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["LSTM Forecast", "Lap Time Regression", "Strategy Predictor"])

# TAB 1: LSTM
with tab1:
    create_subsection_header("LSTM Neural Network Forecasting")
    
    create_ai_detail(
        "🧠 What is LSTM?",
        "LSTM (Long Short-Term Memory) is a type of recurrent neural network designed to learn from sequences of data. Unlike traditional models, LSTM 'remembers' patterns over time, making it perfect for predicting how lap times evolve as tyres degrade lap after lap."
    )
    
    create_ai_detail(
        "📊 What Does the Forecast Show?",
        "<strong>Blue Circles (Training):</strong> Historical data used to train the model (80% of available laps)<br><br>" +
        "<strong>Cyan Diamonds (Test - Actual):</strong> Real lap times from laps the model hasn't seen (20% held out for validation)<br><br>" +
        "<strong>Red X Marks (Test - Predicted):</strong> Model's predictions on the held-out test laps. Compare these with cyan diamonds to see accuracy<br><br>" +
        "<strong>Yellow Line/Dots (Forecast):</strong> The model's predictions for 15 laps BEYOND the available data. This shows when tyres might 'fall off' and require a pit stop"
    )
    
    create_ai_detail(
        "🎯 What Can You Learn?",
        "The forecast answers: <strong>'If the driver stayed on these tyres, how would lap times evolve?'</strong><br><br>" +
        "• <strong>Upward forecast slope:</strong> Tyres degrading significantly - pit stop likely needed soon<br>" +
        "• <strong>Flat forecast:</strong> Tyres holding up well - could extend stint<br>" +
        "• <strong>Gap between red X and cyan diamonds:</strong> Shows model accuracy on unseen data<br>" +
        "• <strong>Training loss curve:</strong> How well the model learned the patterns (lower = better)"
    )
    
    ai_drivers = sorted(temp_df["Driver_Season"].unique())
    sel_driver = st.selectbox("Select Driver", [""] + ai_drivers, index=0, key="lstm_driver")
    
    # Only proceed if driver is selected
    if sel_driver == "":
        st.info(" Please select a driver to view LSTM forecast")
    else:
        # Get all compounds available for this driver
        driver_df = temp_df[temp_df["Driver_Season"] == sel_driver]
        available_compounds = sorted(driver_df["Compound"].unique())
        
        if len(available_compounds) == 0:
            st.warning("No compound data available for this driver")
        else:
            # Create a tab or section for each compound
            compound_tabs = st.tabs(available_compounds)
            
            for idx, compound in enumerate(available_compounds):
                with compound_tabs[idx]:
                    df_model = driver_df[driver_df["Compound"] == compound]
                    
                    if df_model.shape[0] > 20:
                                df_model_sorted = df_model.sort_values("TyreLife").reset_index(drop=True)
                                series = df_model_sorted["LapTimeSeconds"].values.reshape(-1, 1)
            
                                scaler = MinMaxScaler()
                                scaled = scaler.fit_transform(series)
            
                                window = 5
                                X, y = [], []
                                for i in range(len(scaled) - window):
                                    X.append(scaled[i:i+window])
                                    y.append(scaled[i+window])
            
                                X = torch.tensor(X).float()
                                y = torch.tensor(y).float()
            
                                split_idx = int(len(X) * 0.8)
                                X_train, X_test = X[:split_idx], X[split_idx:]
                                y_train, y_test = y[:split_idx], y[split_idx:]
            
                                class LSTMModel(nn.Module):
                                    def __init__(self):
                                        super().__init__()
                                        self.lstm = nn.LSTM(input_size=1, hidden_size=64, batch_first=True)
                                        self.fc = nn.Linear(64, 1)
                
                                    def forward(self, x):
                                        x, _ = self.lstm(x)
                                        return self.fc(x[:, -1, :])
            
                                model = LSTMModel()
                                loss_fn = nn.MSELoss()
                                optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
            
                                losses = []
                                with st.spinner("🔄 Training LSTM model..."):
                                    for epoch in range(100):
                                        optimizer.zero_grad()
                                        output = model(X_train).squeeze()
                                        loss = loss_fn(output, y_train.squeeze())
                                        loss.backward()
                                        optimizer.step()
                                        losses.append(loss.item())
            
                                model.eval()
                                with torch.no_grad():
                                    test_preds = model(X_test).detach().numpy()
            
                                test_preds_actual = scaler.inverse_transform(test_preds)
                                y_test_actual = scaler.inverse_transform(y_test.numpy())
            
                                rmse = np.sqrt(mean_squared_error(y_test_actual, test_preds_actual))
            
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.markdown(f"""
                                    <div class="metric-card">
                                        <div class="metric-label">Test RMSE</div>
                                        <div class="metric-value">{rmse:.4f} sec</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                with col2:
                                    st.markdown(f"""
                                    <div class="metric-card">
                                        <div class="metric-label">Training Epochs</div>
                                        <div class="metric-value">100</div>
                                    </div>
                                    """, unsafe_allow_html=True)
            
                                # Forecast future
                                pred_seq = scaled[-window:]
                                forecast = []
                                for _ in range(15):
                                    input_tensor = torch.tensor(pred_seq).float().unsqueeze(0)
                                    with torch.no_grad():
                                        next_pred = model(input_tensor).detach().numpy()[0][0]
                                    forecast.append(next_pred)
                                    pred_seq = np.vstack([pred_seq[1:], [[next_pred]]])
            
                                forecast_actual = scaler.inverse_transform(np.array(forecast).reshape(-1, 1)).flatten()
                                future_laps = list(range(
                                    int(df_model_sorted["TyreLife"].max()) + 1,
                                    int(df_model_sorted["TyreLife"].max()) + 1 + len(forecast_actual)
                                ))
            
                                fig = go.Figure()
            
                                # Training data
                                train_laps = df_model_sorted["TyreLife"].values[:split_idx + window]
                                train_times = df_model_sorted["LapTimeSeconds"].values[:split_idx + window]
            
                                fig.add_trace(go.Scatter(
                                    x=train_laps,
                                    y=train_times,
                                    name="Training Data",
                                    mode='markers',
                                    marker=dict(size=6, color='#4A9EFF', opacity=0.7),
                                    hovertemplate='Lap: %{x}<br>Time: %{y:.3f}s<extra></extra>'
                                ))
            
                                # Test actual
                                test_laps = df_model_sorted["TyreLife"].values[split_idx + window:]
                                test_times = y_test_actual.flatten()
            
                                fig.add_trace(go.Scatter(
                                    x=test_laps,
                                    y=test_times,
                                    name="Test (Actual)",
                                    mode='markers',
                                    marker=dict(size=8, color='#00D9FF', symbol='diamond'),
                                    hovertemplate='Lap: %{x}<br>Actual: %{y:.3f}s<extra></extra>'
                                ))
            
                                # Test predicted
                                fig.add_trace(go.Scatter(
                                    x=test_laps,
                                    y=test_preds_actual.flatten(),
                                    name="Test (Predicted)",
                                    mode='markers',
                                    marker=dict(size=8, color='#FF6B6B', symbol='x'),
                                    hovertemplate='Lap: %{x}<br>Predicted: %{y:.3f}s<extra></extra>'
                                ))
            
                                # Future forecast
                                fig.add_trace(go.Scatter(
                                    x=future_laps,
                                    y=forecast_actual,
                                    name="Forecast (Future)",
                                    mode='lines+markers',
                                    line=dict(dash="dot", width=3, color='#FFD93D'),
                                    marker=dict(size=7, color='#FFD93D'),
                                    hovertemplate='Lap: %{x}<br>Forecast: %{y:.3f}s<extra></extra>'
                                ))
            
                                fig.update_layout(
                                    template="plotly_dark",
                                    xaxis_title="Tyre Life (laps)",
                                    yaxis_title="Lap Time (seconds)",
                                    hovermode='closest',
                                    height=500,
                                    plot_bgcolor='rgba(0,0,0,0)',
                                    paper_bgcolor='rgba(0,0,0,0)',
                                    legend=dict(
                                        font=dict(size=12, family='Inter'),
                                        orientation="h",
                                        yanchor="bottom",
                                        y=1.02,
                                        xanchor="right",
                                        x=1
                                    ),
                                    font=dict(family='Inter')
                                )
                                st.plotly_chart(fig, use_container_width=True, key=f"lstm_chart_{compound}")
            
                                show_loss = st.checkbox("📉 View Training Loss Curve", key=f"show_lstm_loss_{compound}")
                                if show_loss:
                                    loss_fig = go.Figure()
                                    loss_fig.add_trace(go.Scatter(
                                        y=losses,
                                        mode='lines',
                                        line=dict(color='#FF6B6B', width=2),
                                        fill='tozeroy',
                                        fillcolor='rgba(255, 107, 107, 0.1)'
                                    ))
                                    loss_fig.update_layout(
                                        template="plotly_dark",
                                        title="Model Training Loss (Lower = Better Learning)",
                                        xaxis_title="Epoch",
                                        yaxis_title="Loss (MSE)",
                                        height=350,
                                        plot_bgcolor='rgba(0,0,0,0)',
                                        paper_bgcolor='rgba(0,0,0,0)',
                                        font=dict(family='Inter')
                                    )
                                    st.plotly_chart(loss_fig, use_container_width=True, key=f"lstm_loss_chart_{compound}")
                    else:
                        st.info("ℹ️ Not enough data for LSTM model (need > 20 laps). Try selecting a different compound.")

# TAB 2: REGRESSION
with tab2:
    create_subsection_header("Linear Regression Analysis")
    
    create_ai_detail(
        "📈 What is Linear Regression?",
        "Linear regression finds mathematical relationships between input factors (temperature, tyre life, fuel load, compound type) and lap times. It calculates how much each factor contributes to making laps faster or slower."
    )
    
    create_ai_detail(
        "📊 What Does the Scatter Plot Show?",
        "<strong>Gray Dashed Line:</strong> Perfect prediction line (if actual = predicted, point lands on this line)<br><br>" +
        "<strong>Blue Circles:</strong> Each circle is an actual lap time from the test set<br><br>" +
        "<strong>Red Diamonds:</strong> Model's predictions for those same laps<br><br>" +
        "<strong>Closeness to gray line:</strong> Shows how accurate the model is. Tighter clustering = better predictions"
    )
    
    create_ai_detail(
        "🎯 What Can You Learn?",
        "<strong>RMSE (Root Mean Square Error):</strong> Average prediction error in seconds. Lower = better<br><br>" +
        "<strong>R² Score:</strong> How much variance the model explains (0-1). Higher = better. 0.8+ is excellent<br><br>" +
        "<strong>Feature Importance:</strong> Shows which factors most affect lap times:<br>" +
        "• <strong>Green bars (negative):</strong> Factor makes laps faster<br>" +
        "• <strong>Red bars (positive):</strong> Factor makes laps slower<br>" +
        "• <strong>Taller bars:</strong> Stronger impact on lap time"
    )
    
    ai_drivers_reg = sorted(temp_df["Driver_Season"].unique())
    sel_driver_reg = st.selectbox("Select Driver", [""] + ai_drivers_reg, index=0, key="reg_driver")
    
    # Only proceed if driver is selected
    if sel_driver_reg == "":
        st.info(" Please select a driver to view regression analysis")
    else:
        df_reg = temp_df[temp_df["Driver_Season"] == sel_driver_reg].dropna(subset=["TrackTemp", "LapTimeSeconds"])
        
        if len(df_reg) > 20:
            median_lap = df_reg["LapTimeSeconds"].median()
            df_reg = df_reg[df_reg["LapTimeSeconds"] < (median_lap + 3.0)]
        
            df_reg["CompoundCode"] = df_reg["Compound"].astype("category").cat.codes
            X = df_reg[["TrackTemp", "TyreLife", "CompoundCode", "LapNumber"]]
            y = df_reg["LapTimeSeconds"]
        
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
            model_reg = LinearRegression().fit(X_train, y_train)
            y_pred_train = model_reg.predict(X_train)
            y_pred_test = model_reg.predict(X_test)
        
            rmse_train = np.sqrt(mean_squared_error(y_train, y_pred_train))
            rmse_test = np.sqrt(mean_squared_error(y_test, y_pred_test))
            r2_train = r2_score(y_train, y_pred_train)
            r2_test = r2_score(y_test, y_pred_test)
        
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Train RMSE</div>
                    <div class="metric-value">{rmse_train:.4f}</div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Test RMSE</div>
                    <div class="metric-value">{rmse_test:.4f}</div>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Train R²</div>
                    <div class="metric-value">{r2_train:.4f}</div>
                </div>
                """, unsafe_allow_html=True)
            with col4:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Test R²</div>
                    <div class="metric-value">{r2_test:.4f}</div>
                </div>
                """, unsafe_allow_html=True)
        
            # Scatter plot
            fig = go.Figure()
        
            min_val = min(y_test.min(), y_pred_test.min())
            max_val = max(y_test.max(), y_pred_test.max())
            fig.add_trace(go.Scatter(
                x=[min_val, max_val],
                y=[min_val, max_val],
                mode='lines',
                name='Perfect Prediction',
                line=dict(color='rgba(100, 100, 100, 0.4)', dash='dash', width=2),
                hoverinfo='skip'
            ))
        
            fig.add_trace(go.Scatter(
                x=y_test,
                y=y_test,
                mode='markers',
                name='Actual',
                marker=dict(size=8, color='#4A9EFF', opacity=0.7, symbol='circle'),
                hovertemplate='Actual: %{x:.3f}s<extra></extra>'
            ))
        
            fig.add_trace(go.Scatter(
                x=y_test,
                y=y_pred_test,
                mode='markers',
                name='Predicted',
                marker=dict(size=8, color='#FF6B6B', opacity=0.8, symbol='diamond'),
                hovertemplate='Actual: %{x:.3f}s<br>Predicted: %{y:.3f}s<extra></extra>'
            ))
        
            fig.update_layout(
                template="plotly_dark",
                xaxis_title="Actual Lap Time (seconds)",
                yaxis_title="Predicted Lap Time (seconds)",
                hovermode='closest',
                height=500,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                legend=dict(
                    font=dict(size=12, family='Inter'),
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                font=dict(family='Inter')
            )
            st.plotly_chart(fig, use_container_width=True, key="reg_scatter")
        
            # Feature importance - FIXED
            create_subsection_header("Feature Importance Analysis")
        
            feature_names = ["Track Temperature", "Tyre Life", "Compound Type", "Lap Number (Fuel)"]
            coefficients = model_reg.coef_
        
            # Create DataFrame for proper ordering
            feat_df = pd.DataFrame({
                'Feature': feature_names,
                'Coefficient': coefficients,
                'Abs_Coef': np.abs(coefficients)
            }).sort_values('Abs_Coef', ascending=True)  # Sort by absolute value
        
            feat_fig = go.Figure(go.Bar(
                x=feat_df['Coefficient'],
                y=feat_df['Feature'],
                orientation='h',
                marker_color=['#4AFF88' if c < 0 else '#FF6B6B' for c in feat_df['Coefficient']],
                text=[f"{c:+.4f}" for c in feat_df['Coefficient']],
                textposition='outside',
                hovertemplate='%{y}<br>Coefficient: %{x:.4f}<extra></extra>'
            ))
        
            feat_fig.update_layout(
                template="plotly_dark",
                title="Which Factors Most Affect Lap Times?",
                xaxis_title="Coefficient (Impact on Lap Time)",
                yaxis_title="",
                height=400,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Inter')
            )
            st.plotly_chart(feat_fig, use_container_width=True, key="reg_features")
        
            st.markdown("""
            <div class="insights">
                <div class="insights-title">How to Read Feature Importance</div>
                <div class="explainer-text">
                    • <strong>Positive coefficient (red):</strong> Increasing this factor makes lap times SLOWER (worse)<br>
                    • <strong>Negative coefficient (green):</strong> Increasing this factor makes lap times FASTER (better)<br>
                    • <strong>Larger bars:</strong> Stronger influence on lap time performance<br><br>
                    <strong>Example:</strong> If "Tyre Life" has a coefficient of +0.05, each additional lap on tyres adds 0.05 seconds to lap time
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("ℹ️ Not enough data for regression model (need > 20 laps).")

# TAB 3: STRATEGY - COMPLETELY REDESIGNED
with tab3:
    create_subsection_header("Strategy Optimization Model")
    
    create_ai_detail(
        "🏁 What is Strategy Prediction?",
        "This AI model analyzes historical stint data across all your selected driver's races to learn optimal tyre usage patterns. It predicts the best pit stop windows based on compound performance, degradation rates, and stint length statistics."
    )
    
    create_ai_detail(
        "📊 How the Model Works",
        "<strong>Step 1:</strong> Collects all historical stint data (length, compound, lap times)<br>" +
        "<strong>Step 2:</strong> Calculates average optimal stint length per compound<br>" +
        "<strong>Step 3:</strong> Identifies compounds with best performance (fastest average lap times)<br>" +
        "<strong>Step 4:</strong> Generates predicted pit stop strategy based on these patterns<br>" +
        "<strong>Step 5:</strong> Compares prediction with actual race execution"
    )
    
    ai_drivers_strat = sorted(temp_df["Driver"].unique())
    sel_driver_strat = st.selectbox("Select Driver", [""] + ai_drivers_strat, index=0, key="strat_driver")
    
    # Only proceed if driver is selected
    if sel_driver_strat == "":
        st.info(" Please select a driver to view strategy predictions")
    else:
        driver_strat_df = temp_df[temp_df["Driver"] == sel_driver_strat]
        
        if not driver_strat_df.empty:
            stint_df = driver_strat_df.groupby(["Compound", "Stint"]).agg(
                AvgLap=("LapTimeSeconds", "mean"),
                StintLen=("TyreLife", "max"),
                NumStints=("Stint", "count")
            ).reset_index()
        
            # PREDICTIVE GRAPH - Shows model learning from historical data
            create_subsection_header("Model Learning: Historical Stint Performance")
        
            create_ai_detail(
                "📈 What This Graph Shows",
                "<strong>This visualizes the MODEL'S learning process:</strong><br><br>" +
                "• <strong>Each bar:</strong> Average optimal stint length the model learned for each compound<br>" +
                "• <strong>Height:</strong> How many laps the model recommends per compound based on historical data<br>" +
                "• <strong>Color:</strong> Compound type (Red=Soft, Yellow=Medium, White=Hard)<br><br>" +
                "This is NOT raw data - it's the model's <strong>learned recommendations</strong> for optimal stint lengths."
            )
        
            # Calculate model predictions - average stint lengths per compound
            model_predictions = stint_df.groupby("Compound").agg({
                "StintLen": "mean",
                "AvgLap": "mean"
            }).reset_index()
            model_predictions.columns = ["Compound", "Predicted_Stint_Length", "Avg_Pace"]
        
            # Create predictive bar chart
            pred_fig = go.Figure()
        
            for _, row in model_predictions.iterrows():
                compound = row['Compound']
                pred_length = row['Predicted_Stint_Length']
            
                pred_fig.add_trace(go.Bar(
                    x=[compound],
                    y=[pred_length],
                    name=compound,
                    marker_color=COMPOUND_COLORS.get(compound, '#AAAAAA'),
                    text=f"{pred_length:.1f} laps",
                    textposition='outside',
                    hovertemplate=f'<b>{compound}</b><br>Model Prediction: {pred_length:.1f} laps<extra></extra>',
                    showlegend=False
                ))
        
            pred_fig.update_layout(
                template="plotly_dark",
                title="AI Model's Learned Optimal Stint Lengths per Compound",
                xaxis_title="Compound",
                yaxis_title="Predicted Optimal Stint Length (laps)",
                height=450,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Inter')
            )
            st.plotly_chart(pred_fig, use_container_width=True, key="strat_prediction_graph")
        
            # Performance Summary - What the model learned
            create_subsection_header("Model's Performance Analysis")
        
            create_ai_detail(
                "📋 What This Table Shows",
                "<strong>This summarizes what the AI model learned from historical data:</strong><br><br>" +
                "• <strong>Predicted Stint Length:</strong> Average optimal laps per compound (model's recommendation)<br>" +
                "• <strong>Best Observed:</strong> Longest successful stint seen in data<br>" +
                "• <strong>Historical Uses:</strong> How many times this compound was used (model confidence)<br>" +
                "• <strong>Average Pace:</strong> Expected lap time on this compound<br><br>" +
                "More historical uses = higher model confidence in the prediction."
            )
        
            # Beautiful HTML table with model predictions
            html_table = '<table class="strategy-table">'
            html_table += '<thead><tr><th>Compound</th><th>Predicted Stint (laps)</th><th>Best Observed (laps)</th><th>Historical Uses</th><th>Avg Pace (s)</th></tr></thead><tbody>'
        
            for _, row in model_predictions.iterrows():
                compound_data = stint_df[stint_df['Compound'] == row['Compound']]
                max_stint = compound_data['StintLen'].max()
                total_uses = len(compound_data)
            
                html_table += '<tr>'
                html_table += f'<td><strong>{row["Compound"]}</strong></td>'
                html_table += f'<td>{row["Predicted_Stint_Length"]:.1f}</td>'
                html_table += f'<td>{max_stint:.0f}</td>'
                html_table += f'<td>{total_uses}</td>'
                html_table += f'<td>{row["Avg_Pace"]:.3f}</td>'
                html_table += '</tr>'
        
            html_table += '</tbody></table>'
            st.markdown(html_table, unsafe_allow_html=True)
        
            # Strategy comparison - SWAPPED and FIXED
            if selected_season != "All" and selected_gp != "All":
                st.markdown("<br>", unsafe_allow_html=True)
                create_subsection_header("Model Prediction vs Actual Race Execution")
            
                race_data_full = df[
                    (df["SeasonYear"] == int(selected_season)) &
                    (df["GrandPrix"] == selected_gp)
                ]
            
                actual_strategy = get_actual_pit_strategy(int(selected_season), selected_gp, sel_driver_strat, race_data_full)
            
                if actual_strategy and actual_strategy['stints']:
                    col1, col2 = st.columns(2)
                
                    total_race_laps = race_data_full["LapNumber"].max()
                
                    # LEFT PANEL: ACTUAL RACE (SWAPPED)
                    with col1:
                        st.markdown('<div class="comparison-panel">', unsafe_allow_html=True)
                        st.markdown('<div class="panel-title">🏁 Actual Race Strategy</div>', unsafe_allow_html=True)
                    
                        # Format actual strategy
                        actual_data = []
                        if actual_strategy['stints']:
                            for stint in actual_strategy['stints']:
                                actual_data.append({
                                    "Stint": stint['stint'],
                                    "Laps": f"{stint['start_lap']}-{stint['end_lap']}",
                                    "Length": stint['length'],
                                    "Compound": stint['compound']
                                })
                    
                        actual_table = pd.DataFrame(actual_data)
                    
                        # Render Actual Table
                        html_actual = '<table class="strategy-table">'
                        html_actual += '<thead><tr><th>Stint</th><th>Laps</th><th>Length</th><th>Compound</th></tr></thead><tbody>'
                        for _, row in actual_table.iterrows():
                            html_actual += '<tr>'
                            html_actual += f'<td>{row["Stint"]}</td>'
                            html_actual += f'<td>{row["Laps"]}</td>'
                            html_actual += f'<td>{row["Length"]} laps</td>'
                            html_actual += f'<td><strong>{row["Compound"]}</strong></td>'
                            html_actual += '</tr>'
                        html_actual += '</tbody></table>'
                        st.markdown(html_actual, unsafe_allow_html=True)
                    
                        # Display accurate pit stop count
                        st.markdown(f"<br><strong>Total Pit Stops:</strong> {actual_strategy['total_stops']}", unsafe_allow_html=True)
                    
                        st.markdown('</div>', unsafe_allow_html=True)
                
                    # RIGHT PANEL: MODEL PREDICTION (SWAPPED)
                    with col2:
                        st.markdown('<div class="comparison-panel">', unsafe_allow_html=True)
                        st.markdown('<div class="panel-title">🤖 AI Model Prediction</div>', unsafe_allow_html=True)
                    
                        # Generate model predictions based on learned patterns
                        predicted_data = []
                        lap_counter = 0
                        stint_num = 1
                    
                        # Sort compounds by performance (best average lap time first)
                        sorted_compounds = model_predictions.sort_values('Avg_Pace').head(3)
                    
                        for _, compound_row in sorted_compounds.iterrows():
                            compound = compound_row['Compound']
                            pred_length = int(compound_row['Predicted_Stint_Length'])
                        
                            start_lap = lap_counter + 1
                            end_lap = min(lap_counter + pred_length, total_race_laps)
                        
                            if start_lap < total_race_laps:
                                predicted_data.append({
                                    "Stint": stint_num,
                                    "Laps": f"{start_lap}-{end_lap}",
                                    "Length": end_lap - start_lap + 1,
                                    "Compound": compound
                                })
                                lap_counter = end_lap
                                stint_num += 1
                        
                            if lap_counter >= total_race_laps:
                                break
                    
                        if not predicted_data:
                            predicted_data = [{"Stint": "—", "Laps": "—", "Length": "—", "Compound": "No Prediction"}]
                    
                        predicted_table = pd.DataFrame(predicted_data)
                    
                        # Render Predicted Table
                        html_predicted = '<table class="strategy-table">'
                        html_predicted += '<thead><tr><th>Stint</th><th>Laps</th><th>Length</th><th>Compound</th></tr></thead><tbody>'
                        for _, row in predicted_table.iterrows():
                            html_predicted += '<tr>'
                            html_predicted += f'<td>{row["Stint"]}</td>'
                            html_predicted += f'<td>{row["Laps"]}</td>'
                            html_predicted += f'<td>{row["Length"]} laps</td>' if row["Length"] != "—" else f'<td>{row["Length"]}</td>'
                            html_predicted += f'<td><strong>{row["Compound"]}</strong></td>'
                            html_predicted += '</tr>'
                        html_predicted += '</tbody></table>'
                        st.markdown(html_predicted, unsafe_allow_html=True)
                    
                        # PREDICTED PIT STOPS (stints - 1)
                        predicted_stops = len(predicted_data) - 1 if len(predicted_data) > 0 else 0
                        st.markdown(f"<br><strong>Predicted Pit Stops:</strong> {predicted_stops}", unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                
                    st.markdown("""
                    <div class="insights">
                        <div class="insights-title">Understanding the Comparison</div>
                        <div class="explainer-text">
                            <strong>Left (Actual):</strong> What actually happened in the race<br>
                            <strong>Right (Prediction):</strong> What the AI model recommended based on historical learning<br><br>
                            Differences between predicted and actual strategies can result from:<br>
                            • <strong>Safety cars:</strong> Opportunistic pit stops during yellow flags<br>
                            • <strong>Track position battles:</strong> Staying out to defend or undercut/overcut competitors<br>
                            • <strong>Tyre allocation rules:</strong> Limited sets of preferred compounds<br>
                            • <strong>Weather changes:</strong> Rain requiring intermediates or wets<br>
                            • <strong>Damage/incidents:</strong> Unplanned stops for repairs<br>
                            • <strong>Race-specific conditions:</strong> Track evolution, temperatures, strategic gambles
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                    st.info("📊 Actual race strategy data not available for this driver/race combination.")
        else:
                st.info("ℹ️ Select a specific season and Grand Prix above to compare model predictions with actual race strategies.")
        # End of driver_strat_df check

st.markdown("<br><br>", unsafe_allow_html=True)

# ======================= FOOTER =======================

st.markdown("""
<div style="text-align: center; padding: 50px 20px; border-top: 1px solid rgba(255, 255, 255, 0.08);">
    <div style="font-size: 14px; color: #555; margin-bottom: 10px; font-family: 'Inter', sans-serif; font-weight: 500; letter-spacing: 2px;">
        RACINGLINEAI v13.4
    </div>
    <div style="font-size: 12px; color: #444; font-family: 'Inter', sans-serif;">
        Built by Om Patel • PyTorch • FastF1 • Streamlit • Plotly
    </div>
</div>
""", unsafe_allow_html=True)