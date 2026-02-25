/**
 * TypeScript type definitions corresponding to backend/app/schemas.py
 */

export interface Location {
  lat: number;
  lng: number;
  name?: string;
}

export type Difficulty = 'easy' | 'moderate' | 'hard';

export interface RoutePreferences {
  difficulty: Difficulty;
  avoid_traffic: boolean;
  prefer_scenic: boolean;
  max_distance_km?: number;
  max_elevation_gain_m?: number;
}

export interface PlanRequest {
  origin: Location;
  destination: Location;
  preferences: RoutePreferences;
  departure_time: string; // ISO 8601 datetime string
}

export type SurfaceType = 'paved' | 'gravel' | 'dirt';

export interface RouteSegment {
  coordinates: [number, number][]; // [lat, lng]
  elevations?: number[]; // Elevation in meters for each coordinate point
  distance_km: number;
  elevation_gain_m: number;
  elevation_loss_m: number;
  estimated_duration_min: number;
  surface_type: SurfaceType;
}

export interface WeatherForecast {
  time: string; // ISO 8601 datetime string
  temperature: number;
  wind_speed: number;
  wind_direction: number;
  precipitation_probability: number;
  weather_code: number;
  description: string;
}

export interface RoutePlan {
  id: string;
  segments: RouteSegment[];
  total_distance_km: number;
  total_elevation_gain_m: number;
  total_duration_min: number;
  weather_forecasts: WeatherForecast[];
  llm_analysis: string;
  warnings: string[];
  recommended_gear: string[];
  created_at: string; // ISO 8601 datetime string
}

export interface ElevationPoint {
  distance_km: number;
  elevation_m: number;
}

export interface ElevationProfile {
  points: ElevationPoint[];
}

// API Response types
export interface GeocodeResponse {
  data: Location[];
}

// SSE Event types
export type SSEEvent =
  | { type: 'route_data'; data: Omit<RoutePlan, 'weather_forecasts' | 'llm_analysis'> }
  | { type: 'weather'; data: WeatherForecast[] }
  | { type: 'token'; data: string }
  | { type: 'done' }
  | { type: 'error'; data: string };
