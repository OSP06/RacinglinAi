"""
Telemetry data API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import Dict, List, Optional
import logging

from app.core.database import get_db
from app.models.database import Race, Lap
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


def _get_fastf1():
    import fastf1
    fastf1.Cache.enable_cache(settings.FASTF1_CACHE_DIR)
    return fastf1


def _get_race(race_id: int, db: Session) -> Race:
    race = (
        db.query(Race)
        .options(joinedload(Race.season))
        .filter(Race.id == race_id)
        .first()
    )
    if not race:
        raise HTTPException(status_code=404, detail="Race not found")
    return race


@router.get("/{race_id}/driver/{driver}/lap/{lap_number}")
async def get_lap_telemetry(
    race_id: int,
    driver: str,
    lap_number: int,
    db: Session = Depends(get_db),
) -> Dict:
    race = _get_race(race_id, db)
    fastf1 = _get_fastf1()

    try:
        session = fastf1.get_session(race.season.year, race.grand_prix, "R")
        logger.info(f"Loading telemetry for {driver} lap {lap_number}")
        session.load(telemetry=True)

        laps = session.laps.pick_driver(driver.upper())
        lap = laps[laps["LapNumber"] == lap_number]

        if lap is None or lap.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No telemetry for {driver} lap {lap_number}",
            )

        lap_row = lap.iloc[0]
        telemetry = lap_row.get_telemetry()

        telemetry_data = [
            {
                "time": float(p["Time"].total_seconds()) if "Time" in p else 0.0,
                "distance": float(p["Distance"]) if "Distance" in p else 0.0,
                "speed": float(p["Speed"]) if "Speed" in p else 0.0,
                "rpm": float(p["RPM"]) if "RPM" in p else 0.0,
                "gear": int(p["nGear"]) if "nGear" in p else 0,
                "throttle": float(p["Throttle"]) if "Throttle" in p else 0.0,
                "brake": bool(p["Brake"]) if "Brake" in p else False,
                "drs": int(p["DRS"]) if "DRS" in p else 0,
                "x": float(p["X"]) if "X" in p else 0.0,
                "y": float(p["Y"]) if "Y" in p else 0.0,
            }
            for _, p in telemetry.iterrows()
        ]

        return {
            "driver": driver.upper(),
            "lap_number": lap_number,
            "lap_time": str(lap_row["LapTime"]) if "LapTime" in lap_row else None,
            "compound": str(lap_row["Compound"]) if "Compound" in lap_row else None,
            "tyre_life": int(lap_row["TyreLife"]) if "TyreLife" in lap_row else 0,
            "telemetry": telemetry_data,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading telemetry: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load telemetry: {e}")


@router.get("/{race_id}/comparison")
async def compare_drivers_telemetry(
    race_id: int,
    driver1: str,
    driver2: str,
    lap_number: Optional[int] = None,
    db: Session = Depends(get_db),
) -> Dict:
    race = _get_race(race_id, db)
    fastf1 = _get_fastf1()

    try:
        session = fastf1.get_session(race.season.year, race.grand_prix, "R")
        session.load(telemetry=True)

        if lap_number:
            def _pick(drv):
                laps = session.laps.pick_driver(drv.upper())
                return laps[laps["LapNumber"] == lap_number].iloc[0]
            lap1 = _pick(driver1)
            lap2 = _pick(driver2)
        else:
            lap1 = session.laps.pick_driver(driver1.upper()).pick_fastest()
            lap2 = session.laps.pick_driver(driver2.upper()).pick_fastest()

        if lap1 is None or lap2 is None:
            raise HTTPException(status_code=404, detail="Lap data not available")

        tel1 = lap1.get_telemetry()
        tel2 = lap2.get_telemetry()

        return {
            "driver1": {
                "driver": driver1.upper(),
                "lap_time": str(lap1["LapTime"]),
                "max_speed": float(tel1["Speed"].max()) if "Speed" in tel1 else 0.0,
                "avg_speed": float(tel1["Speed"].mean()) if "Speed" in tel1 else 0.0,
            },
            "driver2": {
                "driver": driver2.upper(),
                "lap_time": str(lap2["LapTime"]),
                "max_speed": float(tel2["Speed"].max()) if "Speed" in tel2 else 0.0,
                "avg_speed": float(tel2["Speed"].mean()) if "Speed" in tel2 else 0.0,
            },
            "delta": {
                "lap_time_diff": float((lap1["LapTime"] - lap2["LapTime"]).total_seconds()),
                "max_speed_diff": float(tel1["Speed"].max() - tel2["Speed"].max())
                if "Speed" in tel1
                else 0.0,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing telemetry: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to compare telemetry: {e}")
