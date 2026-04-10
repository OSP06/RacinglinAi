"""
Enhanced Regression Model using LightGBM
Better handling of non-linear relationships and feature interactions
"""

import numpy as np
import pandas as pd
import lightgbm as lgb
from typing import Dict, List, Tuple, Optional
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import LabelEncoder
import joblib
import logging

logger = logging.getLogger(__name__)


class EnhancedRegressionPredictor:
    """
    Gradient Boosting regressor for lap time prediction
    """

    def __init__(self):
        self.model = None
        self.label_encoders = {}
        self.feature_names = []
        self.feature_importances = {}

    def create_features(self, laps_df: pd.DataFrame) -> pd.DataFrame:
        """
        Create comprehensive feature set

        Args:
            laps_df: DataFrame with lap data

        Returns:
            DataFrame with engineered features
        """
        df = laps_df.copy()

        total_laps = df['lap_number'].max()

        # 1. Fuel load estimation
        df['fuel_load_kg'] = (total_laps - df['lap_number']) * 2.0

        # 2. Fuel effect on lap time (non-linear)
        df['fuel_effect'] = df['fuel_load_kg'] * 0.03  # ~0.03s per kg

        # 3. Air density calculation
        if 'pressure' in df.columns and 'air_temp' in df.columns and 'humidity' in df.columns:
            # Full air density calculation
            vapor_pressure = 6.1078 * 10 ** ((7.5 * df['air_temp']) / (df['air_temp'] + 237.3))
            partial_pressure = (df['humidity'] / 100) * vapor_pressure

            df['air_density'] = (
                ((df['pressure'] * 100) - partial_pressure) / (287.05 * (df['air_temp'] + 273.15))
            )
        else:
            df['air_density'] = 1.225  # Standard

        # Density effect index (relative to standard)
        df['air_density_index'] = df['air_density'] / 1.225

        # 4. Wind effects
        if 'wind_speed' in df.columns and 'wind_direction' in df.columns:
            # Headwind/tailwind component
            df['wind_headwind'] = df['wind_speed'] * np.cos(np.radians(df['wind_direction']))
            # Crosswind component
            df['wind_crosswind'] = df['wind_speed'] * np.sin(np.radians(df['wind_direction']))
        else:
            df['wind_headwind'] = 0.0
            df['wind_crosswind'] = 0.0

        # 5. Tyre compound modeling
        optimal_temps = {
            'SOFT': 100, 'MEDIUM': 105, 'HARD': 110,
            'INTERMEDIATE': 80, 'WET': 70
        }
        peak_laps = {
            'SOFT': 3, 'MEDIUM': 5, 'HARD': 7,
            'INTERMEDIATE': 2, 'WET': 2
        }
        cliff_laps = {
            'SOFT': 15, 'MEDIUM': 25, 'HARD': 35,
            'INTERMEDIATE': 20, 'WET': 25
        }

        df['optimal_track_temp'] = df['compound'].map(optimal_temps).fillna(100)
        df['peak_lap'] = df['compound'].map(peak_laps).fillna(5)
        df['cliff_lap'] = df['compound'].map(cliff_laps).fillna(25)

        # Temperature delta from optimal
        if 'track_temp' in df.columns:
            df['temp_delta'] = df['track_temp'] - df['optimal_track_temp']
            df['temp_delta_abs'] = np.abs(df['temp_delta'])
            df['temp_penalty'] = df['temp_delta_abs'] * 0.05  # 0.05s per degree
        else:
            df['temp_delta'] = 0.0
            df['temp_delta_abs'] = 0.0
            df['temp_penalty'] = 0.0

        # 6. Tyre life modeling (non-linear)
        df['tyre_life_squared'] = df['tyre_life'] ** 2
        df['tyre_life_cubed'] = df['tyre_life'] ** 3

        # Warmup phase (0-1)
        df['tyre_warmup'] = np.minimum(df['tyre_life'] / df['peak_lap'], 1.0)

        # Degradation phase
        df['laps_past_peak'] = np.maximum(df['tyre_life'] - df['peak_lap'], 0)

        # Cliff phase (exponential degradation)
        df['past_cliff'] = (df['tyre_life'] > df['cliff_lap']).astype(int)
        df['laps_past_cliff'] = np.maximum(df['tyre_life'] - df['cliff_lap'], 0)
        df['cliff_degradation'] = df['laps_past_cliff'] ** 1.5

        # 7. Track evolution
        df['track_progression'] = df['lap_number'] / total_laps
        df['track_rubber'] = np.log1p(df['lap_number'])  # Logarithmic improvement

        # 8. Stint analysis
        if 'stint' in df.columns:
            df['stint_lap'] = df.groupby(['driver', 'stint']).cumcount() + 1
            df['stint_lap_squared'] = df['stint_lap'] ** 2
        else:
            df['stint_lap'] = df['tyre_life']
            df['stint_lap_squared'] = df['stint_lap'] ** 2

        # 9. Performance deltas
        if all(col in df.columns for col in ['sector1_time_seconds', 'sector2_time_seconds', 'sector3_time_seconds']):
            # Best sectors
            best_s1 = df['sector1_time_seconds'].replace(0, np.nan).min()
            best_s2 = df['sector2_time_seconds'].replace(0, np.nan).min()
            best_s3 = df['sector3_time_seconds'].replace(0, np.nan).min()

            df['s1_delta'] = df['sector1_time_seconds'] - (best_s1 if not np.isnan(best_s1) else 0)
            df['s2_delta'] = df['sector2_time_seconds'] - (best_s2 if not np.isnan(best_s2) else 0)
            df['s3_delta'] = df['sector3_time_seconds'] - (best_s3 if not np.isnan(best_s3) else 0)

            # Compute sector percentages if not present (they come from ORM hybrid prop)
            if 'sector1_pct' not in df.columns:
                sector_total = df['sector1_time_seconds'] + df['sector2_time_seconds'] + df['sector3_time_seconds']
                sector_total = sector_total.replace(0, np.nan)
                df['sector1_pct'] = (df['sector1_time_seconds'] / sector_total * 100).fillna(33.33)
                df['sector2_pct'] = (df['sector2_time_seconds'] / sector_total * 100).fillna(33.33)
                df['sector3_pct'] = (df['sector3_time_seconds'] / sector_total * 100).fillna(33.33)

            df['s1_pct_delta'] = df['sector1_pct'] - 33.33
            df['s2_pct_delta'] = df['sector2_pct'] - 33.33
            df['s3_pct_delta'] = df['sector3_pct'] - 33.33
        else:
            df['s1_delta'] = 0.0
            df['s2_delta'] = 0.0
            df['s3_delta'] = 0.0
            df['s1_pct_delta'] = 0.0
            df['s2_pct_delta'] = 0.0
            df['s3_pct_delta'] = 0.0

        # 10. Rolling statistics
        for window in [3, 5]:
            df[f'lap_time_rolling_mean_{window}'] = df.groupby('driver')['lap_time_seconds'].transform(
                lambda x: x.rolling(window, min_periods=1).mean()
            )
            df[f'lap_time_rolling_std_{window}'] = df.groupby('driver')['lap_time_seconds'].transform(
                lambda x: x.rolling(window, min_periods=1).std()
            ).fillna(0)

        # 11. Position and race context
        if 'position' in df.columns:
            df['position_change'] = df.groupby('driver')['position'].diff().fillna(0)
            df['fighting_position'] = (np.abs(df['position_change']) > 0).astype(int)
        else:
            df['position_change'] = 0
            df['fighting_position'] = 0

        # 12. Speed trap analysis
        if 'speed_fl' in df.columns:
            max_speed = df['speed_fl'].max()
            df['speed_fl_delta'] = df['speed_fl'] - max_speed
            df['speed_fl_pct'] = (df['speed_fl'] / max_speed) * 100
        else:
            df['speed_fl_delta'] = 0.0
            df['speed_fl_pct'] = 100.0

        # 13. Interaction features
        df['tyre_temp_interaction'] = df['tyre_life'] * df['temp_delta_abs']
        df['fuel_tyre_interaction'] = df['fuel_load_kg'] * df['tyre_life']

        # Fill missing values
        df = df.ffill().bfill().fillna(0)

        return df

    def train(self, laps_df: pd.DataFrame, target_col: str = 'lap_time_seconds',
              cv_splits: int = 5) -> Dict[str, float]:
        """
        Train the regression model with cross-validation

        Args:
            laps_df: DataFrame with lap data
            target_col: Target column name
            cv_splits: Number of CV splits

        Returns:
            Training metrics
        """
        logger.info("Creating features...")
        features_df = self.create_features(laps_df)

        # Define feature columns
        categorical_features = ['compound', 'driver', 'team']
        numerical_features = [
            'lap_number', 'tyre_life', 'tyre_life_squared', 'tyre_life_cubed',
            'track_temp', 'air_temp', 'humidity', 'pressure',
            'fuel_load_kg', 'fuel_effect', 'air_density', 'air_density_index',
            'wind_headwind', 'wind_crosswind',
            'temp_delta', 'temp_delta_abs', 'temp_penalty',
            'tyre_warmup', 'laps_past_peak', 'past_cliff', 'laps_past_cliff', 'cliff_degradation',
            'track_progression', 'track_rubber',
            'stint_lap', 'stint_lap_squared',
            's1_delta', 's2_delta', 's3_delta',
            's1_pct_delta', 's2_pct_delta', 's3_pct_delta',
            'lap_time_rolling_mean_3', 'lap_time_rolling_mean_5',
            'lap_time_rolling_std_3', 'lap_time_rolling_std_5',
            'position', 'position_change', 'fighting_position',
            'speed_fl_delta', 'speed_fl_pct',
            'tyre_temp_interaction', 'fuel_tyre_interaction'
        ]

        # Filter to available features
        available_numerical = [f for f in numerical_features if f in features_df.columns]
        available_categorical = [f for f in categorical_features if f in features_df.columns]

        logger.info(f"Using {len(available_numerical)} numerical and {len(available_categorical)} categorical features")

        # Encode categorical variables
        for col in available_categorical:
            if col not in self.label_encoders:
                self.label_encoders[col] = LabelEncoder()
            features_df[col + '_encoded'] = self.label_encoders[col].fit_transform(features_df[col].astype(str))

        # Prepare features
        encoded_categorical = [f + '_encoded' for f in available_categorical]
        self.feature_names = available_numerical + encoded_categorical

        X = features_df[self.feature_names].values
        y = features_df[target_col].values

        # Remove invalid lap times
        valid_mask = (y > 0) & (y < 300)  # Reasonable lap time range
        X = X[valid_mask]
        y = y[valid_mask]

        logger.info(f"Training on {len(X)} samples")

        # Split train/test (80/20)
        split_idx = int(0.8 * len(X))
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]

        # LightGBM parameters
        params = {
            'objective': 'regression',
            'metric': 'rmse',
            'boosting_type': 'gbdt',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'feature_fraction': 0.8,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'verbose': -1,
            'max_depth': 8,
            'min_child_samples': 20,
            'reg_alpha': 0.1,
            'reg_lambda': 0.1
        }

        # Train model
        logger.info("Training LightGBM model...")
        train_data = lgb.Dataset(X_train, label=y_train)
        test_data = lgb.Dataset(X_test, label=y_test, reference=train_data)

        self.model = lgb.train(
            params,
            train_data,
            num_boost_round=500,
            valid_sets=[train_data, test_data],
            callbacks=[lgb.early_stopping(stopping_rounds=50), lgb.log_evaluation(period=50)]
        )

        # Evaluate
        train_pred = self.model.predict(X_train)
        test_pred = self.model.predict(X_test)

        train_rmse = np.sqrt(mean_squared_error(y_train, train_pred))
        test_rmse = np.sqrt(mean_squared_error(y_test, test_pred))
        train_mae = mean_absolute_error(y_train, train_pred)
        test_mae = mean_absolute_error(y_test, test_pred)
        train_r2 = r2_score(y_train, train_pred)
        test_r2 = r2_score(y_test, test_pred)

        # Feature importance
        importance = self.model.feature_importance(importance_type='gain')
        self.feature_importances = dict(zip(self.feature_names, importance))

        # Sort by importance
        self.feature_importances = dict(sorted(
            self.feature_importances.items(),
            key=lambda x: x[1],
            reverse=True
        ))

        logger.info(f"Training complete!")
        logger.info(f"Train RMSE: {train_rmse:.3f}s, Test RMSE: {test_rmse:.3f}s")
        logger.info(f"Train R²: {train_r2:.3f}, Test R²: {test_r2:.3f}")

        return {
            'train_rmse': train_rmse,
            'test_rmse': test_rmse,
            'train_mae': train_mae,
            'test_mae': test_mae,
            'train_r2': train_r2,
            'test_r2': test_r2
        }

    def predict(self, lap_data: Dict) -> Tuple[float, Dict[str, float]]:
        """
        Predict lap time for single lap

        Args:
            lap_data: Dictionary with lap features

        Returns:
            Predicted lap time and feature contributions
        """
        if self.model is None:
            raise ValueError("Model not trained yet!")

        # Create DataFrame from input
        df = pd.DataFrame([lap_data])

        # Create features
        features_df = self.create_features(df)

        # Encode categorical
        for col in self.label_encoders:
            if col in features_df.columns:
                features_df[col + '_encoded'] = self.label_encoders[col].transform(
                    features_df[col].astype(str)
                )

        # Prepare features
        X = features_df[self.feature_names].values

        # Predict
        prediction = self.model.predict(X)[0]

        return prediction, self.feature_importances

    def save_model(self, path: str):
        """Save model to disk"""
        if self.model is None:
            raise ValueError("No model to save!")

        joblib.dump({
            'model': self.model,
            'label_encoders': self.label_encoders,
            'feature_names': self.feature_names,
            'feature_importances': self.feature_importances
        }, path)
        logger.info(f"Model saved to {path}")

    def load_model(self, path: str):
        """Load model from disk"""
        data = joblib.load(path)
        self.model = data['model']
        self.label_encoders = data['label_encoders']
        self.feature_names = data['feature_names']
        self.feature_importances = data['feature_importances']
        logger.info(f"Model loaded from {path}")
