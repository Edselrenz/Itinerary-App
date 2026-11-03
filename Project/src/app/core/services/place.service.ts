import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, catchError, map, of } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  Municipality,
  PaginatedPlaces,
  Place,
  PlaceSearchParams,
} from '../models/place.models';
import {
  getOfflinePlacesAsPlaceEntities,
  getOfflineNearbyPlaces,
  NearbyPlaceItem,
} from '../data/offline-places.data';

@Injectable({
  providedIn: 'root',
})
export class PlaceService {
  private get baseUrl(): string {
    return `${environment.apiBaseUrl}/places`;
  }
  private get municipalitiesUrl(): string {
    return `${environment.apiBaseUrl}/municipalities`;
  }

  // Curated asset mapping for high-definition photography
  private readonly localImageMap: Record<string, string> = {
    'minalungao national park': 'assets/images/minalungao.png',
    'tagpuan sa lumang gapan': 'assets/images/tagpuan_gapan.png',
    'lumang gapan heritage street': 'assets/images/tagpuan_gapan.png',
    'pantabangan dam and lake viewpoint': 'assets/images/pantabangan_lake.png',
    'pantabangan lake': 'assets/images/pantabangan_lake.png',
    'george point': 'assets/images/george_point.png',
    'highland bali villas resort and spa': 'assets/images/highland_bali.png',
    'farm villaronte': 'assets/images/farm_villaronte.png',
    'casa batik': 'assets/images/casa_batik.png',
    "d' pavilion farm and resort": 'assets/images/pavillion_farm.png',
    'la casa prime cabins': 'assets/images/la_casa_prime.png',
    'lake farm de la marre': 'assets/images/lake_farm_marre.png',
    'rohi paperflower cafe': 'assets/images/rohi_paperflower.png',
    'rohi paperflower': 'assets/images/rohi_paperflower.png',
    'museo de bongabon': 'assets/images/museo_bongabon.png',
    'thornes samgyupsal house': 'assets/images/thornes_samgyupsal.png',
    'thornes samgyupsal': 'assets/images/thornes_samgyupsal.png',
    'nueva ecija': 'assets/images/nueva_ecija_arch.png',
  };

  private readonly categoryDisplayMap: Record<string, string> = {
    cafe: 'Cafe & Dining',
    restaurant: 'Restaurant',
    hotel_accommodation: 'Resort & Stay',
    tourist_attraction: 'Tourist Attraction',
    nature_park: 'Nature & Adventure',
    resort_swimming: 'Resort & Swimming',
    church_religious: 'Heritage & Faith',
    museum_cultural: 'Culture & Museum',
    shopping_market: 'Shopping & Market',
    transport_terminal: 'Transport Terminal',
    hospital_clinic: 'Hospital & Clinic',
    pharmacy: 'Pharmacy',
    bank_atm: 'Bank & ATM',
    fuel_station: 'Fuel Station',
    convenience_store: 'Convenience Store',
    public_facility: 'Public Facility',
  };

  // Canonical curated offline places dataset (DEF-05)
  private readonly curatedOfflinePlaces: Place[] = getOfflinePlacesAsPlaceEntities();

  constructor(private http: HttpClient) {}

  /**
   * Searches and filters places via GET /api/v1/places with zero-cost local database queries.
   */
  public searchPlaces(params?: PlaceSearchParams): Observable<PaginatedPlaces> {
    let httpParams = new HttpParams();

    if (params) {
      if (params.q?.trim()) {
        httpParams = httpParams.set('q', params.q.trim());
      }
      if (params.categories) {
        if (Array.isArray(params.categories)) {
          httpParams = httpParams.set('categories', params.categories.join(','));
        } else {
          httpParams = httpParams.set('categories', params.categories);
        }
      }
      if (params.municipality_id) {
        httpParams = httpParams.set('municipality_id', params.municipality_id);
      }
      if (params.featured !== undefined) {
        httpParams = httpParams.set('featured', String(params.featured));
      }
      if (
        params.min_lat !== undefined &&
        params.max_lat !== undefined &&
        params.min_lng !== undefined &&
        params.max_lng !== undefined
      ) {
        httpParams = httpParams
          .set('min_lat', String(params.min_lat))
          .set('max_lat', String(params.max_lat))
          .set('min_lng', String(params.min_lng))
          .set('max_lng', String(params.max_lng));
      }
      if (params.limit !== undefined) {
        httpParams = httpParams.set('limit', String(params.limit));
      }
      if (params.offset !== undefined) {
        httpParams = httpParams.set('offset', String(params.offset));
      }
    }

    return this.http.get<PaginatedPlaces>(this.baseUrl, { params: httpParams }).pipe(
      catchError(() => of(this.getFallbackPaginatedPlaces(params)))
    );
  }

  private getFallbackPaginatedPlaces(params?: PlaceSearchParams): PaginatedPlaces {
    let items = [...this.curatedOfflinePlaces];

    if (params?.q?.trim()) {
      const q = params.q.trim().toLowerCase();
      items = items.filter(
        (p) =>
          p.name.toLowerCase().includes(q) ||
          (p.municipality_name && p.municipality_name.toLowerCase().includes(q)) ||
          (p.description && p.description.toLowerCase().includes(q))
      );
    }

    if (params?.categories) {
      const cats = Array.isArray(params.categories)
        ? params.categories
        : params.categories.split(',');
      items = items.filter((p) => cats.includes(p.category));
    }

    const limit = params?.limit || 20;
    const offset = params?.offset || 0;

    return {
      total: items.length,
      limit,
      offset,
      items: items.slice(offset, offset + limit),
    };
  }

  /**
   * Retrieves curated featured destinations for the Home tab carousel.
   */
  public getFeaturedPlaces(limit: number = 20): Observable<Place[]> {
    return this.searchPlaces({ featured: true, limit }).pipe(
      map((response) => response.items)
    );
  }

  /**
   * Retrieves full details and provenance for a single place.
   */
  public getPlaceById(id: string): Observable<Place> {
    return this.http.get<Place>(`${this.baseUrl}/${id}`).pipe(
      catchError(() => {
        const found = this.curatedOfflinePlaces.find((p) => p.id === id);
        if (found) {
          return of(found);
        }
        throw new Error('Place not found');
      })
    );
  }

  /**
   * Retrieves the list of Nueva Ecija municipalities and cities.
   */
  public getMunicipalities(query?: string): Observable<Municipality[]> {
    let httpParams = new HttpParams();
    if (query?.trim()) {
      httpParams = httpParams.set('q', query.trim());
    }
    return this.http.get<Municipality[]>(this.municipalitiesUrl, {
      params: httpParams,
    });
  }

  /**
   * Resolves a place's image: prioritizes remote image_url if provided,
   * falls back to locally bundled high-resolution photography, or a default placeholder.
   */
  public getPlaceImage(placeName: string, remoteUrl?: string | null): string {
    if (remoteUrl && remoteUrl.trim().length > 0) {
      return remoteUrl;
    }

    const normalized = (placeName || '').toLowerCase().trim();
    if (!normalized) {
      return 'assets/images/minalungao.png';
    }

    for (const [key, assetPath] of Object.entries(this.localImageMap)) {
      if (normalized.includes(key) || key.includes(normalized)) {
        return assetPath;
      }
    }

    return 'assets/images/minalungao.png';
  }

  /**
   * Formats raw backend category strings into friendly human-readable titles.
   */
  public formatCategoryName(categoryKey: string): string {
    return this.categoryDisplayMap[categoryKey] || categoryKey.replace(/_/g, ' ');
  }

  /**
   * Returns curated nearby restaurants, hospital/pharmacies, and stores
   * matching Figma Flow 2 specifications.
   */
  /**
   * Returns nearby essential services (restaurants, hospitals, stores) for destination (DEF-06).
   */
  public getNearbyPlaces(municipality: string = 'Bongabon'): NearbyPlaceItem[] {
    return getOfflineNearbyPlaces(municipality);
  }
}

export type { NearbyPlaceItem };

