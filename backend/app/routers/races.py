"""
Race data API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.models.database import Season, Race, Lap, WeatherData
from app.schemas.race import (
    SeasonResponse, RaceResponse, LapResponse,
    WeatherDataResponse, RaceDataQuery, RaceDataResponse,
    RaceStatistics
)

router = APIRouter()


@router.get("/seasons", response_model=List[SeasonResponse])
async def get_seasons(db: Session = Depends(get_db)):
    """
    Get all available seasons
    """
    seasons = db.query(Season).order_by(Season.year.desc()).all()
    return seasons


@router.get("/seasons/{year}/races", response_model=List[RaceResponse])
async def get_races_by_season(year: int, db: Session = Depends(get_db)):
    """
    Get all races for a specific season
    """
    season = db.query(Season).filter(Season.year == year).first()
    if not season:
        raise HTTPException(status_code=404, detail=f"Season {year} not found")

    races = db.query(Race).filter(Race.season_id == season.id).order_by(Race.event_date).all()
    return races


@router.get("/races/{race_id}", response_model=RaceResponse)
async def get_race(race_id: int, db: Session = Depends(get_db)):
    """
    Get specific race details
    """
    race = db.query(Race).filter(Race.id == race_id).first()
    if not race:
        raise HTTPException(status_code=404, detail="Race not found")
    return race


@router.get("/races/{race_id}/laps", response_model=List[LapResponse])
async def get_race_laps(
    race_id: int,
    driver: Optional[str] = None,
    lap_number: Optional[int] = None,
    min_lap: Optional[int] = None,
    max_lap: Optional[int] = None,
    compound: Optional[str] = None,
    valid_only: bool = True,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Get lap data for a specific race with filtering

    Args:
        race_id: Race ID
        driver: Filter by driver code (e.g., 'VER', 'HAM')
        lap_number: Filter by specific lap number
        min_lap: Minimum lap number
        max_lap: Maximum lap number
        compound: Filter by tyre compound
        valid_only: Only include valid laps
        page: Page number
        page_size: Items per page
    """
    query = db.query(Lap).filter(Lap.race_id == race_id)

    # Apply filters
    if driver:
        query = query.filter(Lap.driver == driver.upper())

    if lap_number:
        query = query.filter(Lap.lap_number == lap_number)

    if min_lap:
        query = query.filter(Lap.lap_number >= min_lap)

    if max_lap:
        query = query.filter(Lap.lap_number <= max_lap)

    if compound:
        query = query.filter(Lap.compound == compound.upper())

    if valid_only:
        query = query.filter(Lap.is_valid_lap == True)

    # Pagination
    offset = (page - 1) * page_size
    laps = query.order_by(Lap.lap_number).offset(offset).limit(page_size).all()

    return laps


@router.get("/races/{race_id}/weather", response_model=List[WeatherDataResponse])
async def get_race_weather(race_id: int, db: Session = Depends(get_db)):
    """
    Get weather data for a specific race
    """
    weather = db.query(WeatherData).filter(WeatherData.race_id == race_id).order_by(WeatherData.lap_number).all()
    return weather


@router.get("/races/{race_id}/statistics", response_model=List[RaceStatistics])
async def get_race_statistics(
    race_id: int,
    drivers: Optional[List[str]] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get race statistics for drivers

    Args:
        race_id: Race ID
        drivers: Optional list of driver codes
    """
    query = db.query(Lap).filter(Lap.race_id == race_id)

    if drivers:
        query = query.filter(Lap.driver.in_([d.upper() for d in drivers]))

    laps = query.all()

    if not laps:
        return []

    # Group by driver and calculate statistics
    from collections import defaultdict
    import pandas as pd

    df = pd.DataFrame([{
        'driver': lap.driver,
        'team': lap.team,
        'lap_number': lap.lap_number,
        'lap_time_seconds': lap.lap_time_seconds,
        'position': lap.position,
        'is_pit_lap': lap.is_pit_lap,
        'is_valid_lap': lap.is_valid_lap
    } for lap in laps])

    statistics = []

    for driver in df['driver'].unique():
        driver_laps = df[df['driver'] == driver]
        valid_laps = driver_laps[driver_laps['is_valid_lap'] == True]

        if len(valid_laps) == 0:
            continue

        team = driver_laps['team'].iloc[0]
        total_laps = len(driver_laps)
        avg_lap_time = valid_laps['lap_time_seconds'].mean()
        fastest_lap = valid_laps['lap_time_seconds'].min()
        pit_stops = driver_laps['is_pit_lap'].sum()

        # Position changes
        first_position = driver_laps['position'].iloc[0] if 'position' in driver_laps.columns else 0
        final_position = driver_laps['position'].iloc[-1] if 'position' in driver_laps.columns else 0
        positions_gained = first_position - final_position if first_position and final_position else 0

        statistics.append(RaceStatistics(
            driver=driver,
            team=team,
            total_laps=total_laps,
            avg_lap_time=avg_lap_time,
            fastest_lap=fastest_lap,
            pit_stops=pit_stops,
            positions_gained=positions_gained,
            final_position=final_position
        ))

    return statistics


@router.get("/data", response_model=dict)
async def get_race_data(
    season: Optional[int] = None,
    grand_prix: Optional[str] = None,
    drivers: Optional[List[str]] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Get race data with comprehensive filtering

    Args:
        season: Season year
        grand_prix: Grand Prix slug
        drivers: List of driver codes
        page: Page number
        page_size: Items per page
    """
    # Find race
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

    # Get laps
    laps_query = db.query(Lap).filter(Lap.race_id == race.id)

    if drivers:
        laps_query = laps_query.filter(Lap.driver.in_([d.upper() for d in drivers]))

    # Pagination
    offset = (page - 1) * page_size
    total_laps = laps_query.count()
    laps = laps_query.order_by(Lap.lap_number).offset(offset).limit(page_size).all()

    # Get weather
    weather = db.query(WeatherData).filter(WeatherData.race_id == race.id).all()

    # Get statistics
    stats_drivers = drivers if drivers else [lap.driver for lap in db.query(Lap.driver).filter(Lap.race_id == race.id).distinct()]
    statistics = await get_race_statistics(race.id, stats_drivers, db)

    return {
        'race': race,
        'laps': laps,
        'weather': weather,
        'statistics': statistics,
        'total_laps': total_laps,
        'page': page,
        'page_size': page_size
    }


@router.get("/drivers", response_model=List[str])
async def get_drivers(
    season: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get list of all drivers

    Args:
        season: Optional season filter
    """
    query = db.query(Lap.driver).distinct()

    if season:
        season_obj = db.query(Season).filter(Season.year == season).first()
        if season_obj:
            race_ids = [r.id for r in db.query(Race.id).filter(Race.season_id == season_obj.id).all()]
            query = query.filter(Lap.race_id.in_(race_ids))

    drivers = [row[0] for row in query.all()]
    return sorted(drivers)


@router.get("/teams", response_model=List[str])
async def get_teams(
    season: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get list of all teams

    Args:
        season: Optional season filter
    """
    query = db.query(Lap.team).distinct()

    if season:
        season_obj = db.query(Season).filter(Season.year == season).first()
        if season_obj:
            race_ids = [r.id for r in db.query(Race.id).filter(Race.season_id == season_obj.id).all()]
            query = query.filter(Lap.race_id.in_(race_ids))

    teams = [row[0] for row in query.all()]
    return sorted(teams)
