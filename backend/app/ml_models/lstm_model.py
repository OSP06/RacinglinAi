"""
Enhanced LSTM Model for Lap Time Prediction
Multi-feature LSTM with attention mechanism
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import pandas as pd
from typing import Tuple, List, Dict, Optional
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit
import logging

logger = logging.getLogger(__name__)


class EnhancedLSTMModel(nn.Module):
    """
    Enhanced LSTM with attention for lap time forecasting
    """

    def __init__(self, input_features: int = 25, hidden_size_1: int = 128,
                 hidden_size_2: int = 64, num_heads: int = 4, dropout: float = 0.2):
        super(EnhancedLSTMModel, self).__init__()

        self.input_features = input_features
        self.hidden_size_1 = hidden_size_1
        self.hidden_size_2 = hidden_size_2

        # LSTM layers
        self.lstm1 = nn.LSTM(input_features, hidden_size_1, batch_first=True)
        self.lstm2 = nn.LSTM(hidden_size_1, hidden_size_2, batch_first=True)

        # Attention mechanism
        self.attention = nn.MultiheadAttention(hidden_size_2, num_heads=num_heads, batch_first=True)

        # Fully connected layers
        self.fc1 = nn.Linear(hidden_size_2, 32)
        self.fc2 = nn.Linear(32, 1)

        # Dropout for regularization
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        """
        Forward pass
        Args:
            x: Input tensor of shape (batch, sequence_length, features)
        Returns:
            Predicted lap time
        """
        # LSTM layers
        lstm_out1, _ = self.lstm1(x)
        lstm_out2, _ = self.lstm2(lstm_out1)

        # Attention mechanism
        attn_out, _ = self.attention(lstm_out2, lstm_out2, lstm_out2)

        # Take last timestep
        last_timestep = attn_out[:, -1, :]

        # Fully connected layers
        x = F.relu(self.fc1(self.dropout(last_timestep)))
        output = self.fc2(x)

        return output


class LSTMPredictor:
    """
    LSTM predictor with training and inference capabilities
    """

    def __init__(self, sequence_length: int = 10, input_features: int = 25):
        self.sequence_length = sequence_length
        self.input_features = input_features
        self.model = None
        self.scaler_X = StandardScaler()
        self.scaler_y = StandardScaler()
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"Using device: {self.device}")

    def create_features(self, laps_df: pd.DataFrame) -> pd.DataFrame:
        """
        Create enhanced feature set from lap data

        Features include:
        - Physical factors (fuel, air density, wind)
        - Tyre modeling (warmup, degradation, temperature)
        - Track evolution
        - Performance context
        - Driver/team factors
        - Race context
        """
        df = laps_df.copy()

        # Total laps in race
        total_laps = df['lap_number'].max()

        # 1. Fuel load estimation
        df['fuel_load_estimated'] = (total_laps - df['lap_number']) * 2.0  # kg

        # 2. Air density (if weather data available)
        if 'pressure' in df.columns and 'air_temp' in df.columns:
            df['air_density'] = (df['pressure'] * 100) / (287.05 * (df['air_temp'] + 273.15))
        else:
            df['air_density'] = 1.225  # Standard air density

        # 3. Effective wind (if available)
        if 'wind_speed' in df.columns and 'wind_direction' in df.columns:
            # Simplified: assume headwind reduces lap time
            df['effective_wind'] = df['wind_speed'] * np.cos(np.radians(df['wind_direction']))
        else:
            df['effective_wind'] = 0.0

        # 4. Tyre modeling
        # Optimal temperatures per compound
        optimal_temps = {
            'SOFT': 100,
            'MEDIUM': 105,
            'HARD': 110,
            'INTERMEDIATE': 80,
            'WET': 70
        }

        # Peak performance lap per compound
        peak_laps = {
            'SOFT': 3,
            'MEDIUM': 5,
            'HARD': 7,
            'INTERMEDIATE': 2,
            'WET': 2
        }

        # Cliff lap per compound
        cliff_laps = {
            'SOFT': 15,
            'MEDIUM': 25,
            'HARD': 35,
            'INTERMEDIATE': 20,
            'WET': 25
        }

        df['optimal_track_temp'] = df['compound'].map(optimal_temps).fillna(100)
        df['peak_lap'] = df['compound'].map(peak_laps).fillna(5)
        df['cliff_lap'] = df['compound'].map(cliff_laps).fillna(25)

        # Temperature delta from optimal
        if 'track_temp' in df.columns:
            df['temp_from_optimal'] = np.abs(df['track_temp'] - df['optimal_track_temp'])
        else:
            df['temp_from_optimal'] = 0.0

        # Tyre warmup state (0 to 1)
        df['tyre_warmup_state'] = np.minimum(df['tyre_life'] / df['peak_lap'], 1.0)

        # Past cliff flag
        df['past_cliff'] = (df['tyre_life'] > df['cliff_lap']).astype(int)

        # 5. Track evolution
        df['track_rubber_buildup'] = df['lap_number'] / total_laps
        df['session_progression'] = df['lap_number'] / total_laps

        # 6. Performance context (deltas from best)
        if 'sector1_time_seconds' in df.columns:
            best_s1 = df['sector1_time_seconds'].min()
            best_s2 = df['sector2_time_seconds'].min()
            best_s3 = df['sector3_time_seconds'].min()

            df['sector1_delta'] = df['sector1_time_seconds'] - best_s1
            df['sector2_delta'] = df['sector2_time_seconds'] - best_s2
            df['sector3_delta'] = df['sector3_time_seconds'] - best_s3
        else:
            df['sector1_delta'] = 0.0
            df['sector2_delta'] = 0.0
            df['sector3_delta'] = 0.0

        # 7. Speed trap delta (if available)
        if 'speed_fl' in df.columns:
            fastest_speed = df['speed_fl'].max()
            df['speed_trap_delta'] = df['speed_fl'] - fastest_speed
        else:
            df['speed_trap_delta'] = 0.0

        # 8. Previous lap features
        df['prev_lap_time'] = df.groupby('driver')['lap_time_seconds'].shift(1)
        df['lap_time_trend'] = df.groupby('driver')['lap_time_seconds'].rolling(3, min_periods=1).mean().reset_index(0, drop=True)
        df['pace_variance'] = df.groupby('driver')['lap_time_seconds'].rolling(5, min_periods=1).std().reset_index(0, drop=True)

        # 9. Position and gap context (if available)
        if 'position' in df.columns:
            df['gap_to_car_ahead'] = df.groupby('lap_number')['lap_time_seconds'].shift(1)
            df['gap_to_car_behind'] = df.groupby('lap_number')['lap_time_seconds'].shift(-1)
            df['in_drs_range'] = ((df['gap_to_car_ahead'] < 1.0) & (df['gap_to_car_ahead'] > 0)).astype(int)
            df['defending'] = ((df['gap_to_car_behind'] < 1.0) & (df['gap_to_car_behind'] > 0)).astype(int)
        else:
            df['gap_to_car_ahead'] = 0.0
            df['gap_to_car_behind'] = 0.0
            df['in_drs_range'] = 0
            df['defending'] = 0

        # 10. Encode categorical variables
        # Compound
        compound_encoding = {
            'SOFT': 1,
            'MEDIUM': 2,
            'HARD': 3,
            'INTERMEDIATE': 4,
            'WET': 5
        }
        df['compound_encoded'] = df['compound'].map(compound_encoding).fillna(2)

        # Fill NaN values
        df = df.fillna(method='ffill').fillna(method='bfill').fillna(0)

        return df

    def prepare_sequences(self, features_df: pd.DataFrame, target_col: str = 'lap_time_seconds') -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare sequences for LSTM training

        Args:
            features_df: DataFrame with features
            target_col: Target column name

        Returns:
            X, y arrays for training
        """
        # Select feature columns
        feature_cols = [
            'lap_number', 'tyre_life', 'compound_encoded', 'track_temp',
            'fuel_load_estimated', 'air_density', 'effective_wind',
            'tyre_warmup_state', 'past_cliff', 'temp_from_optimal',
            'track_rubber_buildup', 'session_progression',
            'sector1_delta', 'sector2_delta', 'sector3_delta',
            'speed_trap_delta', 'prev_lap_time', 'lap_time_trend', 'pace_variance',
            'gap_to_car_ahead', 'gap_to_car_behind', 'in_drs_range', 'defending',
            'position', 'stint'
        ]

        # Filter to available columns
        available_cols = [col for col in feature_cols if col in features_df.columns]
        logger.info(f"Using {len(available_cols)} features: {available_cols}")

        X_data = features_df[available_cols].values
        y_data = features_df[target_col].values

        # Create sequences
        X_sequences = []
        y_sequences = []

        for i in range(len(X_data) - self.sequence_length):
            X_sequences.append(X_data[i:i + self.sequence_length])
            y_sequences.append(y_data[i + self.sequence_length])

        X_sequences = np.array(X_sequences)
        y_sequences = np.array(y_sequences)

        return X_sequences, y_sequences

    def train(self, laps_df: pd.DataFrame, epochs: int = 100, learning_rate: float = 0.001,
              batch_size: int = 32) -> Dict[str, List[float]]:
        """
        Train the LSTM model

        Args:
            laps_df: DataFrame with lap data
            epochs: Number of training epochs
            learning_rate: Learning rate
            batch_size: Batch size

        Returns:
            Training history
        """
        logger.info("Creating features...")
        features_df = self.create_features(laps_df)

        logger.info("Preparing sequences...")
        X, y = self.prepare_sequences(features_df)

        # Update input features based on actual data
        self.input_features = X.shape[2]

        # Split into train and test
        split_idx = int(0.8 * len(X))
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]

        # Normalize data
        # Reshape for scaling
        X_train_reshaped = X_train.reshape(-1, X_train.shape[-1])
        X_test_reshaped = X_test.reshape(-1, X_test.shape[-1])

        X_train_scaled = self.scaler_X.fit_transform(X_train_reshaped)
        X_test_scaled = self.scaler_X.transform(X_test_reshaped)

        # Reshape back
        X_train_scaled = X_train_scaled.reshape(X_train.shape)
        X_test_scaled = X_test_scaled.reshape(X_test.shape)

        y_train_scaled = self.scaler_y.fit_transform(y_train.reshape(-1, 1)).flatten()
        y_test_scaled = self.scaler_y.transform(y_test.reshape(-1, 1)).flatten()

        # Convert to tensors
        X_train_tensor = torch.FloatTensor(X_train_scaled).to(self.device)
        y_train_tensor = torch.FloatTensor(y_train_scaled).to(self.device)
        X_test_tensor = torch.FloatTensor(X_test_scaled).to(self.device)
        y_test_tensor = torch.FloatTensor(y_test_scaled).to(self.device)

        # Initialize model
        self.model = EnhancedLSTMModel(input_features=self.input_features).to(self.device)

        # Loss and optimizer
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate)

        # Training loop
        history = {'train_loss': [], 'test_loss': []}

        logger.info(f"Training on {len(X_train)} samples, testing on {len(X_test)} samples")

        for epoch in range(epochs):
            self.model.train()

            # Mini-batch training
            for i in range(0, len(X_train_tensor), batch_size):
                batch_X = X_train_tensor[i:i + batch_size]
                batch_y = y_train_tensor[i:i + batch_size]

                # Forward pass
                outputs = self.model(batch_X).squeeze()
                loss = criterion(outputs, batch_y)

                # Backward pass
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

            # Evaluate
            self.model.eval()
            with torch.no_grad():
                train_pred = self.model(X_train_tensor).squeeze()
                train_loss = criterion(train_pred, y_train_tensor).item()

                test_pred = self.model(X_test_tensor).squeeze()
                test_loss = criterion(test_pred, y_test_tensor).item()

            history['train_loss'].append(train_loss)
            history['test_loss'].append(test_loss)

            if (epoch + 1) % 10 == 0:
                logger.info(f"Epoch {epoch + 1}/{epochs} - Train Loss: {train_loss:.4f}, Test Loss: {test_loss:.4f}")

        logger.info("Training completed!")
        return history

    def predict(self, laps_df: pd.DataFrame, forecast_laps: int = 15) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Predict future lap times

        Args:
            laps_df: Historical lap data
            forecast_laps: Number of laps to forecast

        Returns:
            predictions, lower_bound, upper_bound arrays
        """
        if self.model is None:
            raise ValueError("Model not trained yet!")

        self.model.eval()

        # Create features
        features_df = self.create_features(laps_df)
        X, _ = self.prepare_sequences(features_df)

        # Use last sequence as starting point
        current_sequence = X[-1:].copy()

        # Normalize
        current_sequence_reshaped = current_sequence.reshape(-1, current_sequence.shape[-1])
        current_sequence_scaled = self.scaler_X.transform(current_sequence_reshaped)
        current_sequence_scaled = current_sequence_scaled.reshape(current_sequence.shape)

        predictions = []
        uncertainties = []

        with torch.no_grad():
            for _ in range(forecast_laps):
                # Predict
                input_tensor = torch.FloatTensor(current_sequence_scaled).to(self.device)
                pred_scaled = self.model(input_tensor).cpu().numpy()

                # Denormalize
                pred = self.scaler_y.inverse_transform(pred_scaled.reshape(-1, 1))[0, 0]
                predictions.append(pred)

                # Estimate uncertainty (simplified - could use Monte Carlo dropout)
                uncertainty = 0.5  # seconds - conservative estimate
                uncertainties.append(uncertainty)

                # Update sequence for next prediction
                # This is simplified - in production, you'd update all features
                current_sequence_scaled = np.roll(current_sequence_scaled, -1, axis=1)

        predictions = np.array(predictions)
        uncertainties = np.array(uncertainties)

        lower_bound = predictions - 2 * uncertainties  # 95% confidence
        upper_bound = predictions + 2 * uncertainties

        return predictions, lower_bound, upper_bound

    def save_model(self, path: str):
        """Save model to disk"""
        if self.model is None:
            raise ValueError("No model to save!")

        torch.save({
            'model_state_dict': self.model.state_dict(),
            'scaler_X': self.scaler_X,
            'scaler_y': self.scaler_y,
            'input_features': self.input_features,
            'sequence_length': self.sequence_length
        }, path)
        logger.info(f"Model saved to {path}")

    def load_model(self, path: str):
        """Load model from disk"""
        checkpoint = torch.load(path, map_location=self.device)

        self.input_features = checkpoint['input_features']
        self.sequence_length = checkpoint['sequence_length']
        self.scaler_X = checkpoint['scaler_X']
        self.scaler_y = checkpoint['scaler_y']

        self.model = EnhancedLSTMModel(input_features=self.input_features).to(self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.eval()

        logger.info(f"Model loaded from {path}")
