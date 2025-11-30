"""
Telemetry data API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import fastf1
from typing import Dict, List, Optional
import logging

from app.core.database import get_db
from app.models.database import Race, Lap
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# Enable FastF1 cache
fastf1.Cache.enable_cache(settings.FASTF1_CACHE_DIR)


@router.get("/{race_id}/driver/{driver}/lap/{lap_number}")
async def get_lap_telemetry(
    race_id: int,
    driver: str,
    lap_number: int,
    db: Session = Depends(get_db)
) -> Dict:
    """
    Get detailed telemetry for a specific lap

    Returns high-frequency telemetry data (speed, throttle, brake, etc.)

    Args:
        race_id: Race ID
        driver: Driver code (e.g., 'VER', 'HAM')
        lap_number: Lap number
    """
    # Get race from database
    race = db.query(Race).filter(Race.id == race_id).first()
    if not race:
        raise HTTPException(status_code=404, detail="Race not found")

    try:
        # Load session from FastF1
        session = fastf1.get_session(
            race.season.year,
            race.grand_prix,
            'R'
        )

        logger.info(f"Loading telemetry for {driver} lap {lap_number}")
        session.load(telemetry=True)

        # Get specific lap
        lap = session.laps.pick_driver(driver.upper()).pick_lap(lap_number)

        if lap is None or lap.telemetry.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No telemetry data available for {driver} lap {lap_number}"
            )

        # Get telemetry
        telemetry = lap.get_telemetry()

        # Convert to list of dictionaries
        telemetry_data = []
        for _, point in telemetry.iterrows():
            telemetry_data.append({
                'time': float(point['Time'].total_seconds()) if 'Time' in point else 0,
                'distance': float(point['Distance']) if 'Distance' in point else 0,
                'speed': float(point['Speed']) if 'Speed' in point else 0,
                'rpm': float(point['RPM']) if 'RPM' in point else 0,
                'gear': int(point['nGear']) if 'nGear' in point else 0,
                'throttle': float(point['Throttle']) if 'Throttle' in point else 0,
                'brake': bool(point['Brake']) if 'Brake' in point else False,
                'drs': int(point['DRS']) if 'DRS' in point else 0,
                'x': float(point['X']) if 'X' in point else 0,
                'y': float(point['Y']) if 'Y' in point else 0,
            })

        return {
            'driver': driver.upper(),
            'lap_number': lap_number,
            'lap_time': str(lap['LapTime']) if 'LapTime' in lap else None,
            'compound': str(lap['Compound']) if 'Compound' in lap else None,
            'tyre_life': int(lap['TyreLife']) if 'TyreLife' in lap else 0,
            'telemetry': telemetry_data
        }

    except Exception as e:
        logger.error(f"Error loading telemetry: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load telemetry: {str(e)}"
        )


@router.get("/{race_id}/comparison")
async def compare_drivers_telemetry(
    race_id: int,
    driver1: str,
    driver2: str,
    lap_number: Optional[int] = None,
    db: Session = Depends(get_db)
) -> Dict:
    """
    Compare telemetry between two drivers

    Args:
        race_id: Race ID
        driver1: First driver code
        driver2: Second driver code
        lap_number: Optional specific lap, or uses fastest lap if not provided
    """
    # Get race
    race = db.query(Race).filter(Race.id == race_id).first()
    if not race:
        raise HTTPException(status_code=404, detail="Race not found")

    try:
        # Load session
        session = fastf1.get_session(
            race.season.year,
            race.grand_prix,
            'R'
        )

        session.load(telemetry=True)

        # Get laps for comparison
        if lap_number:
            lap1 = session.laps.pick_driver(driver1.upper()).pick_lap(lap_number)
            lap2 = session.laps.pick_driver(driver2.upper()).pick_lap(lap_number)
        else:
            # Use fastest laps
            lap1 = session.laps.pick_driver(driver1.upper()).pick_fastest()
            lap2 = session.laps.pick_driver(driver2.upper()).pick_fastest()

        if lap1 is None or lap2 is None:
            raise HTTPException(status_code=404, detail="Lap data not available")

        # Get telemetry
        tel1 = lap1.get_telemetry()
        tel2 = lap2.get_telemetry()

        # Compare key metrics
        comparison = {
            'driver1': {
                'driver': driver1.upper(),
                'lap_time': str(lap1['LapTime']),
                'max_speed': float(tel1['Speed'].max()) if 'Speed' in tel1 else 0,
                'avg_speed': float(tel1['Speed'].mean()) if 'Speed' in tel1 else 0,
            },
            'driver2': {
                'driver': driver2.upper(),
                'lap_time': str(lap2['LapTime']),
                'max_speed': float(tel2['Speed'].max()) if 'Speed' in tel2 else 0,
                'avg_speed': float(tel2['Speed'].mean()) if 'Speed' in tel2 else 0,
            },
            'delta': {
                'lap_time_diff': float((lap1['LapTime'] - lap2['LapTime']).total_seconds()),
                'max_speed_diff': float(tel1['Speed'].max() - tel2['Speed'].max()) if 'Speed' in tel1 else 0,
            }
        }

        return comparison

    except Exception as e:
        logger.error(f"Error comparing telemetry: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compare telemetry: {str(e)}"
        )
