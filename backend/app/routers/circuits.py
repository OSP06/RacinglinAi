"""
Circuit and telemetry visualization endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import Dict, List
import logging

from app.core.database import get_db
from app.models.database import Race
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


def _get_fastf1():
    """Lazy-import FastF1 and enable cache."""
    import fastf1
    fastf1.Cache.enable_cache(settings.FASTF1_CACHE_DIR)
    return fastf1


@router.get("/{race_id}/layout")
async def get_circuit_layout(
    race_id: int,
    db: Session = Depends(get_db),
) -> Dict:
    """
    Get circuit layout with speed-coloured coordinates from FastF1 telemetry.
    The race's Season is eagerly loaded to avoid DetachedInstanceError.
    """
    # Eager-load the season so we can read .year outside the lazy-load window
    race = (
        db.query(Race)
        .options(joinedload(Race.season))
        .filter(Race.id == race_id)
        .first()
    )
    if not race:
        raise HTTPException(status_code=404, detail="Race not found")

    season_year: int = race.season.year

    fastf1 = _get_fastf1()

    try:
        session = fastf1.get_session(season_year, race.grand_prix, "R")
        logger.info(f"Loading telemetry for {race.grand_prix} {season_year}")
        session.load(telemetry=True, laps=False, weather=False)

        fastest_lap = session.laps.pick_fastest()
        if fastest_lap is None or fastest_lap.telemetry.empty:
            raise HTTPException(
                status_code=404,
                detail="No telemetry data available for this race",
            )

        telemetry = fastest_lap.get_telemetry()

        coordinates = []
        for _, point in telemetry.iterrows():
            coordinates.append(
                {
                    "x": float(point["X"]),
                    "y": float(point["Y"]),
                    "speed": float(point["Speed"]) if "Speed" in point else 0.0,
                    "distance": float(point["Distance"]) if "Distance" in point else 0.0,
                }
            )

        return {
            "circuit_name": race.circuit_name,
            "circuit_country": race.circuit_country,
            "track_length_km": race.track_length_km,
            "altitude_m": race.altitude_m,
            "coordinates": coordinates,
            "fastest_lap_time": str(fastest_lap["LapTime"]) if "LapTime" in fastest_lap else None,
            "fastest_lap_driver": str(fastest_lap["Driver"]) if "Driver" in fastest_lap else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading circuit layout: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load circuit layout: {e}")


@router.get("/list")
async def list_circuits(
    season: int = None,
    db: Session = Depends(get_db),
) -> List[Dict]:
    query = db.query(Race).options(joinedload(Race.season)).distinct(Race.circuit_name)

    if season:
        # Filter through the joined season
        from app.models.database import Season
        query = query.join(Race.season).filter(Season.year == season)

    circuits = query.all()

    return [
        {
            "circuit_name": r.circuit_name,
            "circuit_short": r.circuit_short,
            "circuit_country": r.circuit_country,
            "track_length_km": r.track_length_km,
            "altitude_m": r.altitude_m,
            "circuit_type": r.circuit_type,
        }
        for r in circuits
    ]
