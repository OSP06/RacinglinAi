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


def _telemetry_points(tel, max_points: int = 300) -> List[Dict]:
    """Return sampled coordinate + channel arrays for track overlay."""
    if tel is None or tel.empty:
        return []
    step = max(1, len(tel) // max_points)
    points = []
    for _, p in tel.iloc[::step].iterrows():
        points.append({
            "x":        float(p["X"])        if "X"        in p.index else 0.0,
            "y":        float(p["Y"])        if "Y"        in p.index else 0.0,
            "speed":    float(p["Speed"])    if "Speed"    in p.index else 0.0,
            "distance": float(p["Distance"]) if "Distance" in p.index else 0.0,
            "throttle": float(p["Throttle"]) if "Throttle" in p.index else 0.0,
            "brake":    bool(p["Brake"])     if "Brake"    in p.index else False,
        })
    return points


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
        lap_filtered = laps[laps["LapNumber"] == lap_number]

        if lap_filtered is None or lap_filtered.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No telemetry for {driver} lap {lap_number}",
            )

        lap_row = lap_filtered.iloc[0]
        telemetry = lap_row.get_telemetry()

        telemetry_data = [
            {
                "time":     float(p["Time"].total_seconds()) if "Time"     in p else 0.0,
                "distance": float(p["Distance"])             if "Distance" in p else 0.0,
                "speed":    float(p["Speed"])                if "Speed"    in p else 0.0,
                "rpm":      float(p["RPM"])                  if "RPM"      in p else 0.0,
                "gear":     int(p["nGear"])                  if "nGear"    in p else 0,
                "throttle": float(p["Throttle"])             if "Throttle" in p else 0.0,
                "brake":    bool(p["Brake"])                 if "Brake"    in p else False,
                "drs":      int(p["DRS"])                    if "DRS"      in p else 0,
                "x":        float(p["X"])                    if "X"        in p else 0.0,
                "y":        float(p["Y"])                    if "Y"        in p else 0.0,
            }
            for _, p in telemetry.iterrows()
        ]

        return {
            "driver":     driver.upper(),
            "lap_number": lap_number,
            "lap_time":   str(lap_row["LapTime"])  if "LapTime"  in lap_row else None,
            "compound":   str(lap_row["Compound"]) if "Compound" in lap_row else None,
            "tyre_life":  int(lap_row["TyreLife"]) if "TyreLife" in lap_row else 0,
            "telemetry":  telemetry_data,
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
            def _pick(drv: str):
                laps = session.laps.pick_driver(drv.upper())
                subset = laps[laps["LapNumber"] == lap_number]
                if subset.empty:
                    raise HTTPException(
                        status_code=404,
                        detail=f"No data for {drv} on lap {lap_number}",
                    )
                return subset.iloc[0]
            lap1 = _pick(driver1)
            lap2 = _pick(driver2)
        else:
            lap1 = session.laps.pick_driver(driver1.upper()).pick_fastest()
            lap2 = session.laps.pick_driver(driver2.upper()).pick_fastest()

        if lap1 is None or lap2 is None:
            raise HTTPException(status_code=404, detail="Lap data not available for one or both drivers")

        tel1 = lap1.get_telemetry()
        tel2 = lap2.get_telemetry()

        lap1_time = lap1["LapTime"] if "LapTime" in lap1.index else None
        lap2_time = lap2["LapTime"] if "LapTime" in lap2.index else None

        lap_time_diff = 0.0
        if lap1_time is not None and lap2_time is not None:
            try:
                lap_time_diff = float((lap1_time - lap2_time).total_seconds())
            except Exception:
                lap_time_diff = 0.0

        max_speed1 = float(tel1["Speed"].max()) if "Speed" in tel1.columns and not tel1.empty else 0.0
        max_speed2 = float(tel2["Speed"].max()) if "Speed" in tel2.columns and not tel2.empty else 0.0
        avg_speed1 = float(tel1["Speed"].mean()) if "Speed" in tel1.columns and not tel1.empty else 0.0
        avg_speed2 = float(tel2["Speed"].mean()) if "Speed" in tel2.columns and not tel2.empty else 0.0

        return {
            "driver1": {
                "driver":      driver1.upper(),
                "lap_time":    str(lap1_time) if lap1_time is not None else None,
                "max_speed":   max_speed1,
                "avg_speed":   avg_speed1,
                "coordinates": _telemetry_points(tel1),
            },
            "driver2": {
                "driver":      driver2.upper(),
                "lap_time":    str(lap2_time) if lap2_time is not None else None,
                "max_speed":   max_speed2,
                "avg_speed":   avg_speed2,
                "coordinates": _telemetry_points(tel2),
            },
            "delta": {
                "lap_time_diff":  lap_time_diff,
                "max_speed_diff": max_speed1 - max_speed2,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing telemetry: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to compare telemetry: {e}")
