/**
 * API Client for RacingLineAI Backend
 */

import axios, { AxiosInstance } from 'axios';
import type {
  Season,
  Race,
  Lap,
  RaceDataResponse,
  RaceStatistics,
  CircuitLayout,
} from '../types/race';
import type {
  LSTMPredictionResponse,
  RegressionPredictionResponse,
  StrategyPredictionResponse,
  ModelMetrics,
} from '../types/prediction';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class APIClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  // ========== Race Endpoints ==========

  async getSeasons(): Promise<Season[]> {
    const response = await this.client.get('/api/races/seasons');
    return response.data;
  }

  async getRacesBySeason(year: number): Promise<Race[]> {
    const response = await this.client.get(`/api/races/seasons/${year}/races`);
    return response.data;
  }

  async getRace(raceId: number): Promise<Race> {
    const response = await this.client.get(`/api/races/races/${raceId}`);
    return response.data;
  }

  async getRaceLaps(
    raceId: number,
    params?: {
      driver?: string;
      lap_number?: number;
      min_lap?: number;
      max_lap?: number;
      compound?: string;
      valid_only?: boolean;
      page?: number;
      page_size?: number;
    }
  ): Promise<Lap[]> {
    const response = await this.client.get(`/api/races/races/${raceId}/laps`, {
      params,
    });
    return response.data;
  }

  // Alias for getRaceLaps
  async getLaps(
    raceId: number,
    params?: {
      driver?: string;
      lap_number?: number;
      min_lap?: number;
      max_lap?: number;
      compound?: string;
      valid_only?: boolean;
      page?: number;
      page_size?: number;
    }
  ): Promise<Lap[]> {
    return this.getRaceLaps(raceId, params);
  }

  async getRaceStatistics(
    raceId: number,
    drivers?: string[]
  ): Promise<RaceStatistics[]> {
    const response = await this.client.get(
      `/api/races/races/${raceId}/statistics`,
      {
        params: { drivers },
      }
    );
    return response.data;
  }

  async getRaceData(params: {
    season?: number;
    grand_prix?: string;
    drivers?: string[];
    page?: number;
    page_size?: number;
  }): Promise<RaceDataResponse> {
    const response = await this.client.get('/api/races/data', { params });
    return response.data;
  }

  async getDrivers(season?: number): Promise<string[]> {
    const response = await this.client.get('/api/races/drivers', {
      params: { season },
    });
    return response.data;
  }

  async getTeams(season?: number): Promise<string[]> {
    const response = await this.client.get('/api/races/teams', {
      params: { season },
    });
    return response.data;
  }

  // ========== Circuit Endpoints ==========

  async getCircuitLayout(raceId: number): Promise<CircuitLayout> {
    const response = await this.client.get(`/api/circuits/${raceId}/layout`);
    return response.data;
  }

  async listCircuits(season?: number): Promise<any[]> {
    const response = await this.client.get('/api/circuits/list', {
      params: { season },
    });
    return response.data;
  }

  // ========== Prediction Endpoints ==========

  async predictLSTM(params: {
    race_id: number;
    driver: string;
    compound: string;
    forecast_laps?: number;
  }): Promise<LSTMPredictionResponse> {
    const response = await this.client.post('/api/predictions/lstm', params);
    return response.data;
  }

  async predictRegression(params: {
    race_id: number;
    driver: string;
    lap_number: number;
    compound: string;
    tyre_life: number;
    track_temp: number;
    air_temp?: number;
    fuel_load?: number;
  }): Promise<RegressionPredictionResponse> {
    const response = await this.client.post(
      '/api/predictions/regression',
      params
    );
    return response.data;
  }

  async predictStrategy(params: {
    race_id: number;
    driver: string;
    current_lap?: number;
    available_compounds?: string[];
  }): Promise<StrategyPredictionResponse> {
    const response = await this.client.post('/api/predictions/strategy', params);
    return response.data;
  }

  async getModelMetrics(): Promise<ModelMetrics[]> {
    const response = await this.client.get('/api/predictions/models/metrics');
    return response.data;
  }

  // ========== Telemetry Endpoints ==========

  async getLapTelemetry(
    raceId: number,
    driver: string,
    lapNumber: number
  ): Promise<any> {
    const response = await this.client.get(
      `/api/telemetry/${raceId}/driver/${driver}/lap/${lapNumber}`
    );
    return response.data;
  }

  async compareTelemetry(
    raceId: number,
    driver1: string,
    driver2: string,
    lapNumber?: number
  ): Promise<any> {
    const response = await this.client.get(
      `/api/telemetry/${raceId}/comparison`,
      {
        params: { driver1, driver2, lap_number: lapNumber },
      }
    );
    return response.data;
  }
}

// Export singleton instance
export const apiClient = new APIClient();

// Export class for testing
export default APIClient;
