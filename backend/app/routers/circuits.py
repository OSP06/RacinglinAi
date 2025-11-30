"""
Circuit and telemetry visualization endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import fastf1
from typing import Dict, List
import logging

from app.core.database import get_db
from app.models.database import Race
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# Enable FastF1 cache
fastf1.Cache.enable_cache(settings.FASTF1_CACHE_DIR)


@router.get("/{race_id}/layout")
async def get_circuit_layout(
    race_id: int,
    db: Session = Depends(get_db)
) -> Dict:
    """
    Get circuit layout data with telemetry coordinates

    Returns track coordinates and metadata for visualization

    Args:
        race_id: Race ID
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
            'R'  # Race session
        )

        logger.info(f"Loading telemetry for {race.grand_prix} {race.season.year}")
        session.load(telemetry=True, laps=False, weather=False)

        # Get fastest lap for track layout
        fastest_lap = session.laps.pick_fastest()

        if fastest_lap is None or fastest_lap.telemetry.empty:
            raise HTTPException(
                status_code=404,
                detail="No telemetry data available for this race"
            )

        # Get telemetry data
        telemetry = fastest_lap.get_telemetry()

        # Extract coordinates and speed
        coordinates = []
        for _, point in telemetry.iterrows():
            coordinates.append({
                'x': float(point['X']),
                'y': float(point['Y']),
                'speed': float(point['Speed']) if 'Speed' in point else 0,
                'distance': float(point['Distance']) if 'Distance' in point else 0
            })

        return {
            'circuit_name': race.circuit_name,
            'circuit_country': race.circuit_country,
            'track_length_km': race.track_length_km,
            'altitude_m': race.altitude_m,
            'coordinates': coordinates,
            'fastest_lap_time': str(fastest_lap['LapTime']) if 'LapTime' in fastest_lap else None,
            'fastest_lap_driver': str(fastest_lap['Driver']) if 'Driver' in fastest_lap else None
        }

    except Exception as e:
        logger.error(f"Error loading circuit layout: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load circuit layout: {str(e)}"
        )


@router.get("/list")
async def list_circuits(
    season: int = None,
    db: Session = Depends(get_db)
) -> List[Dict]:
    """
    Get list of all circuits

    Args:
        season: Optional season filter
    """
    query = db.query(Race).distinct(Race.circuit_name)

    if season:
        query = query.join(Race.season).filter(Race.season.has(year=season))

    circuits = query.all()

    return [
        {
            'circuit_name': race.circuit_name,
            'circuit_short': race.circuit_short,
            'circuit_country': race.circuit_country,
            'track_length_km': race.track_length_km,
            'altitude_m': race.altitude_m,
            'circuit_type': race.circuit_type
        }
        for race in circuits
    ]
