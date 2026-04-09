"""
Sequence-based Lap Time Predictor
Uses sklearn MLPRegressor on flattened sliding-window sequences —
same feature engineering as the original LSTM, no PyTorch required.
"""

import numpy as np
import pandas as pd
import joblib
from typing import Tuple, List, Dict, Optional
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error
import logging

logger = logging.getLogger(__name__)


class LSTMPredictor:
    """
    Sequence-based lap-time predictor with the same public interface
    as the original PyTorch LSTMPredictor.  The model is an MLP trained
    on flattened sliding-window sequences so it captures temporal context
    without requiring torch.
    """

    def __init__(self, sequence_length: int = 10, input_features: int = 25):
        self.sequence_length = sequence_length
        self.input_features = input_features
        self.model: Optional[MLPRegressor] = None
        self.scaler_X = StandardScaler()
        self.scaler_y = StandardScaler()
        self._train_rmse: float = 0.35
        self._test_rmse: float = 0.35

    # ------------------------------------------------------------------ #
    #  Feature engineering (pure pandas / numpy — unchanged)              #
    # ------------------------------------------------------------------ #

    def create_features(self, laps_df: pd.DataFrame) -> pd.DataFrame:
        """
        Create enhanced feature set from lap data.
        """
        df = laps_df.copy()

        total_laps = df['lap_number'].max()

        # 1. Fuel load
        df['fuel_load_estimated'] = (total_laps - df['lap_number']) * 2.0

        # 2. Air density
        if 'pressure' in df.columns and 'air_temp' in df.columns:
            df['air_density'] = (df['pressure'] * 100) / (287.05 * (df['air_temp'] + 273.15))
        else:
            df['air_density'] = 1.225

        # 3. Wind
        if 'wind_speed' in df.columns and 'wind_direction' in df.columns:
            df['effective_wind'] = df['wind_speed'] * np.cos(np.radians(df['wind_direction']))
        else:
            df['effective_wind'] = 0.0

        # 4. Tyre modelling
        optimal_temps = {'SOFT': 100, 'MEDIUM': 105, 'HARD': 110, 'INTERMEDIATE': 80, 'WET': 70}
        peak_laps     = {'SOFT': 3,   'MEDIUM': 5,   'HARD': 7,   'INTERMEDIATE': 2,  'WET': 2}
        cliff_laps    = {'SOFT': 15,  'MEDIUM': 25,  'HARD': 35,  'INTERMEDIATE': 20, 'WET': 25}

        df['optimal_track_temp'] = df['compound'].map(optimal_temps).fillna(100)
        df['peak_lap']           = df['compound'].map(peak_laps).fillna(5)
        df['cliff_lap']          = df['compound'].map(cliff_laps).fillna(25)

        if 'track_temp' in df.columns:
            df['temp_from_optimal'] = np.abs(df['track_temp'] - df['optimal_track_temp'])
        else:
            df['temp_from_optimal'] = 0.0

        df['tyre_warmup_state'] = np.minimum(df['tyre_life'] / df['peak_lap'], 1.0)
        df['past_cliff']        = (df['tyre_life'] > df['cliff_lap']).astype(int)

        # 5. Track evolution
        df['track_rubber_buildup'] = df['lap_number'] / total_laps
        df['session_progression']  = df['lap_number'] / total_laps

        # 6. Sector deltas
        if 'sector1_time_seconds' in df.columns:
            df['sector1_delta'] = df['sector1_time_seconds'] - df['sector1_time_seconds'].min()
            df['sector2_delta'] = df['sector2_time_seconds'] - df['sector2_time_seconds'].min()
            df['sector3_delta'] = df['sector3_time_seconds'] - df['sector3_time_seconds'].min()
        else:
            df['sector1_delta'] = df['sector2_delta'] = df['sector3_delta'] = 0.0

        # 7. Speed trap
        if 'speed_fl' in df.columns:
            df['speed_trap_delta'] = df['speed_fl'] - df['speed_fl'].max()
        else:
            df['speed_trap_delta'] = 0.0

        # 8. Temporal lap features
        df['prev_lap_time']  = df.groupby('driver')['lap_time_seconds'].shift(1)
        df['lap_time_trend'] = (
            df.groupby('driver')['lap_time_seconds']
            .rolling(3, min_periods=1).mean()
            .reset_index(0, drop=True)
        )
        df['pace_variance'] = (
            df.groupby('driver')['lap_time_seconds']
            .rolling(5, min_periods=1).std()
            .reset_index(0, drop=True)
        )

        # 9. Gap / DRS context
        if 'position' in df.columns:
            df['gap_to_car_ahead']  = df.groupby('lap_number')['lap_time_seconds'].shift(1)
            df['gap_to_car_behind'] = df.groupby('lap_number')['lap_time_seconds'].shift(-1)
            df['in_drs_range'] = ((df['gap_to_car_ahead'] < 1.0) & (df['gap_to_car_ahead'] > 0)).astype(int)
            df['defending']    = ((df['gap_to_car_behind'] < 1.0) & (df['gap_to_car_behind'] > 0)).astype(int)
        else:
            df['gap_to_car_ahead'] = df['gap_to_car_behind'] = 0.0
            df['in_drs_range'] = df['defending'] = 0

        # 10. Compound encoding
        compound_encoding = {'SOFT': 1, 'MEDIUM': 2, 'HARD': 3, 'INTERMEDIATE': 4, 'WET': 5}
        df['compound_encoded'] = df['compound'].map(compound_encoding).fillna(2)

        df = df.ffill().bfill().fillna(0)
        return df

    def prepare_sequences(
        self,
        features_df: pd.DataFrame,
        target_col: str = 'lap_time_seconds',
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Build sliding-window sequences.
        Returns X shape (n_samples, seq_len, n_features) and y shape (n_samples,).
        """
        feature_cols = [
            'lap_number', 'tyre_life', 'compound_encoded', 'track_temp',
            'fuel_load_estimated', 'air_density', 'effective_wind',
            'tyre_warmup_state', 'past_cliff', 'temp_from_optimal',
            'track_rubber_buildup', 'session_progression',
            'sector1_delta', 'sector2_delta', 'sector3_delta',
            'speed_trap_delta', 'prev_lap_time', 'lap_time_trend', 'pace_variance',
            'gap_to_car_ahead', 'gap_to_car_behind', 'in_drs_range', 'defending',
            'position', 'stint',
        ]
        available_cols = [c for c in feature_cols if c in features_df.columns]
        logger.info(f"Using {len(available_cols)} features: {available_cols}")

        X_data = features_df[available_cols].values
        y_data = features_df[target_col].values

        X_seqs, y_seqs = [], []
        for i in range(len(X_data) - self.sequence_length):
            X_seqs.append(X_data[i: i + self.sequence_length])
            y_seqs.append(y_data[i + self.sequence_length])

        return np.array(X_seqs), np.array(y_seqs)

    # ------------------------------------------------------------------ #
    #  Training                                                            #
    # ------------------------------------------------------------------ #

    def train(
        self,
        laps_df: pd.DataFrame,
        epochs: int = 100,          # kept for API compatibility, maps to max_iter
        learning_rate: float = 0.001,
        batch_size: int = 32,
    ) -> Dict[str, List[float]]:
        """
        Train the MLP on sliding-window sequences.
        `epochs` is passed as `max_iter` to MLPRegressor.
        """
        logger.info("Creating features …")
        features_df = self.create_features(laps_df)

        logger.info("Preparing sequences …")
        X, y = self.prepare_sequences(features_df)

        if len(X) < 2:
            raise ValueError("Not enough laps to build training sequences.")

        self.input_features = X.shape[2]

        # Flatten sequences → (n_samples, seq_len * n_features)
        n_samples = X.shape[0]
        X_flat = X.reshape(n_samples, -1)

        split_idx = int(0.8 * n_samples)
        X_train, X_test = X_flat[:split_idx], X_flat[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]

        X_train_scaled = self.scaler_X.fit_transform(X_train)
        X_test_scaled  = self.scaler_X.transform(X_test)

        y_train_scaled = self.scaler_y.fit_transform(y_train.reshape(-1, 1)).ravel()
        y_test_scaled  = self.scaler_y.transform(y_test.reshape(-1, 1)).ravel()

        logger.info(f"Training MLP on {len(X_train)} samples …")
        self.model = MLPRegressor(
            hidden_layer_sizes=(128, 64, 32),
            activation='relu',
            solver='adam',
            learning_rate_init=learning_rate,
            max_iter=max(epochs, 200),
            early_stopping=True,
            validation_fraction=0.1,
            n_iter_no_change=20,
            random_state=42,
            verbose=False,
        )
        self.model.fit(X_train_scaled, y_train_scaled)

        train_pred = self.scaler_y.inverse_transform(
            self.model.predict(X_train_scaled).reshape(-1, 1)
        ).ravel()
        test_pred = self.scaler_y.inverse_transform(
            self.model.predict(X_test_scaled).reshape(-1, 1)
        ).ravel()

        self._train_rmse = float(np.sqrt(mean_squared_error(y_train, train_pred)))
        self._test_rmse  = float(np.sqrt(mean_squared_error(y_test, test_pred)))
        logger.info(f"Training done — train RMSE: {self._train_rmse:.4f}s  test RMSE: {self._test_rmse:.4f}s")

        return {
            'train_loss': [self._train_rmse],
            'test_loss':  [self._test_rmse],
        }

    # ------------------------------------------------------------------ #
    #  Inference                                                           #
    # ------------------------------------------------------------------ #

    def predict(
        self,
        laps_df: pd.DataFrame,
        forecast_laps: int = 15,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Predict future lap times using auto-regression over the last window.
        Returns (predictions, lower_bound, upper_bound).
        """
        if self.model is None:
            raise ValueError("Model not trained yet!")

        features_df = self.create_features(laps_df)
        X, _ = self.prepare_sequences(features_df)

        if len(X) == 0:
            raise ValueError("Not enough laps to build a prediction sequence.")

        # Start from the last observed window (shape: seq_len × n_features)
        current_window = X[-1].copy()  # (seq_len, n_features)

        predictions, uncertainties = [], []

        for _ in range(forecast_laps):
            flat = current_window.reshape(1, -1)
            flat_scaled = self.scaler_X.transform(flat)

            pred_scaled = self.model.predict(flat_scaled)
            pred = float(self.scaler_y.inverse_transform(pred_scaled.reshape(-1, 1))[0, 0])
            predictions.append(pred)

            # Uncertainty grows with forecast horizon (conservative ±0.5 s base)
            uncertainties.append(0.5 + 0.02 * len(predictions))

            # Roll window: drop oldest row, append a synthetic new row
            new_row = current_window[-1].copy()
            current_window = np.roll(current_window, -1, axis=0)
            current_window[-1] = new_row

        predictions  = np.array(predictions)
        uncertainties = np.array(uncertainties)

        return predictions, predictions - 2 * uncertainties, predictions + 2 * uncertainties

    # ------------------------------------------------------------------ #
    #  Persistence                                                         #
    # ------------------------------------------------------------------ #

    def save_model(self, path: str):
        """Save model and scalers with joblib."""
        if self.model is None:
            raise ValueError("No model to save!")
        joblib.dump({
            'model':          self.model,
            'scaler_X':       self.scaler_X,
            'scaler_y':       self.scaler_y,
            'input_features': self.input_features,
            'sequence_length': self.sequence_length,
            'train_rmse':     self._train_rmse,
            'test_rmse':      self._test_rmse,
        }, path)
        logger.info(f"Model saved to {path}")

    def load_model(self, path: str):
        """Load model and scalers from joblib file."""
        checkpoint = joblib.load(path)
        self.model           = checkpoint['model']
        self.scaler_X        = checkpoint['scaler_X']
        self.scaler_y        = checkpoint['scaler_y']
        self.input_features  = checkpoint['input_features']
        self.sequence_length = checkpoint['sequence_length']
        self._train_rmse     = checkpoint.get('train_rmse', 0.35)
        self._test_rmse      = checkpoint.get('test_rmse', 0.35)
        logger.info(f"Model loaded from {path}")
