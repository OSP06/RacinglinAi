/**
 * TypeScript types for race data
 */

export enum CompoundType {
  SOFT = 'SOFT',
  MEDIUM = 'MEDIUM',
  HARD = 'HARD',
  INTERMEDIATE = 'INTERMEDIATE',
  WET = 'WET',
}

export enum StintType {
  OPENING = 'OPENING',
  MID = 'MID',
  CLOSING = 'CLOSING',
}

export enum TrackStatus {
  GREEN = 'GREEN',
  YELLOW = 'YELLOW',
  SC = 'SC',
  VSC = 'VSC',
  RED = 'RED',
}

export interface Season {
  id: number;
  year: number;
}

export interface Race {
  id: number;
  season_id: number;
  grand_prix: string;
  gp_slug: string;
  event_date: string;
  round_number: number | null;
  circuit_name: string;
  circuit_short: string | null;
  circuit_country: string | null;
  track_length_km: number | null;
  altitude_m: number | null;
  circuit_type: string | null;
}

export interface Lap {
  id: number;
  race_id: number;
  driver: string;
  driver_number: number | null;
  team: string;
  lap_number: number;
  lap_time: string | null;
  lap_time_seconds: number | null;
  sector1_time_seconds: number | null;
  sector2_time_seconds: number | null;
  sector3_time_seconds: number | null;
  sector1_pct: number | null;
  sector2_pct: number | null;
  sector3_pct: number | null;
  speed_i1: number | null;
  speed_i2: number | null;
  speed_fl: number | null;
  speed_st: number | null;
  compound: CompoundType | null;
  tyre_life: number | null;
  is_fresh_tyre: boolean;
  stint: number | null;
  stint_type: StintType | null;
  position: number | null;
  track_status: TrackStatus | null;
  is_personal_best: boolean;
  is_valid_lap: boolean;
  is_accurate: boolean;
  delta_to_fastest_lap: number | null;
  is_pit_out_lap?: boolean;
  is_pit_in_lap?: boolean;
}

export interface WeatherData {
  id: number;
  race_id: number;
  lap_number: number | null;
  air_temp: number | null;
  track_temp: number | null;
  humidity: number | null;
  pressure: number | null;
  wind_speed: number | null;
  wind_direction: number | null;
  rainfall: boolean;
  air_density: number | null;
}

export interface RaceStatistics {
  driver: string;
  team: string;
  total_laps: number;
  avg_lap_time: number;
  fastest_lap: number;
  pit_stops: number;
  positions_gained: number;
  final_position: number;
}

export interface RaceDataResponse {
  race: Race;
  laps: Lap[];
  weather: WeatherData[];
  statistics: RaceStatistics[];
  total_laps: number;
  page: number;
  page_size: number;
}

export interface CircuitLayout {
  circuit_name: string;
  circuit_country: string;
  track_length_km: number | null;
  altitude_m: number | null;
  coordinates: {
    x: number;
    y: number;
    speed: number;
    distance: number;
  }[];
  fastest_lap_time: string | null;
  fastest_lap_driver: string | null;
}
