import type { Place } from './place.models';

export type TravelMode = 'DRIVE' | 'WALK' | 'BICYCLE' | 'TRANSIT';

export interface RouteStepInstruction {
  instruction: string;
  distance_meters: number;
  duration_seconds: number;
  polyline?: string | null;
  start_location?: { latitude: number; longitude: number } | null;
  end_location?: { latitude: number; longitude: number } | null;
  maneuver?: string | null;
}

export interface RouteLegMetadata {
  start_location: { latitude: number; longitude: number };
  end_location: { latitude: number; longitude: number };
  distance_meters: number;
  duration_seconds: number;
  polyline?: string | null;
  steps?: RouteStepInstruction[];
}

export interface ItineraryItem {
  id: string;
  day_id: string;
  place_id?: string | null;
  custom_title?: string | null;
  custom_lat?: number | null;
  custom_lng?: number | null;
  sort_order: number;
  planned_time?: string | null;
  duration_minutes: number;
  notes?: string | null;
  estimated_cost_min?: number | null;
  estimated_cost_max?: number | null;
  created_at?: string;
  updated_at?: string;
  place?: Place | null;

  // GIS & Turn-by-Turn routing extensions
  google_place_id?: string | null;
  travel_mode_from_prev?: TravelMode | string | null;
  travel_distance_meters?: number | null;
  travel_duration_seconds?: number | null;
  route_polyline_from_prev?: string | null;
}

export interface ItineraryDay {
  id: string;
  itinerary_id: string;
  day_number: number;
  travel_date: string;
  title?: string | null;
  items: ItineraryItem[];

  // Day routing overview & turn legs
  day_overview_polyline?: string | null;
  total_distance_meters?: number | null;
  total_travel_duration_seconds?: number | null;
  route_legs?: RouteLegMetadata[];
}

export interface Itinerary {
  id: string;
  user_id?: string;
  title: string;
  destination: string;
  start_date: string;
  end_date: string;
  daily_budget: number;
  preferences: string[];
  type: 'custom' | 'suggested';
  assumptions: string[];
  created_at: string;
  updated_at?: string;
  days: ItineraryDay[];
}

export interface ItineraryItemCreatePayload {
  place_id?: string | null;
  custom_title?: string | null;
  custom_lat?: number | null;
  custom_lng?: number | null;
  sort_order?: number;
  planned_time?: string | null;
  duration_minutes?: number;
  notes?: string | null;
  estimated_cost_min?: number | null;
  estimated_cost_max?: number | null;
  place?: Place | null;

  // GIS & Turn-by-Turn routing extensions
  google_place_id?: string | null;
  place_payload?: Partial<Place> | null;
  travel_mode_from_prev?: TravelMode | string | null;
  travel_distance_meters?: number | null;
  travel_duration_seconds?: number | null;
  route_polyline_from_prev?: string | null;
}

export interface ItineraryDayCreatePayload {
  day_number: number;
  travel_date: string;
  title?: string | null;
  items?: ItineraryItemCreatePayload[];
}

export interface ItineraryCreatePayload {
  title: string;
  destination: string;
  start_date: string;
  end_date: string;
  daily_budget: number;
  preferences?: string[];
  type?: 'custom' | 'suggested';
  assumptions?: string[];
  days?: ItineraryDayCreatePayload[];
}

export interface ItineraryUpdatePayload {
  title?: string;
  destination?: string;
  start_date?: string;
  end_date?: string;
  daily_budget?: number;
  preferences?: string[];
  assumptions?: string[];
  days?: ItineraryDayCreatePayload[];
}

export interface ItineraryReorderEntry {
  id: string;
  day_id: string;
  sort_order: number;
}

export interface SuggestedItineraryRequest {
  title?: string;
  destination: string;
  start_date: string;
  end_date: string;
  daily_budget: number;
  preferences: string[];
  pacing?: 'relaxed' | 'moderate' | 'fast' | string;
  save_immediately?: boolean;
  origin_lat?: number;
  origin_lng?: number;
  travel_mode?: TravelMode | string;
  min_rating?: number;
  include_live_places?: boolean;
  anchor_place_id?: string;
}

export interface RouteComputeRequest {
  origin: { latitude: number; longitude: number };
  destination: { latitude: number; longitude: number };
  intermediates?: Array<{ latitude: number; longitude: number }>;
  travel_mode?: TravelMode | string;
}

export interface RouteComputeResponse {
  overview_polyline: string;
  total_distance_meters: number;
  total_duration_seconds: number;
  legs: RouteLegMetadata[];
  source: 'google_routes' | 'osrm' | 'haversine_direct' | 'cache';
}

export interface ItineraryBudgetSummary {
  verifiedMin: number;
  verifiedMax: number;
  unverifiedCount: number;
  displayText: string;
}
