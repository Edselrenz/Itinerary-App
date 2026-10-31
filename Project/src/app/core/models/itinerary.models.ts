import { Place } from './place.models';

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
}

export interface ItineraryDay {
  id: string;
  itinerary_id: string;
  day_number: number;
  travel_date: string;
  title?: string | null;
  items: ItineraryItem[];
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
  save_immediately?: boolean;
}

