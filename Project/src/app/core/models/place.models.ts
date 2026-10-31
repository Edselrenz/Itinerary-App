export interface Municipality {
  id: string;
  name: string;
  slug: string;
  is_city: boolean;
  center_lat: number;
  center_lng: number;
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

