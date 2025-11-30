"""
Database models for RacingLineAI
"""

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean,
    ForeignKey, Index, Enum as SQLEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


class CompoundType(str, enum.Enum):
    """Tyre compound types"""
    SOFT = "SOFT"
    MEDIUM = "MEDIUM"
    HARD = "HARD"
    INTERMEDIATE = "INTERMEDIATE"
    WET = "WET"


class StintType(str, enum.Enum):
    """Stint types"""
    OPENING = "OPENING"
    MID = "MID"
    CLOSING = "CLOSING"


class TrackStatusType(str, enum.Enum):
    """Track status types"""
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    SC = "SC"
    VSC = "VSC"
    RED = "RED"


class Season(Base):
    """F1 Season"""
    __tablename__ = "seasons"

    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, unique=True, nullable=False, index=True)

    # Relationships
    races = relationship("Race", back_populates="season")


class Race(Base):
    """F1 Race Event"""
    __tablename__ = "races"

    id = Column(Integer, primary_key=True, index=True)
    season_id = Column(Integer, ForeignKey("seasons.id"), nullable=False)

    # Race details
    grand_prix = Column(String, nullable=False)
    gp_slug = Column(String, nullable=False, index=True)
    event_date = Column(DateTime, nullable=False)
    round_number = Column(Integer)

    # Circuit details
    circuit_name = Column(String, nullable=False)
    circuit_short = Column(String)
    circuit_country = Column(String)
    track_length_km = Column(Float)
    altitude_m = Column(Float)
    circuit_type = Column(String)

    # Relationships
    season = relationship("Season", back_populates="races")
    laps = relationship("Lap", back_populates="race")
    weather_data = relationship("WeatherData", back_populates="race")

    # Indexes
    __table_args__ = (
        Index('idx_race_season_gp', 'season_id', 'gp_slug'),
    )


class Lap(Base):
    """Individual lap data"""
    __tablename__ = "laps"

    id = Column(Integer, primary_key=True, index=True)
    race_id = Column(Integer, ForeignKey("races.id"), nullable=False)

    # Driver & Team
    driver = Column(String, nullable=False, index=True)
    driver_number = Column(Integer)
    team = Column(String, nullable=False)

    # Lap details
    lap_number = Column(Integer, nullable=False)
    lap_time = Column(String)
    lap_time_seconds = Column(Float, index=True)
    lap_start_time = Column(String)

    # Sector times
    sector1_time = Column(String)
    sector1_time_seconds = Column(Float)
    sector2_time = Column(String)
    sector2_time_seconds = Column(Float)
    sector3_time = Column(String)
    sector3_time_seconds = Column(Float)

    # Sector percentages
    sector1_pct = Column(Float)
    sector2_pct = Column(Float)
    sector3_pct = Column(Float)

    # Speed traps
    speed_i1 = Column(Float)  # Intermediate 1 speed
    speed_i2 = Column(Float)  # Intermediate 2 speed
    speed_fl = Column(Float)  # Finish line speed
    speed_st = Column(Float)  # Speed trap

    # Tyre information
    compound = Column(SQLEnum(CompoundType))
    tyre_life = Column(Integer)
    is_fresh_tyre = Column(Boolean, default=False)

    # Stint information
    stint = Column(Integer)
    stint_type = Column(SQLEnum(StintType))
    stint_length = Column(Integer)

    # Pit stop
    is_pit_lap = Column(Boolean, default=False)
    pit_in_time = Column(String)
    pit_out_time = Column(String)
    pit_duration = Column(Float)

    # Position
    position = Column(Integer)

    # Track conditions
    track_status = Column(SQLEnum(TrackStatusType))

    # Calculated fields
    best_sector = Column(Integer)  # 1, 2, or 3
    delta_to_fastest_lap = Column(Float)
    avg_lap_time = Column(Float)

    # Flags
    is_personal_best = Column(Boolean, default=False)
    is_valid_lap = Column(Boolean, default=True)
    is_accurate = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    deleted_reason = Column(String)

    # Race situation flags
    is_wet_lap = Column(Boolean, default=False)
    is_dry_lap = Column(Boolean, default=True)
    is_sc = Column(Boolean, default=False)
    is_vsc = Column(Boolean, default=False)
    is_red_flag = Column(Boolean, default=False)
    is_dnf = Column(Boolean, default=False)

    # Relationships
    race = relationship("Race", back_populates="laps")

    # Indexes for common queries
    __table_args__ = (
        Index('idx_lap_race_driver', 'race_id', 'driver'),
        Index('idx_lap_race_number', 'race_id', 'lap_number'),
        Index('idx_lap_compound', 'compound'),
    )


class WeatherData(Base):
    """Weather data for races"""
    __tablename__ = "weather_data"

    id = Column(Integer, primary_key=True, index=True)
    race_id = Column(Integer, ForeignKey("races.id"), nullable=False)

    # Timestamp
    weather_time = Column(DateTime, nullable=False)
    lap_number = Column(Integer)

    # Weather conditions
    air_temp = Column(Float)
    track_temp = Column(Float)
    humidity = Column(Float)
    pressure = Column(Float)
    wind_speed = Column(Float)
    wind_direction = Column(Float)
    rainfall = Column(Boolean, default=False)

    # Calculated
    air_density = Column(Float)

    # Relationships
    race = relationship("Race", back_populates="weather_data")

    __table_args__ = (
        Index('idx_weather_race_lap', 'race_id', 'lap_number'),
    )


class PredictionCache(Base):
    """Cache for ML predictions"""
    __tablename__ = "prediction_cache"

    id = Column(Integer, primary_key=True, index=True)

    # Cache key
    race_id = Column(Integer, ForeignKey("races.id"), nullable=False)
    driver = Column(String, nullable=False)
    model_type = Column(String, nullable=False)  # 'lstm', 'regression', 'strategy'

    # Prediction data (stored as JSON)
    prediction_data = Column(String)

    # Metadata
    created_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    __table_args__ = (
        Index('idx_prediction_cache', 'race_id', 'driver', 'model_type'),
    )
