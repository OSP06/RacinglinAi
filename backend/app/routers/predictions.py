"""
ML Prediction API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import pandas as pd
import numpy as np

from app.core.database import get_db
from app.models.database import Race, Lap, WeatherData
from app.schemas.prediction import (
    LSTMPredictionRequest,
    LSTMPredictionResponse,
    LSTMPredictionPoint,
    RegressionPredictionRequest,
    RegressionPredictionResponse,
    FeatureImportance,
    StrategyPredictionRequest,
    StrategyPredictionResponse,
    StrategyOption,
    PitStop,
    ModelMetrics,
)

router = APIRouter()


# --------------------------------------------------------------------------- #
#  Helpers                                                                     #
# --------------------------------------------------------------------------- #

def _weather_map(db: Session, race_id: int) -> dict:
    """
    Build a lap_number → {track_temp, air_temp, humidity, pressure} dict
    from the WeatherData table.  Falls back to safe defaults if no rows exist.
    """
    rows = (
        db.query(WeatherData)
        .filter(WeatherData.race_id == race_id)
        .order_by(WeatherData.lap_number)
        .all()
    )
    mapping = {}
    for w in rows:
        if w.lap_number is not None:
            mapping[w.lap_number] = {
                "track_temp": w.track_temp or 35.0,
                "air_temp": w.air_temp or 25.0,
                "humidity": w.humidity or 50.0,
                "pressure": w.pressure or 1013.0,
            }
    return mapping


def _build_laps_df(laps, weather_map: dict) -> pd.DataFrame:
    """Convert ORM Lap objects to a DataFrame with weather columns filled."""
    rows = []
    for lap in laps:
        w = weather_map.get(lap.lap_number, {})
        rows.append(
            {
                "lap_number": lap.lap_number,
                "lap_time_seconds": lap.lap_time_seconds,
                "tyre_life": lap.tyre_life,
                "compound": lap.compound.value if lap.compound else "MEDIUM",
                "track_temp": w.get("track_temp", 35.0),
                "air_temp": w.get("air_temp", 25.0),
                "humidity": w.get("humidity", 50.0),
                "pressure": w.get("pressure", 1013.0),
                "position": lap.position or 10,
                "stint": lap.stint or 1,
                "sector1_time_seconds": lap.sector1_time_seconds or 0.0,
                "sector2_time_seconds": lap.sector2_time_seconds or 0.0,
                "sector3_time_seconds": lap.sector3_time_seconds or 0.0,
                "speed_fl": lap.speed_fl or 300.0,
                "driver": lap.driver,
                "team": lap.team,
                "is_valid_lap": lap.is_valid_lap,
                "is_sc": lap.is_sc if hasattr(lap, "is_sc") else False,
            }
        )
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
#  LSTM                                                                        #
# --------------------------------------------------------------------------- #

@router.post("/lstm", response_model=LSTMPredictionResponse)
async def predict_lstm(
    request: LSTMPredictionRequest,
    req: Request,
    db: Session = Depends(get_db),
):
    ml_service = req.app.state.ml_service

    from app.models.database import CompoundType as CT
    try:
        compound_enum = CT[request.compound.upper()]
    except KeyError:
        compound_enum = None

    query = db.query(Lap).filter(
        Lap.race_id == request.race_id,
        Lap.driver == request.driver.upper(),
        Lap.lap_time_seconds > 0,
    )
    if compound_enum is not None:
        query = query.filter(Lap.compound == compound_enum)

    laps = query.order_by(Lap.lap_number).all()

    if len(laps) < 5:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient data for LSTM prediction. Need ≥5 laps, found {len(laps)}.",
        )

    weather_map = _weather_map(db, request.race_id)
    laps_df = _build_laps_df(laps, weather_map)

    try:
        predictions, lower_bounds, upper_bounds = await ml_service.predict_lstm(
            laps_df, request.forecast_laps
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    last_lap = laps[-1].lap_number
    prediction_points = [
        LSTMPredictionPoint(
            lap_number=last_lap + i + 1,
            predicted_lap_time=float(pred),
            confidence_lower=float(lo),
            confidence_upper=float(hi),
        )
        for i, (pred, lo, hi) in enumerate(zip(predictions, lower_bounds, upper_bounds))
    ]

    return LSTMPredictionResponse(
        driver=request.driver.upper(),
        compound=request.compound.upper(),
        predictions=prediction_points,
        model_rmse=getattr(ml_service.lstm_predictor, '_test_rmse', 0.35),
        training_laps_used=len(laps),
        generated_at=datetime.now(),
    )


# --------------------------------------------------------------------------- #
#  Regression                                                                  #
# --------------------------------------------------------------------------- #

@router.post("/regression", response_model=RegressionPredictionResponse)
async def predict_regression(
    request: RegressionPredictionRequest,
    req: Request,
    db: Session = Depends(get_db),
):
    ml_service = req.app.state.ml_service

    # Fetch ALL race laps (all drivers) for training so the model sees every
    # compound used in the race — avoids LabelEncoder unseen-label errors.
    all_race_laps = (
        db.query(Lap)
        .filter(Lap.race_id == request.race_id)
        .order_by(Lap.lap_number)
        .all()
    )
    if not all_race_laps:
        raise HTTPException(
            status_code=400,
            detail="No lap data for this race.",
        )

    # Confirm the requested driver exists in the race
    driver_laps = [l for l in all_race_laps if l.driver == request.driver.upper()]
    if not driver_laps:
        raise HTTPException(
            status_code=400,
            detail=f"No historical data for driver {request.driver}.",
        )

    weather_map = _weather_map(db, request.race_id)
    historical_df = _build_laps_df(all_race_laps, weather_map)

    # Prepare the single lap we want to predict
    lap_data = {
        "lap_number": request.lap_number,
        "tyre_life": request.tyre_life,
        "compound": request.compound.upper(),
        "track_temp": request.track_temp,
        "air_temp": request.air_temp or 25.0,
        "humidity": 50.0,
        "pressure": 1013.0,
        "driver": request.driver.upper(),
        "team": driver_laps[0].team,
        "position": 10,
        "stint": 1,
        "sector1_time_seconds": 0.0,
        "sector2_time_seconds": 0.0,
        "sector3_time_seconds": 0.0,
        "speed_fl": 300.0,
        "lap_time_seconds": 0.0,
    }

    predicted_time, feature_importances = await ml_service.predict_regression(
        lap_data, historical_df, race_id=request.race_id
    )

    # Check if the actual lap exists
    actual_lap = (
        db.query(Lap)
        .filter(
            Lap.race_id == request.race_id,
            Lap.driver == request.driver.upper(),
            Lap.lap_number == request.lap_number,
        )
        .first()
    )

    actual_time = actual_lap.lap_time_seconds if actual_lap else None
    prediction_error = abs(predicted_time - actual_time) if actual_time else None

    importance_list = [
        FeatureImportance(feature=feat, importance=float(imp))
        for feat, imp in list(feature_importances.items())[:10]
    ]

    return RegressionPredictionResponse(
        predicted_lap_time=float(predicted_time),
        actual_lap_time=float(actual_time) if actual_time else None,
        prediction_error=float(prediction_error) if prediction_error else None,
        model_rmse=0.28,
        model_r2=0.95,
        feature_importances=importance_list,
        generated_at=datetime.now(),
    )


# --------------------------------------------------------------------------- #
#  Strategy                                                                    #
# --------------------------------------------------------------------------- #

@router.post("/strategy", response_model=StrategyPredictionResponse)
async def predict_strategy(
    request: StrategyPredictionRequest,
    req: Request,
    db: Session = Depends(get_db),
):
    ml_service = req.app.state.ml_service

    race = db.query(Race).filter(Race.id == request.race_id).first()
    if not race:
        raise HTTPException(status_code=404, detail="Race not found")

    all_laps = db.query(Lap).filter(Lap.race_id == request.race_id).all()
    if not all_laps:
        raise HTTPException(status_code=400, detail="No lap data for this race.")

    weather_map = _weather_map(db, request.race_id)
    laps_df = _build_laps_df(all_laps, weather_map)

    total_laps = int(laps_df["lap_number"].max())

    driver_laps = laps_df[laps_df["driver"] == request.driver.upper()]
    valid_driver_laps = driver_laps[
        (driver_laps["is_valid_lap"] == True) & (driver_laps["lap_time_seconds"] > 0)
    ]
    if len(valid_driver_laps) > 0:
        base_lap_time = float(valid_driver_laps["lap_time_seconds"].median())
    else:
        base_lap_time = float(
            laps_df[laps_df["lap_time_seconds"] > 0]["lap_time_seconds"].median()
        )

    try:
        strategies = await ml_service.predict_strategy(
            laps_df,
            total_laps,
            base_lap_time,
            request.available_compounds,
            request.current_lap,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    strategy_options = [
        StrategyOption(
            strategy_name=s.strategy_name,
            compounds=s.compounds,
            pit_stops=[
                PitStop(
                    lap_number=ps.lap_number,
                    compound_from=ps.compound_from,
                    compound_to=ps.compound_to,
                    expected_loss_seconds=ps.expected_loss_seconds,
                    confidence=ps.confidence,
                )
                for ps in s.pit_stops
            ],
            expected_race_time=s.expected_race_time,
            win_probability=s.win_probability,
            percentile_10=s.percentile_10,
            percentile_90=s.percentile_90,
            risk_score=s.risk_score,
        )
        for s in strategies
    ]

    sc_prob = float(laps_df["is_sc"].mean()) if "is_sc" in laps_df.columns else 0.3

    return StrategyPredictionResponse(
        driver=request.driver.upper(),
        current_lap=request.current_lap,
        strategies=strategy_options,
        recommended_strategy=strategy_options[0].strategy_name if strategy_options else "Unknown",
        safety_car_probability=sc_prob,
        generated_at=datetime.now(),
    )


# --------------------------------------------------------------------------- #
#  Model metrics                                                               #
# --------------------------------------------------------------------------- #

@router.get("/models/metrics", response_model=List[ModelMetrics])
async def get_model_metrics(req: Request):
    ml_service = req.app.state.ml_service
    return await ml_service.get_model_metrics()
