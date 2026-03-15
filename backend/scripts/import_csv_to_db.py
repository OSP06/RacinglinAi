"""
CSV to Database Migration Script
Imports existing race data CSVs into PostgreSQL database.

Column mapping covers both the original Streamlit CSV schema and any
enriched columns that may exist in newer exports.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging
from pathlib import Path

from app.models.database import (
    Base, Season, Race, Lap, WeatherData,
    CompoundType, StintType, TrackStatusType,
)
from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
#  Helpers                                                                     #
# --------------------------------------------------------------------------- #

def _safe_float(row, *keys) -> float | None:
    for k in keys:
        v = row.get(k)
        if v is not None and not (isinstance(v, float) and np.isnan(v)):
            try:
                return float(v)
            except (ValueError, TypeError):
                pass
    return None


def _safe_int(row, *keys) -> int | None:
    v = _safe_float(row, *keys)
    return int(v) if v is not None else None


def _safe_bool(row, *keys, default=False) -> bool:
    for k in keys:
        v = row.get(k)
        if v is not None and not (isinstance(v, float) and np.isnan(v)):
            if isinstance(v, bool):
                return v
            if isinstance(v, (int, float)):
                return bool(v)
            if str(v).lower() in ("true", "1", "yes"):
                return True
            if str(v).lower() in ("false", "0", "no"):
                return False
    return default


def _safe_str(row, *keys) -> str | None:
    for k in keys:
        v = row.get(k)
        if v is not None and not (isinstance(v, float) and np.isnan(v)):
            s = str(v).strip()
            if s and s.lower() not in ("nan", "none", "nat"):
                return s
    return None


def _map_compound(value: str | None) -> CompoundType:
    if value is None:
        return CompoundType.MEDIUM
    v = str(value).strip().upper()
    return CompoundType.__members__.get(v, CompoundType.MEDIUM)


def _map_stint_type(value: str | None) -> StintType:
    if value is None:
        return StintType.MID
    v = str(value).strip().upper()
    return StintType.__members__.get(v, StintType.MID)


def _map_track_status(row: dict) -> TrackStatusType:
    if _safe_bool(row, "IsSC", "is_sc"):
        return TrackStatusType.SC
    if _safe_bool(row, "IsVSC", "is_vsc"):
        return TrackStatusType.VSC
    if _safe_bool(row, "IsRedFlag", "is_red_flag"):
        return TrackStatusType.RED
    return TrackStatusType.GREEN


# --------------------------------------------------------------------------- #
#  Core import                                                                 #
# --------------------------------------------------------------------------- #

def create_database_tables(engine):
    logger.info("Creating / verifying database tables …")
    Base.metadata.create_all(bind=engine)
    logger.info("Tables ready")


def import_season_data(csv_path: str, session, season_year: int):
    logger.info(f"Importing {csv_path}")
    df = pd.read_csv(csv_path, low_memory=False)
    # Normalise column names to strip accidental whitespace
    df.columns = [c.strip() for c in df.columns]
    logger.info(f"  {len(df)} rows, columns: {list(df.columns)[:10]} …")

    # Get / create season
    season = session.query(Season).filter(Season.year == season_year).first()
    if not season:
        season = Season(year=season_year)
        session.add(season)
        session.commit()

    # Group by grand prix
    gp_col = next((c for c in df.columns if c.lower() in ("grandprix", "grand_prix")), None)
    slug_col = next((c for c in df.columns if c.lower() in ("gp_slug", "gpslug")), None)

    if gp_col is None:
        logger.error("Cannot find GrandPrix column — skipping file")
        return

    group_cols = [gp_col]
    if slug_col:
        group_cols.append(slug_col)

    race_count = 0
    lap_count = 0

    for group_key, race_data in df.groupby(group_cols):
        grand_prix = group_key if isinstance(group_key, str) else group_key[0]
        gp_slug = (group_key[1] if len(group_key) > 1 else grand_prix).lower().replace(" ", "_")

        first = race_data.iloc[0].to_dict()

        existing = session.query(Race).filter(
            Race.season_id == season.id,
            Race.gp_slug == gp_slug,
        ).first()

        if existing:
            logger.info(f"  [{season_year}] {grand_prix} already imported — skipping")
            continue

        # Parse event date
        raw_date = _safe_str(first, "EventDate", "event_date", "Date", "date")
        try:
            event_date = pd.to_datetime(raw_date)
        except Exception:
            event_date = datetime(season_year, 1, 1)

        race = Race(
            season_id=season.id,
            grand_prix=grand_prix,
            gp_slug=gp_slug,
            event_date=event_date,
            round_number=race_count + 1,
            circuit_name=_safe_str(first, "CircuitName", "circuit_name") or grand_prix,
            circuit_short=_safe_str(first, "CircuitShort", "circuit_short"),
            circuit_country=_safe_str(first, "CircuitCountry", "circuit_country"),
            track_length_km=_safe_float(first, "TrackLengthKM", "track_length_km"),
            altitude_m=_safe_float(first, "AltitudeM", "altitude_m"),
            circuit_type=_safe_str(first, "CircuitType", "circuit_type"),
        )
        session.add(race)
        session.flush()
        race_count += 1

        for _, row_series in race_data.iterrows():
            row = row_series.to_dict()

            lap = Lap(
                race_id=race.id,
                driver=(_safe_str(row, "Driver", "driver") or "UNK").upper(),
                driver_number=_safe_int(row, "DriverNumber", "driver_number"),
                team=_safe_str(row, "Team", "team") or "Unknown",
                lap_number=_safe_int(row, "LapNumber", "lap_number") or 0,
                lap_time=_safe_str(row, "LapTime", "lap_time"),
                lap_time_seconds=_safe_float(row, "LapTimeSeconds", "lap_time_seconds"),
                lap_start_time=_safe_str(row, "LapStartTime", "lap_start_time"),
                # Sector times
                sector1_time=_safe_str(row, "Sector1Time", "sector1_time"),
                sector1_time_seconds=_safe_float(row, "Sector1TimeSeconds", "sector1_time_seconds"),
                sector2_time=_safe_str(row, "Sector2Time", "sector2_time"),
                sector2_time_seconds=_safe_float(row, "Sector2TimeSeconds", "sector2_time_seconds"),
                sector3_time=_safe_str(row, "Sector3Time", "sector3_time"),
                sector3_time_seconds=_safe_float(row, "Sector3TimeSeconds", "sector3_time_seconds"),
                # Sector percentages
                sector1_pct=_safe_float(row, "Sector1Pct", "sector1_pct"),
                sector2_pct=_safe_float(row, "Sector2Pct", "sector2_pct"),
                sector3_pct=_safe_float(row, "Sector3Pct", "sector3_pct"),
                # Speed traps
                speed_i1=_safe_float(row, "SpeedI1", "speed_i1"),
                speed_i2=_safe_float(row, "SpeedI2", "speed_i2"),
                speed_fl=_safe_float(row, "SpeedFL", "speed_fl"),
                speed_st=_safe_float(row, "SpeedST", "speed_st"),
                # Tyre
                compound=_map_compound(_safe_str(row, "Compound", "compound")),
                tyre_life=_safe_int(row, "TyreLife", "tyre_life"),
                is_fresh_tyre=_safe_bool(row, "FreshTyre", "is_fresh_tyre"),
                # Stint
                stint=_safe_int(row, "Stint", "stint"),
                stint_type=_map_stint_type(_safe_str(row, "StintType", "stint_type")),
                stint_length=_safe_int(row, "StintLength", "stint_length"),
                # Pit
                is_pit_lap=_safe_bool(row, "PitLap", "is_pit_lap"),
                pit_in_time=_safe_str(row, "PitInTime", "pit_in_time"),
                pit_out_time=_safe_str(row, "PitOutTime", "pit_out_time"),
                pit_duration=_safe_float(row, "PitDuration", "pit_duration"),
                # Position / status
                position=_safe_int(row, "Position", "position"),
                track_status=_map_track_status(row),
                # Analytical
                best_sector=_safe_int(row, "BestSector", "best_sector"),
                delta_to_fastest_lap=_safe_float(row, "DeltaToFastestLap", "delta_to_fastest_lap"),
                avg_lap_time=_safe_float(row, "AvgLapTime", "avg_lap_time"),
                # Flags
                is_personal_best=_safe_bool(row, "IsPersonalBest", "is_personal_best"),
                is_valid_lap=_safe_bool(row, "IsValidLap", "is_valid_lap", default=True),
                is_accurate=_safe_bool(row, "IsAccurate", "is_accurate", default=True),
                is_wet_lap=_safe_bool(row, "IsWetLap", "is_wet_lap"),
                is_dry_lap=_safe_bool(row, "IsDryLap", "is_dry_lap", default=True),
                is_sc=_safe_bool(row, "IsSC", "is_sc"),
                is_vsc=_safe_bool(row, "IsVSC", "is_vsc"),
                is_red_flag=_safe_bool(row, "IsRedFlag", "is_red_flag"),
                is_dnf=_safe_bool(row, "IsDNF", "is_dnf"),
            )
            session.add(lap)
            lap_count += 1

            if lap_count % 2000 == 0:
                session.commit()
                logger.info(f"  … committed {lap_count} laps")

        session.commit()
        logger.info(f"  [{season_year}] {grand_prix}: {len(race_data)} laps imported")

    logger.info(f"Season {season_year}: {race_count} races, {lap_count} laps total")


def main():
    logger.info("Starting CSV → DB import")
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    create_database_tables(engine)
    session = SessionLocal()

    try:
        data_dir = Path(__file__).parent.parent.parent / "data" / "processed"
        logger.info(f"CSV directory: {data_dir}")

        for year in range(2018, 2027):   # covers up to 2026 season
            csv_file = data_dir / f"all_races_combined_{year}.csv"
            if csv_file.exists():
                try:
                    import_season_data(str(csv_file), session, year)
                except Exception as e:
                    logger.error(f"Error importing {year}: {e}")
                    session.rollback()
            else:
                logger.warning(f"Not found: {csv_file}")

        logger.info("Import complete")
    except Exception as e:
        logger.error(f"Import failed: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
