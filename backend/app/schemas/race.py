"""
Pydantic schemas for race data
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class CompoundType(str, Enum):
    SOFT = "SOFT"
    MEDIUM = "MEDIUM"
    HARD = "HARD"
    INTERMEDIATE = "INTERMEDIATE"
    WET = "WET"


class StintType(str, Enum):
    OPENING = "OPENING"
    MID = "MID"
    CLOSING = "CLOSING"


class TrackStatus(str, Enum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    SC = "SC"
    VSC = "VSC"
    RED = "RED"


class SeasonResponse(BaseModel):
    """Season response schema"""
    id: int
    year: int

    class Config:
        from_attributes = True


class RaceBase(BaseModel):
    """Base race schema"""
    grand_prix: str
    gp_slug: str
    event_date: datetime
    round_number: Optional[int] = None
    circuit_name: str
    circuit_short: Optional[str] = None
    circuit_country: Optional[str] = None
    track_length_km: Optional[float] = None
    altitude_m: Optional[float] = None
    circuit_type: Optional[str] = None


class RaceResponse(RaceBase):
    """Race response schema"""
    id: int
    season_id: int

    class Config:
        from_attributes = True


class LapBase(BaseModel):
    """Base lap schema"""
    driver: str
    driver_number: Optional[int] = None
    team: str
    lap_number: int
    lap_time: Optional[str] = None
    lap_time_seconds: Optional[float] = None

    # Sector times
    sector1_time_seconds: Optional[float] = None
    sector2_time_seconds: Optional[float] = None
    sector3_time_seconds: Optional[float] = None

    # Speed traps
    speed_i1: Optional[float] = None
    speed_i2: Optional[float] = None
    speed_fl: Optional[float] = None
    speed_st: Optional[float] = None

    # Tyre info
    compound: Optional[CompoundType] = None
    tyre_life: Optional[int] = None
    is_fresh_tyre: bool = False

    # Stint info
    stint: Optional[int] = None
    stint_type: Optional[StintType] = None

    # Position
    position: Optional[int] = None

    # Track status
    track_status: Optional[TrackStatus] = None

    # Flags
    is_personal_best: bool = False
    is_valid_lap: bool = True
    is_accurate: bool = True


class LapResponse(LapBase):
    """Lap response schema"""
    id: int
    race_id: int

    class Config:
        from_attributes = True


class WeatherDataResponse(BaseModel):
    """Weather data response schema"""
    id: int
    race_id: int
    lap_number: Optional[int] = None
    air_temp: Optional[float] = None
    track_temp: Optional[float] = None
    humidity: Optional[float] = None
    pressure: Optional[float] = None
    wind_speed: Optional[float] = None
    wind_direction: Optional[float] = None
    rainfall: bool = False
    air_density: Optional[float] = None

    class Config:
        from_attributes = True


class RaceDataQuery(BaseModel):
    """Query parameters for race data"""
    season: Optional[int] = None
    grand_prix: Optional[str] = None
    drivers: Optional[List[str]] = Field(default=None, description="List of driver codes")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=100, ge=1, le=1000)


class RaceStatistics(BaseModel):
    """Race statistics summary"""
    driver: str
    team: str
    total_laps: int
    avg_lap_time: float
    fastest_lap: float
    pit_stops: int
    positions_gained: int
    final_position: int


class RaceDataResponse(BaseModel):
    """Complete race data response"""
    race: RaceResponse
    laps: List[LapResponse]
    weather: List[WeatherDataResponse]
    statistics: List[RaceStatistics]
    total_laps: int
    page: int
    page_size: int
