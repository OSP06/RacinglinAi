"""
Circuit and telemetry visualization endpoints

Circuit layout coordinates are loaded from FastF1 in a background thread
and cached in memory. The first request returns 202 (loading); subsequent
requests return 200 with cached data. This avoids Render's ~90s proxy timeout.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import Dict, List, Optional
import threading
import logging

from app.core.database import get_db
from app.models.database import Race
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
#  In-memory circuit cache                                                     #
# --------------------------------------------------------------------------- #

_circuit_cache: Dict[int, Dict] = {}          # race_id → full response dict
_circuit_loading: Dict[int, bool] = {}        # race_id → True while loading
_circuit_error: Dict[int, str] = {}           # race_id → error message
_cache_lock = threading.Lock()


def _get_fastf1():
    import fastf1
    fastf1.Cache.enable_cache(settings.FASTF1_CACHE_DIR)
    return fastf1


def _load_circuit_background(race_id: int, season_year: int, grand_prix: str,
                              circuit_name: str, circuit_country: str,
                              track_length_km: Optional[float], altitude_m: Optional[float]):
    """Runs in a daemon thread. Loads FastF1 data and populates _circuit_cache."""
    logger.info(f"[circuit-loader] Starting load for {grand_prix} {season_year}")
    try:
        fastf1 = _get_fastf1()
        session = fastf1.get_session(season_year, grand_prix, "R")

        # Load laps + telemetry — takes 30-120s on first run (cached afterward)
        session.load(laps=True, telemetry=True, weather=False)

        fastest_lap = session.laps.pick_fastest()
        if fastest_lap is None:
            raise ValueError("No fastest lap found in session")

        telemetry = fastest_lap.get_telemetry()
        if telemetry is None or telemetry.empty:
            raise ValueError("Telemetry data is empty")

        coordinates = []
        for _, point in telemetry.iterrows():
            coordinates.append({
                "x": float(point["X"]) if "X" in point.index else 0.0,
                "y": float(point["Y"]) if "Y" in point.index else 0.0,
                "speed": float(point["Speed"]) if "Speed" in point.index else 0.0,
                "distance": float(point["Distance"]) if "Distance" in point.index else 0.0,
            })

        result = {
            "circuit_name": circuit_name,
            "circuit_country": circuit_country,
            "track_length_km": track_length_km,
            "altitude_m": altitude_m,
            "coordinates": coordinates,
            "fastest_lap_time": str(fastest_lap["LapTime"]) if "LapTime" in fastest_lap.index else None,
            "fastest_lap_driver": str(fastest_lap["Driver"]) if "Driver" in fastest_lap.index else None,
        }

        with _cache_lock:
            _circuit_cache[race_id] = result
            _circuit_loading[race_id] = False
            _circuit_error.pop(race_id, None)

        logger.info(f"[circuit-loader] Done — {len(coordinates)} points for {grand_prix} {season_year}")

    except Exception as e:
        logger.error(f"[circuit-loader] Failed for {grand_prix} {season_year}: {e}")
        with _cache_lock:
            _circuit_loading[race_id] = False
            _circuit_error[race_id] = str(e)


# --------------------------------------------------------------------------- #
#  Endpoints                                                                   #
# --------------------------------------------------------------------------- #

@router.get("/{race_id}/layout")
async def get_circuit_layout(
    race_id: int,
    db: Session = Depends(get_db),
) -> Dict:
    """
    Returns circuit layout coordinates.
    - 200: data ready (from cache)
    - 202: still loading (try again in 15s)
    - 500: permanent error
    """
    with _cache_lock:
        if race_id in _circuit_cache:
            return _circuit_cache[race_id]

        if _circuit_loading.get(race_id):
            raise HTTPException(status_code=202, detail="Circuit data is loading — retry in 15s")

        if race_id in _circuit_error:
            err = _circuit_error[race_id]
            raise HTTPException(status_code=500, detail=f"Failed to load circuit: {err}")

    # Not cached, not loading → look up race and start background thread
    race = (
        db.query(Race)
        .options(joinedload(Race.season))
        .filter(Race.id == race_id)
        .first()
    )
    if not race:
        raise HTTPException(status_code=404, detail="Race not found")

    with _cache_lock:
        # Double-check after lock (another request may have started it)
        if race_id in _circuit_cache:
            return _circuit_cache[race_id]
        if _circuit_loading.get(race_id):
            raise HTTPException(status_code=202, detail="Circuit data is loading — retry in 15s")

        _circuit_loading[race_id] = True

    t = threading.Thread(
        target=_load_circuit_background,
        args=(
            race_id,
            race.season.year,
            race.grand_prix,
            race.circuit_name,
            race.circuit_country,
            race.track_length_km,
            race.altitude_m,
        ),
        daemon=True,
    )
    t.start()
    logger.info(f"Started background load for race {race_id} ({race.grand_prix})")
    raise HTTPException(status_code=202, detail="Circuit data is loading — retry in 15s")


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
