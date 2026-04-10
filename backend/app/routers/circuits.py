"""
Circuit and telemetry visualization endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import Dict, List
import asyncio
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


def _load_circuit_sync(season_year: int, grand_prix: str) -> List[Dict]:
    """
    Synchronous FastF1 load — runs in a thread executor.
    Returns list of coordinate dicts {x, y, speed, distance}.
    """
    fastf1 = _get_fastf1()

    session = fastf1.get_session(season_year, grand_prix, "R")
    logger.info(f"Loading laps for {grand_prix} {season_year}")

    # Phase 1: load laps only (fast, ~2-5s) to find the fastest lap driver
    session.load(laps=True, telemetry=False, weather=False)

    fastest_lap = session.laps.pick_fastest()
    if fastest_lap is None:
        raise ValueError("No fastest lap found")

    # Phase 2: reload with telemetry so we can call get_telemetry()
    logger.info(f"Loading telemetry for {grand_prix} {season_year}")
    session.load(laps=True, telemetry=True, weather=False)

    # Re-fetch fastest lap from the fully loaded session
    fastest_lap = session.laps.pick_fastest()
    if fastest_lap is None:
        raise ValueError("No fastest lap after telemetry load")

    telemetry = fastest_lap.get_telemetry()
    if telemetry is None or telemetry.empty:
        raise ValueError("Telemetry is empty")

    coordinates = []
    for _, point in telemetry.iterrows():
        coordinates.append({
            "x": float(point["X"]) if "X" in point.index else 0.0,
            "y": float(point["Y"]) if "Y" in point.index else 0.0,
            "speed": float(point["Speed"]) if "Speed" in point.index else 0.0,
            "distance": float(point["Distance"]) if "Distance" in point.index else 0.0,
        })

    driver = str(fastest_lap["Driver"]) if "Driver" in fastest_lap.index else None
    lap_time = str(fastest_lap["LapTime"]) if "LapTime" in fastest_lap.index else None
    return coordinates, driver, lap_time


@router.get("/{race_id}/layout")
async def get_circuit_layout(
    race_id: int,
    db: Session = Depends(get_db),
) -> Dict:
    """
    Get circuit layout with speed-coloured coordinates from FastF1 telemetry.
    FastF1 loading runs in a thread executor so it does not block the event loop.
    Times out after 120 seconds and returns 503 (retry after cache is warm).
    """
    race = (
        db.query(Race)
        .options(joinedload(Race.season))
        .filter(Race.id == race_id)
        .first()
    )
    if not race:
        raise HTTPException(status_code=404, detail="Race not found")

    season_year: int = race.season.year

    loop = asyncio.get_event_loop()
    try:
        coordinates, fastest_driver, lap_time = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                _load_circuit_sync,
                season_year,
                race.grand_prix,
            ),
            timeout=120.0,
        )
    except asyncio.TimeoutError:
        logger.warning(f"Circuit layout timed out for {race.grand_prix} {season_year}")
        raise HTTPException(
            status_code=503,
            detail="Circuit data is loading. First load takes ~30s — please try again.",
        )
    except Exception as e:
        logger.error(f"Error loading circuit layout for {race.grand_prix}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load circuit layout: {e}")

    return {
        "circuit_name": race.circuit_name,
        "circuit_country": race.circuit_country,
        "track_length_km": race.track_length_km,
        "altitude_m": race.altitude_m,
        "coordinates": coordinates,
        "fastest_lap_time": lap_time,
        "fastest_lap_driver": fastest_driver,
    }


@router.get("/list")
async def list_circuits(
    season: int = None,
    db: Session = Depends(get_db),
) -> List[Dict]:
    query = db.query(Race).options(joinedload(Race.season)).distinct(Race.circuit_name)

    if season:
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
