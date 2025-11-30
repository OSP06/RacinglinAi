"""
Pydantic schemas for ML predictions
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


class LSTMPredictionRequest(BaseModel):
    """Request for LSTM lap time prediction"""
    race_id: int
    driver: str
    compound: str
    forecast_laps: int = Field(default=15, ge=1, le=30)


class LSTMPredictionPoint(BaseModel):
    """Single prediction point"""
    lap_number: int
    predicted_lap_time: float
    confidence_lower: float
    confidence_upper: float


class LSTMPredictionResponse(BaseModel):
    """Response for LSTM prediction"""
    driver: str
    compound: str
    predictions: List[LSTMPredictionPoint]
    model_rmse: float
    training_laps_used: int
    generated_at: datetime


class RegressionPredictionRequest(BaseModel):
    """Request for regression-based prediction"""
    race_id: int
    driver: str
    lap_number: int
    compound: str
    tyre_life: int
    track_temp: float
    air_temp: Optional[float] = None
    fuel_load: Optional[float] = None


class FeatureImportance(BaseModel):
    """Feature importance from regression model"""
    feature: str
    importance: float


class RegressionPredictionResponse(BaseModel):
    """Response for regression prediction"""
    predicted_lap_time: float
    actual_lap_time: Optional[float] = None
    prediction_error: Optional[float] = None
    model_rmse: float
    model_r2: float
    feature_importances: List[FeatureImportance]
    generated_at: datetime


class StrategyPredictionRequest(BaseModel):
    """Request for pit strategy prediction"""
    race_id: int
    driver: str
    current_lap: int = 1
    available_compounds: List[str] = Field(default=["SOFT", "MEDIUM", "HARD"])


class PitStop(BaseModel):
    """Predicted pit stop"""
    lap_number: int
    compound_from: str
    compound_to: str
    expected_loss_seconds: float
    confidence: float


class StrategyOption(BaseModel):
    """Single strategy option"""
    strategy_name: str
    compounds: List[str]
    pit_stops: List[PitStop]
    expected_race_time: float
    win_probability: float
    percentile_10: float  # Best case
    percentile_90: float  # Worst case
    risk_score: float  # 0-100, higher = riskier


class StrategyPredictionResponse(BaseModel):
    """Response for strategy prediction"""
    driver: str
    current_lap: int
    strategies: List[StrategyOption]
    recommended_strategy: str
    safety_car_probability: float
    generated_at: datetime


class ModelMetrics(BaseModel):
    """Overall model performance metrics"""
    model_type: str
    rmse: float
    mae: float
    r2_score: float
    training_samples: int
    last_trained: datetime
    accuracy_by_compound: Dict[str, float]
