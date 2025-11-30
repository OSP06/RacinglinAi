/**
 * TypeScript types for ML predictions
 */

export interface LSTMPredictionPoint {
  lap_number: number;
  predicted_lap_time: number;
  confidence_lower: number;
  confidence_upper: number;
}

export interface LSTMPredictionResponse {
  driver: string;
  compound: string;
  predictions: LSTMPredictionPoint[];
  model_rmse: number;
  training_laps_used: number;
  generated_at: string;
}

export interface FeatureImportance {
  feature: string;
  importance: number;
}

export interface RegressionPredictionResponse {
  predicted_lap_time: number;
  actual_lap_time: number | null;
  prediction_error: number | null;
  model_rmse: number;
  model_r2: number;
  feature_importances: FeatureImportance[];
  generated_at: string;
}

export interface PitStop {
  lap_number: number;
  compound_from: string;
  compound_to: string;
  expected_loss_seconds: number;
  confidence: number;
}

export interface StrategyOption {
  strategy_name: string;
  compounds: string[];
  pit_stops: PitStop[];
  expected_race_time: number;
  win_probability: number;
  percentile_10: number;
  percentile_90: number;
  risk_score: number;
}

export interface StrategyPredictionResponse {
  driver: string;
  current_lap: number;
  strategies: StrategyOption[];
  recommended_strategy: string;
  safety_car_probability: number;
  generated_at: string;
}

export interface ModelMetrics {
  model_type: string;
  rmse: number;
  mae: number;
  r2_score: number;
  training_samples: number;
  last_trained: string;
  accuracy_by_compound: Record<string, number>;
}
