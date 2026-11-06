export interface Municipality {
  id: string;
  name: string;
  slug: string;
  is_city: boolean;
  center_lat: number;
  center_lng: number;
}

export interface PlacePhoto {
  name?: string | null;
  width_px?: number | null;
  height_px?: number | null;
  author_attributions?: Array<Record<string, unknown>>;
  photo_uri?: string | null;
}

export interface PlaceReview {
  name?: string | null;
  author_name?: string | null;
  author_photo_uri?: string | null;
  rating?: number | null;
  text?: string | null;
  publish_time?: string | null;
  relative_publish_time_description?: string | null;
}

export interface PlaceRegularOpeningHours {
  open_now?: boolean | null;
  periods?: Array<Record<string, unknown>>;
  weekday_descriptions?: string[];
}

export interface Place {
  id: string;
  name: string;
  category: string;
  latitude: number;
  longitude: number;
  municipality_id?: string | null;
  municipality_name?: string | null;
  address_text?: string | null;
  description?: string | null;
  phone?: string | null;
  website?: string | null;
  opening_hours?: string | null;
  estimated_cost_min?: number | null;
  estimated_cost_max?: number | null;
  cost_currency: string;
  image_url?: string | null;
  image_license?: string | null;
  source_name: string;
  source_record_id: string;
  source_url?: string | null;
  imported_at: string;
  verified_at?: string | null;
  is_featured: boolean;
  tags: string[];
  directions_url: string;

  // Google Places API (New) & GIS Extensions
  google_place_id?: string | null;
  google_types?: string[];
  editorial_summary?: string | null;
  regular_opening_hours?: PlaceRegularOpeningHours | null;
  rating?: number | null;
  user_rating_count?: number | null;
  price_level?: number | null;
  photos?: PlacePhoto[];
  reviews?: PlaceReview[];
  business_status?: string | null;
  google_maps_uri?: string | null;
  details_cached_at?: string | null;
}

export interface PaginatedPlaces {
  total: number;
  limit: number;
  offset: number;
  items: Place[];
}

export interface PlaceSearchParams {
  q?: string;
  categories?: string[] | string;
  municipality_id?: string;
  featured?: boolean;
  min_lat?: number;
  max_lat?: number;
  min_lng?: number;
  max_lng?: number;
  limit?: number;
  offset?: number;
}

export interface LivePlaceSearchRequest {
  query: string;
  latitude?: number;
  longitude?: number;
  radius_meters?: number;
  included_types?: string[];
  min_rating?: number;
  open_now?: boolean;
}

export interface LivePlaceSearchResponse {
  places: Place[];
  source: 'google_live' | 'cache' | 'local_db';
  total: number;
}

