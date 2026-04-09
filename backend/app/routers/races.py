"""
Race data API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from typing import List, Optional

from app.core.database import get_db
from app.models.database import Season, Race, Lap, WeatherData
from app.schemas.race import (
    SeasonResponse, RaceResponse, LapResponse,
    WeatherDataResponse, RaceDataResponse,
    RaceStatistics,
)

router = APIRouter()


# --------------------------------------------------------------------------- #
#  Helpers                                                                     #
# --------------------------------------------------------------------------- #

def _lap_to_dict(lap: Lap) -> dict:
    """Serialize a Lap ORM object to a plain dict, including hybrid props."""
    return {
        "id": lap.id,
        "race_id": lap.race_id,
        "driver": lap.driver,
        "driver_number": lap.driver_number,
        "team": lap.team,
        "lap_number": lap.lap_number,
        "lap_time": lap.lap_time,
        "lap_time_seconds": lap.lap_time_seconds,
        "sector1_time_seconds": lap.sector1_time_seconds,
        "sector2_time_seconds": lap.sector2_time_seconds,
        "sector3_time_seconds": lap.sector3_time_seconds,
        "sector1_pct": lap.sector1_pct,
        "sector2_pct": lap.sector2_pct,
        "sector3_pct": lap.sector3_pct,
        "speed_i1": lap.speed_i1,
        "speed_i2": lap.speed_i2,
        "speed_fl": lap.speed_fl,
        "speed_st": lap.speed_st,
        "compound": lap.compound.value if lap.compound else None,
        "tyre_life": lap.tyre_life,
        "is_fresh_tyre": lap.is_fresh_tyre,
        "stint": lap.stint,
        "stint_type": lap.stint_type.value if lap.stint_type else None,
        "position": lap.position,
        "track_status": lap.track_status.value if lap.track_status else None,
        "delta_to_fastest_lap": lap.delta_to_fastest_lap,
        "is_personal_best": lap.is_personal_best,
        "is_valid_lap": lap.is_valid_lap,
        "is_accurate": lap.is_accurate,
        # Hybrid properties — evaluate here so Pydantic can serialise them
        "is_pit_out_lap": lap.is_pit_out_lap,
        "is_pit_in_lap": lap.is_pit_in_lap,
    }


def _compute_race_statistics(laps: List[Lap]) -> List[RaceStatistics]:
    """Compute per-driver statistics from a list of Lap ORM objects."""
    from collections import defaultdict

    driver_laps: dict = defaultdict(list)
    driver_team: dict = {}

    for lap in laps:
        driver_laps[lap.driver].append(lap)
        driver_team[lap.driver] = lap.team

    statistics = []
    for driver, dlaps in driver_laps.items():
        valid = [l for l in dlaps if l.is_valid_lap and l.lap_time_seconds and l.lap_time_seconds > 0]
        if not valid:
            continue

        lap_times = [l.lap_time_seconds for l in valid]
        avg_lap_time = sum(lap_times) / len(lap_times) if lap_times else 0.0
        fastest_lap = min(lap_times) if lap_times else 0.0
        pit_stops = sum(1 for l in dlaps if l.is_pit_in_lap)

        positions = [l.position for l in dlaps if l.position]
        first_pos = positions[0] if positions else 0
        final_pos = positions[-1] if positions else 0
        positions_gained = (first_pos - final_pos) if first_pos and final_pos else 0

        statistics.append(RaceStatistics(
            driver=driver,
            team=driver_team[driver],
            total_laps=len(dlaps),
            avg_lap_time=avg_lap_time,
            fastest_lap=fastest_lap,
            pit_stops=pit_stops,
            positions_gained=positions_gained,
            final_position=final_pos,
        ))

    return statistics


# --------------------------------------------------------------------------- #
#  Endpoints                                                                   #
# --------------------------------------------------------------------------- #

@router.get("/seasons", response_model=List[SeasonResponse])
async def get_seasons(db: Session = Depends(get_db)):
    return db.query(Season).order_by(Season.year.desc()).all()


@router.get("/seasons/{year}/races", response_model=List[RaceResponse])
async def get_races_by_season(year: int, db: Session = Depends(get_db)):
    season = db.query(Season).filter(Season.year == year).first()
    if not season:
        raise HTTPException(status_code=404, detail=f"Season {year} not found")
    return (
        db.query(Race)
        .filter(Race.season_id == season.id)
        .order_by(Race.event_date)
        .all()
    )


@router.get("/races/{race_id}", response_model=RaceResponse)
async def get_race(race_id: int, db: Session = Depends(get_db)):
    race = db.query(Race).filter(Race.id == race_id).first()
    if not race:
        raise HTTPException(status_code=404, detail="Race not found")
    return race


@router.get("/races/{race_id}/laps")
async def get_race_laps(
    race_id: int,
    driver: Optional[str] = None,
    lap_number: Optional[int] = None,
    min_lap: Optional[int] = None,
    max_lap: Optional[int] = None,
    compound: Optional[str] = None,
    valid_only: bool = False,   # default False so frontend gets all laps
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=2000),
    db: Session = Depends(get_db),
):
    """
    Return lap data for a race.  All filtering is optional.
    Returns plain dicts (not Pydantic models) so hybrid properties are included.
    """
    query = db.query(Lap).filter(Lap.race_id == race_id)

    if driver:
        query = query.filter(Lap.driver == driver.upper())
    if lap_number is not None:
        query = query.filter(Lap.lap_number == lap_number)
    if min_lap is not None:
        query = query.filter(Lap.lap_number >= min_lap)
    if max_lap is not None:
        query = query.filter(Lap.lap_number <= max_lap)
    if compound:
        from app.models.database import CompoundType as CT
        try:
            query = query.filter(Lap.compound == CT[compound.upper()])
        except KeyError:
            pass  # unknown compound — return all
    if valid_only:
        query = query.filter(Lap.is_valid_lap == True)

    offset = (page - 1) * page_size
    laps = query.order_by(Lap.driver, Lap.lap_number).offset(offset).limit(page_size).all()

    return [_lap_to_dict(l) for l in laps]


@router.get("/races/{race_id}/weather", response_model=List[WeatherDataResponse])
async def get_race_weather(race_id: int, db: Session = Depends(get_db)):
    return (
        db.query(WeatherData)
        .filter(WeatherData.race_id == race_id)
        .order_by(WeatherData.lap_number)
        .all()
    )


@router.get("/races/{race_id}/statistics", response_model=List[RaceStatistics])
async def get_race_statistics(
    race_id: int,
    drivers: Optional[List[str]] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Lap).filter(Lap.race_id == race_id)
    if drivers:
        query = query.filter(Lap.driver.in_([d.upper() for d in drivers]))

    laps = query.all()
    if not laps:
        return []

    return _compute_race_statistics(laps)


@router.get("/data")
async def get_race_data(
    season: Optional[int] = None,
    grand_prix: Optional[str] = None,
    drivers: Optional[List[str]] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    race_query = db.query(Race)

    if season:
        season_obj = db.query(Season).filter(Season.year == season).first()
        if not season_obj:
            raise HTTPException(status_code=404, detail=f"Season {season} not found")
        race_query = race_query.filter(Race.season_id == season_obj.id)

    if grand_prix:
        race_query = race_query.filter(Race.gp_slug == grand_prix.lower())

    race = race_query.first()
    if not race:
        raise HTTPException(status_code=404, detail="Race not found")

    laps_query = db.query(Lap).filter(Lap.race_id == race.id)
    if drivers:
        laps_query = laps_query.filter(Lap.driver.in_([d.upper() for d in drivers]))

    total_laps = laps_query.count()
    offset = (page - 1) * page_size
    laps = laps_query.order_by(Lap.lap_number).offset(offset).limit(page_size).all()

    weather = db.query(WeatherData).filter(WeatherData.race_id == race.id).all()
    statistics = _compute_race_statistics(laps)

    return {
        "race": race,
        "laps": [_lap_to_dict(l) for l in laps],
        "weather": weather,
        "statistics": statistics,
        "total_laps": total_laps,
        "page": page,
        "page_size": page_size,
    }


@router.get("/drivers", response_model=List[str])
async def get_drivers(
    season: Optional[int] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Lap.driver).distinct()

    if season:
        season_obj = db.query(Season).filter(Season.year == season).first()
        if season_obj:
            race_ids = [
                r.id
                for r in db.query(Race.id).filter(Race.season_id == season_obj.id).all()
            ]
            query = query.filter(Lap.race_id.in_(race_ids))

    return sorted(row[0] for row in query.all())


@router.get("/teams", response_model=List[str])
async def get_teams(
    season: Optional[int] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Lap.team).distinct()

    if season:
        season_obj = db.query(Season).filter(Season.year == season).first()
        if season_obj:
            race_ids = [
                r.id
                for r in db.query(Race.id).filter(Race.season_id == season_obj.id).all()
            ]
            query = query.filter(Lap.race_id.in_(race_ids))

    return sorted(row[0] for row in query.all())
