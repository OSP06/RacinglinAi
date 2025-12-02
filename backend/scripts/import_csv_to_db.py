"""
CSV to Database Migration Script
Imports existing race data CSVs into PostgreSQL database
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

from app.models.database import Base, Season, Race, Lap, WeatherData, CompoundType, StintType, TrackStatusType
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_database_tables(engine):
    """Create all database tables"""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tables created successfully")


def import_season_data(csv_path: str, session, season_year: int):
    """
    Import data from a season CSV file

    Args:
        csv_path: Path to CSV file
        session: Database session
        season_year: Season year
    """
    logger.info(f"Importing data from {csv_path}")

    # Read CSV
    df = pd.read_csv(csv_path)
    logger.info(f"Loaded {len(df)} rows from CSV")

    # Get or create season
    season = session.query(Season).filter(Season.year == season_year).first()
    if not season:
        season = Season(year=season_year)
        session.add(season)
        session.commit()
        logger.info(f"Created season {season_year}")

    # Group by race
    races = df.groupby(['GrandPrix', 'GP_Slug'])

    race_count = 0
    lap_count = 0

    for (grand_prix, gp_slug), race_data in races:
        logger.info(f"Processing race: {grand_prix}")

        # Get race details from first row
        first_row = race_data.iloc[0]

        # Check if race already exists
        existing_race = session.query(Race).filter(
            Race.season_id == season.id,
            Race.gp_slug == gp_slug.lower()
        ).first()

        if existing_race:
            logger.info(f"Race {grand_prix} already exists, skipping...")
            continue

        # Create race
        race = Race(
            season_id=season.id,
            grand_prix=grand_prix,
            gp_slug=gp_slug.lower(),
            event_date=pd.to_datetime(first_row['EventDate']),
            round_number=race_count + 1,
            circuit_name=first_row['CircuitName'] if 'CircuitName' in first_row else grand_prix,
            circuit_short=first_row['CircuitShort'] if 'CircuitShort' in first_row else None,
            circuit_country=first_row['CircuitCountry'] if 'CircuitCountry' in first_row else None,
            track_length_km=first_row['TrackLengthKM'] if 'TrackLengthKM' in first_row else None,
            altitude_m=first_row['AltitudeM'] if 'AltitudeM' in first_row else None,
            circuit_type=first_row['CircuitType'] if 'CircuitType' in first_row else None
        )

        session.add(race)
        session.flush()  # Get race ID
        race_count += 1

        # Import laps
        for _, row in race_data.iterrows():
            # Map compound
            compound_str = str(row['Compound']).upper() if 'Compound' in row and pd.notna(row['Compound']) else 'MEDIUM'
            try:
                compound = CompoundType[compound_str]
            except KeyError:
                compound = CompoundType.MEDIUM

            # Map stint type
            stint_type_str = str(row['StintType']).upper() if 'StintType' in row and pd.notna(row['StintType']) else 'MID'
            try:
                stint_type = StintType[stint_type_str]
            except KeyError:
                stint_type = StintType.MID

            # Map track status
            track_status_str = 'GREEN'
            if 'IsSC' in row and row['IsSC']:
                track_status_str = 'SC'
            elif 'IsVSC' in row and row['IsVSC']:
                track_status_str = 'VSC'
            elif 'IsRedFlag' in row and row['IsRedFlag']:
                track_status_str = 'RED'

            try:
                track_status = TrackStatusType[track_status_str]
            except KeyError:
                track_status = TrackStatusType.GREEN

            # Create lap
            lap = Lap(
                race_id=race.id,
                driver=str(row['Driver']).upper(),
                driver_number=int(row['DriverNumber']) if 'DriverNumber' in row and pd.notna(row['DriverNumber']) else None,
                team=str(row['Team']),
                lap_number=int(row['LapNumber']),
                lap_time=str(row['LapTime']) if 'LapTime' in row and pd.notna(row['LapTime']) else None,
                lap_time_seconds=float(row['LapTimeSeconds']) if 'LapTimeSeconds' in row and pd.notna(row['LapTimeSeconds']) else None,
                lap_start_time=str(row['LapStartTime']) if 'LapStartTime' in row and pd.notna(row['LapStartTime']) else None,
                sector1_time=str(row['Sector1Time']) if 'Sector1Time' in row and pd.notna(row['Sector1Time']) else None,
                sector1_time_seconds=float(row['Sector1TimeSeconds']) if 'Sector1TimeSeconds' in row and pd.notna(row['Sector1TimeSeconds']) else None,
                sector2_time=str(row['Sector2Time']) if 'Sector2Time' in row and pd.notna(row['Sector2Time']) else None,
                sector2_time_seconds=float(row['Sector2TimeSeconds']) if 'Sector2TimeSeconds' in row and pd.notna(row['Sector2TimeSeconds']) else None,
                sector3_time=str(row['Sector3Time']) if 'Sector3Time' in row and pd.notna(row['Sector3Time']) else None,
                sector3_time_seconds=float(row['Sector3TimeSeconds']) if 'Sector3TimeSeconds' in row and pd.notna(row['Sector3TimeSeconds']) else None,
                sector1_pct=float(row['Sector1Pct']) if 'Sector1Pct' in row and pd.notna(row['Sector1Pct']) else None,
                sector2_pct=float(row['Sector2Pct']) if 'Sector2Pct' in row and pd.notna(row['Sector2Pct']) else None,
                sector3_pct=float(row['Sector3Pct']) if 'Sector3Pct' in row and pd.notna(row['Sector3Pct']) else None,
                speed_fl=float(row['SpeedFL']) if 'SpeedFL' in row and pd.notna(row['SpeedFL']) else None,
                compound=compound,
                tyre_life=int(row['TyreLife']) if 'TyreLife' in row and pd.notna(row['TyreLife']) else None,
                is_fresh_tyre=bool(row['FreshTyre']) if 'FreshTyre' in row and pd.notna(row['FreshTyre']) else False,
                stint=int(row['Stint']) if 'Stint' in row and pd.notna(row['Stint']) else None,
                stint_type=stint_type,
                stint_length=int(row['StintLength']) if 'StintLength' in row and pd.notna(row['StintLength']) else None,
                is_pit_lap=bool(row['PitLap']) if 'PitLap' in row and pd.notna(row['PitLap']) else False,
                pit_duration=float(row['PitDuration']) if 'PitDuration' in row and pd.notna(row['PitDuration']) else None,
                position=int(row['Position']) if 'Position' in row and pd.notna(row['Position']) else None,
                track_status=track_status,
                best_sector=int(row['BestSector']) if 'BestSector' in row and pd.notna(row['BestSector']) else None,
                delta_to_fastest_lap=float(row['DeltaToFastestLap']) if 'DeltaToFastestLap' in row and pd.notna(row['DeltaToFastestLap']) else None,
                is_personal_best=bool(row['IsPersonalBest']) if 'IsPersonalBest' in row and pd.notna(row['IsPersonalBest']) else False,
                is_valid_lap=bool(row['IsValidLap']) if 'IsValidLap' in row and pd.notna(row['IsValidLap']) else True,
                is_accurate=bool(row['IsAccurate']) if 'IsAccurate' in row and pd.notna(row['IsAccurate']) else True,
                is_wet_lap=bool(row['IsWetLap']) if 'IsWetLap' in row and pd.notna(row['IsWetLap']) else False,
                is_dry_lap=bool(row['IsDryLap']) if 'IsDryLap' in row and pd.notna(row['IsDryLap']) else True,
                is_sc=bool(row['IsSC']) if 'IsSC' in row and pd.notna(row['IsSC']) else False,
                is_vsc=bool(row['IsVSC']) if 'IsVSC' in row and pd.notna(row['IsVSC']) else False,
                is_red_flag=bool(row['IsRedFlag']) if 'IsRedFlag' in row and pd.notna(row['IsRedFlag']) else False,
                is_dnf=bool(row['IsDNF']) if 'IsDNF' in row and pd.notna(row['IsDNF']) else False
            )

            session.add(lap)
            lap_count += 1

            # Commit in batches
            if lap_count % 1000 == 0:
                session.commit()
                logger.info(f"Committed {lap_count} laps...")

        session.commit()
        logger.info(f"Race {grand_prix} imported with {len(race_data)} laps")

    logger.info(f"Season {season_year} complete: {race_count} races, {lap_count} laps")


def main():
    """Main import function"""
    logger.info("Starting CSV to Database import...")

    # Create database connection
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create tables
    create_database_tables(engine)

    # Create session
    session = SessionLocal()

    try:
        # Path to CSV files (relative to backend/scripts directory)
        data_dir = Path(__file__).parent.parent.parent / "data" / "processed"

        logger.info(f"Looking for CSV files in {data_dir}")

        # Import each season
        for year in range(2018, 2026):  # 2018-2025
            csv_file = data_dir / f"all_races_combined_{year}.csv"

            if csv_file.exists():
                try:
                    import_season_data(str(csv_file), session, year)
                except Exception as e:
                    logger.error(f"Error importing {year}: {str(e)}")
                    session.rollback()
            else:
                logger.warning(f"CSV file not found: {csv_file}")

        logger.info("Import completed successfully!")

    except Exception as e:
        logger.error(f"Import failed: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
