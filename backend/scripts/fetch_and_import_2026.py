"""
Fetch 2026 F1 race data via FastF1 and import to Supabase.
Run with: backend/venv/bin/python backend/scripts/fetch_and_import_2026.py

Incremental — skips races already in the combined CSV.
"""

import sys
import os
import re
import logging

# ---- path setup so we can import app modules ----
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
ROOT_DIR = os.path.dirname(BACKEND_DIR)
sys.path.insert(0, BACKEND_DIR)

# Load .env from backend/
from dotenv import load_dotenv
load_dotenv(os.path.join(BACKEND_DIR, ".env"))

import pandas as pd
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ---- config ----
SEASON = 2026
WET_LAP_THRESHOLD = 0.1
CACHE_DIR = os.path.join(ROOT_DIR, ".fastf1_cache")
OUTPUT_DIR = os.path.join(ROOT_DIR, "data", "processed")
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

COMBINED_PATH = os.path.join(OUTPUT_DIR, f"all_races_combined_{SEASON}.csv")


def slugify(text: str) -> str:
    return re.sub(r"[^\w]+", "_", text.lower()).strip("_")


compound_map = {
    "SOFT": "Soft", "MEDIUM": "Medium", "HARD": "Hard",
    "INTERMEDIATE": "Intermediate", "WET": "Wet",
}


def fetch_season_data() -> pd.DataFrame:
    import fastf1
    fastf1.Cache.enable_cache(CACHE_DIR)
    logger.info(f"FastF1 cache enabled at {CACHE_DIR}")

    schedule = fastf1.get_event_schedule(SEASON, include_testing=False)

    # Load existing combined CSV (incremental)
    if os.path.exists(COMBINED_PATH):
        existing_df = pd.read_csv(COMBINED_PATH, low_memory=False)
        already_imported = set(existing_df["GP_Slug"].unique())
        all_races = [existing_df]
        print(f"📂 Found existing file with {len(existing_df)} rows across {len(already_imported)} races.")
        print(f"   Already imported: {sorted(already_imported)}")
    else:
        already_imported = set()
        all_races = []
        print("📂 No existing 2026 file — starting fresh.")

    for _, row in schedule.iterrows():
        round_num = row["RoundNumber"]
        event_name = row["EventName"]
        gp_slug = slugify(event_name)
        event_date = row["EventDate"]

        if gp_slug in already_imported:
            print(f"⏭️  Skipping (already imported): {event_name}")
            continue

        try:
            session = fastf1.get_session(SEASON, round_num, "R")
            session.load()
        except Exception as e:
            print(f"⏳ Not yet available or failed to load: {event_name} — {e}")
            continue

        try:
            laps = session.laps.reset_index(drop=True)
            selected_cols = [
                "Driver", "Team", "LapNumber", "LapTime",
                "Sector1Time", "Sector2Time", "Sector3Time",
                "Compound", "TyreLife", "Stint",
                "PitInTime", "PitOutTime", "TrackStatus",
                "IsAccurate", "Time",
            ]
            lap_data = laps[selected_cols].copy()

            for col in ["LapTime", "Sector1Time", "Sector2Time", "Sector3Time"]:
                lap_data[f"{col}Seconds"] = lap_data[col].dt.total_seconds()
            lap_data["LapStartTime"] = lap_data["Time"].dt.total_seconds()

            # Weather merge
            try:
                weather = session.weather_data.rename(columns={"Time": "WeatherTime"})
                weather["WeatherTime"] = weather["WeatherTime"].dt.total_seconds()
                lap_data = pd.merge_asof(
                    lap_data.sort_values("LapStartTime"),
                    weather.sort_values("WeatherTime"),
                    left_on="LapStartTime", right_on="WeatherTime",
                    direction="nearest",
                )
            except Exception:
                logger.warning(f"No weather data for {gp_slug}")
                lap_data["Rainfall"] = 0
                lap_data["AirTemp"] = None
                lap_data["Humidity"] = None
                lap_data["WindSpeed"] = None

            lap_data["IsWetLap"] = lap_data["Rainfall"] > WET_LAP_THRESHOLD
            lap_data["IsDryLap"] = lap_data["Rainfall"] <= WET_LAP_THRESHOLD
            lap_data["IsWetRace"] = lap_data["IsWetLap"].any()

            # Circuit metadata
            try:
                ci = session.get_circuit_info()
                lap_data["CircuitName"] = ci.name
                lap_data["CircuitShort"] = ci.location
                lap_data["CircuitCountry"] = ci.country
                lap_data["TrackLengthKM"] = ci.length / 1000 if ci.length else None
                lap_data["AltitudeM"] = ci.altitude
            except Exception:
                ev = session.event
                lap_data["CircuitName"] = ev.get("OfficialEventName", event_name)
                lap_data["CircuitShort"] = ev.get("Location", "Unknown")
                lap_data["CircuitCountry"] = ev.get("Country", "Unknown")
                lap_data["TrackLengthKM"] = None
                lap_data["AltitudeM"] = None

            lap_data["CircuitType"] = lap_data["CircuitShort"].apply(lambda n: (
                "Street" if isinstance(n, str) and any(x in n.lower() for x in ["monaco", "baku", "miami", "jeddah"])
                else "Hybrid" if isinstance(n, str) and "marina" in n.lower()
                else "Permanent"
            ))

            # Type cleanup
            lap_data["TrackStatus"] = lap_data["TrackStatus"].astype(str)
            lap_data["IsAccurate"] = lap_data["IsAccurate"].astype(bool)
            lap_data["LapNumber"] = lap_data["LapNumber"].fillna(0).astype(int)
            lap_data["TyreLife"] = lap_data["TyreLife"].fillna(0).astype(int)
            lap_data["Stint"] = lap_data["Stint"].fillna(0).astype(int)

            lap_data.dropna(subset=[
                "LapTimeSeconds", "Sector1TimeSeconds", "Sector2TimeSeconds",
                "Sector3TimeSeconds", "Compound",
            ], inplace=True)

            lap_data["Compound"] = (
                lap_data["Compound"].str.upper()
                .map(compound_map)
                .fillna(lap_data["Compound"])
            )

            # Pit info
            lap_data["PitLap"] = lap_data.apply(
                lambda r: r["LapNumber"] if pd.notna(r["PitInTime"]) else None, axis=1
            )
            lap_data["PitDuration"] = (
                lap_data["PitOutTime"] - lap_data["PitInTime"]
            ).dt.total_seconds()

            # Sector features
            lap_data["Sector1Pct"] = lap_data["Sector1TimeSeconds"] / lap_data["LapTimeSeconds"]
            lap_data["Sector2Pct"] = lap_data["Sector2TimeSeconds"] / lap_data["LapTimeSeconds"]
            lap_data["Sector3Pct"] = lap_data["Sector3TimeSeconds"] / lap_data["LapTimeSeconds"]
            lap_data["BestSector"] = (
                lap_data[["Sector1TimeSeconds", "Sector2TimeSeconds", "Sector3TimeSeconds"]]
                .idxmin(axis=1)
                .str.extract(r"(\d)")
                .astype(int)
            )
            lap_data["IsValidLap"] = (lap_data["TrackStatus"] == "Green") & lap_data["IsAccurate"]

            # Metadata
            lap_data["GrandPrix"] = event_name
            lap_data["GP_Slug"] = gp_slug
            lap_data["SeasonYear"] = SEASON
            lap_data["EventDate"] = pd.to_datetime(event_date)

            if "CarNumber" in laps.columns:
                lap_data["CarNumber"] = laps["CarNumber"]

            # Stint summary
            stint_summary = lap_data.groupby(["Driver", "Stint"]).agg(
                AvgLapTime=("LapTimeSeconds", "mean"),
                StintLength=("LapNumber", "count"),
            ).reset_index()
            lap_data = lap_data.merge(stint_summary, on=["Driver", "Stint"], how="left")

            stint_max_map = lap_data.groupby("Driver")["Stint"].max().to_dict()
            lap_data["StintType"] = lap_data.apply(
                lambda r: "Opening" if r["Stint"] == 1
                else "Closing" if r["Stint"] == stint_max_map.get(r["Driver"], 3)
                else "Mid",
                axis=1,
            )

            # Delta to driver's fastest lap
            fastest_per_driver = lap_data.groupby("Driver")["LapTimeSeconds"].min().to_dict()
            lap_data["DeltaToFastestLap"] = lap_data.apply(
                lambda r: r["LapTimeSeconds"] - fastest_per_driver.get(r["Driver"], r["LapTimeSeconds"]),
                axis=1,
            )

            # Status flags
            lap_data["IsSC"] = lap_data["TrackStatus"].str.contains("4").fillna(False)
            lap_data["IsVSC"] = lap_data["TrackStatus"].str.contains("8").fillna(False)
            lap_data["IsRedFlag"] = lap_data["TrackStatus"].str.contains("16").fillna(False)
            race_max_lap = lap_data["LapNumber"].max()
            lap_data["IsDNF"] = lap_data["LapNumber"] < (race_max_lap - 3)

            # Individual race CSV
            race_csv = os.path.join(OUTPUT_DIR, f"race_summary_{SEASON}_{gp_slug}.csv")
            lap_data.to_csv(race_csv, index=False)
            all_races.append(lap_data)
            already_imported.add(gp_slug)
            print(f"✅ Exported: {event_name} ({len(lap_data)} laps)")

        except Exception as e:
            logger.error(f"Failed processing {event_name}: {e}")
            print(f"❌ Failed: {event_name} — {e}")

    if len(all_races) == 0:
        print("⚠️  No races processed — nothing to save.")
        return None

    combined_df = pd.concat(all_races, ignore_index=True)
    combined_df.to_csv(COMBINED_PATH, index=False)
    print(f"\n🎉 Combined CSV → {COMBINED_PATH}")
    print(f"   {len(combined_df)} rows across {combined_df['GP_Slug'].nunique()} races")
    return combined_df


def import_to_db():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models.database import Base
    from app.core.config import settings
    from scripts.import_csv_to_db import import_season_data

    if not os.path.exists(COMBINED_PATH):
        print("⚠️  No combined CSV to import.")
        return

    print(f"\n📥 Importing to database …")
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    db = SessionLocal()
    try:
        import_season_data(COMBINED_PATH, db, SEASON)
        print("✅ Database import complete!")
    except Exception as e:
        print(f"❌ Database import failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print(f"=== Fetching {SEASON} F1 data ===\n")
    df = fetch_season_data()
    if df is not None:
        import_to_db()
    print("\nDone.")
