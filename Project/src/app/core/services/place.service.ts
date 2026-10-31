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

  private readonly curatedOfflinePlaces: Place[] = [
    {
      id: 'dest-rohi-paperflower',
      name: 'Rohi Paperflower Cafe',
      category: 'cafe',
      latitude: 15.6315,
      longitude: 121.1440,
      municipality_name: 'Bongabon',
      address_text: 'Bongabon, Nueva Ecija',
      description: 'Charming artisanal cafe adorned with vibrant paper flower crafts, signature coffee blends, and baked pastries.',
      phone: null,
      website: null,
      opening_hours: '10:00-21:00',
      estimated_cost_min: 150,
      estimated_cost_max: 350,
      cost_currency: 'PHP',
      image_url: 'assets/images/rohi_paperflower.png',
      image_license: null,
      source_name: 'CuratedNuevaEcijaMVP',
      source_record_id: 'curated/rohi_paperflower',
      source_url: null,
      imported_at: '2026-10-31T00:00:00Z',
      verified_at: '2026-10-31T00:00:00Z',
      is_featured: true,
      tags: ['Cafe', 'Artisan Coffee', 'Crafts'],
      directions_url: 'https://www.google.com/maps/dir/?api=1&destination=15.6315,121.1440',
    },
    {
      id: 'dest-museo-bongabon',
      name: 'Museo de Bongabon',
      category: 'museum_cultural',
      latitude: 15.6300,
      longitude: 121.1430,
      municipality_name: 'Bongabon',
      address_text: 'Bongabon, Nueva Ecija',
      description: 'Community heritage museum chronicling the agricultural identity, historic revolution roots, and onion industry of Bongabon.',
      phone: null,
      website: null,
      opening_hours: '08:00-17:00',
      estimated_cost_min: null,
      estimated_cost_max: null,
      cost_currency: 'PHP',
      image_url: 'assets/images/museo_bongabon.png',
      image_license: null,
      source_name: 'CuratedNuevaEcijaMVP',
      source_record_id: 'curated/museo_bongabon',
      source_url: null,
      imported_at: '2026-10-31T00:00:00Z',
      verified_at: '2026-10-31T00:00:00Z',
      is_featured: true,
      tags: ['Museum', 'Culture', 'History'],
      directions_url: 'https://www.google.com/maps/dir/?api=1&destination=15.6300,121.1430',
    },
    {
      id: 'dest-thornes-samgyupsal',
      name: 'Thornes Samgyupsal House',
      category: 'restaurant',
      latitude: 15.6330,
      longitude: 121.1460,
      municipality_name: 'Bongabon',
      address_text: 'Bongabon, Nueva Ecija',
      description: 'Beloved dining spot serving unlimited Korean samgyupsal BBQ, savory side dishes, and fresh lettuce wraps.',
      phone: null,
      website: null,
      opening_hours: '11:00-22:00',
      estimated_cost_min: 399,
      estimated_cost_max: 599,
      cost_currency: 'PHP',
      image_url: 'assets/images/thornes_samgyupsal.png',
      image_license: null,
      source_name: 'CuratedNuevaEcijaMVP',
      source_record_id: 'curated/thornes_samgyupsal',
      source_url: null,
      imported_at: '2026-10-31T00:00:00Z',
      verified_at: '2026-10-31T00:00:00Z',
      is_featured: true,
      tags: ['Korean BBQ', 'Samgyupsal', 'Dinner'],
      directions_url: 'https://www.google.com/maps/dir/?api=1&destination=15.6330,121.1460',
    },
    {
      id: 'dest-minalungao',
      name: 'Minalungao National Park',
      category: 'nature_park',
      latitude: 15.2981,
      longitude: 121.1223,
      municipality_name: 'General Tinio',
      address_text: 'General Tinio, Nueva Ecija',
      description: 'Towering 16-meter limestone cliffs, emerald-green Peñaranda River bamboo rafting, and subterranean caves.',
      phone: null,
      website: null,
      opening_hours: '07:00-17:00',
      estimated_cost_min: 100,
      estimated_cost_max: 500,
      cost_currency: 'PHP',
      image_url: 'assets/images/minalungao.png',
      image_license: null,
      source_name: 'CuratedNuevaEcijaMVP',
      source_record_id: 'curated/minalungao',
      source_url: null,
      imported_at: '2026-10-30T00:00:00Z',
      verified_at: '2026-10-30T00:00:00Z',
      is_featured: true,
      tags: ['Balsa Rafting', 'Cliff Diving', 'Caving'],
      directions_url: 'https://www.google.com/maps/dir/?api=1&destination=15.2981,121.1223',
    },
    {
      id: 'dest-tagpuan-gapan',
      name: 'Tagpuan sa Lumang Gapan',
      category: 'church_religious',
      latitude: 15.3065,
      longitude: 120.9461,
      municipality_name: 'Gapan City',
      address_text: 'Gapan City, Nueva Ecija',
      description: 'The "Little Vigan" of Nueva Ecija featuring restored Spanish colonial street lamps, historic brick facades, and night food stalls.',
      phone: null,
      website: null,
      opening_hours: '06:00-20:00',
      estimated_cost_min: null,
      estimated_cost_max: null,
      cost_currency: 'PHP',
      image_url: 'assets/images/tagpuan_gapan.png',
      image_license: null,
      source_name: 'CuratedNuevaEcijaMVP',
      source_record_id: 'curated/tagpuan_gapan',
      source_url: null,
      imported_at: '2026-10-30T00:00:00Z',
      verified_at: '2026-10-30T00:00:00Z',
      is_featured: true,
      tags: ['Colonial Walk', 'Night Market', 'Historic Street'],
      directions_url: 'https://www.google.com/maps/dir/?api=1&destination=15.3065,120.9461',
    },
    {
      id: 'dest-pantabangan-lake',
      name: 'Pantabangan Dam and Lake Viewpoint',
      category: 'tourist_attraction',
      latitude: 15.8126,
      longitude: 121.1098,
      municipality_name: 'Pantabangan',
      address_text: 'Pantabangan, Nueva Ecija',
      description: "One of Southeast Asia's largest clean water reservoirs, framed by scenic Sierra Madre mountain ridges and bass fishing spots.",
      phone: null,
      website: null,
      opening_hours: '06:00-18:00',
      estimated_cost_min: null,
      estimated_cost_max: null,
      cost_currency: 'PHP',
      image_url: 'assets/images/pantabangan_lake.png',
      image_license: null,
      source_name: 'CuratedNuevaEcijaMVP',
      source_record_id: 'curated/pantabangan_lake',
      source_url: null,
      imported_at: '2026-10-30T00:00:00Z',
      verified_at: '2026-10-30T00:00:00Z',
      is_featured: true,
      tags: ['Bass Fishing', 'Scenic View', 'Dam Site'],
      directions_url: 'https://www.google.com/maps/dir/?api=1&destination=15.8126,121.1098',
    },
    {
      id: 'dest-george-point',
      name: 'George Point',
      category: 'cafe',
      latitude: 15.82,
      longitude: 121.115,
      municipality_name: 'Pantabangan',
      address_text: 'Pantabangan, Nueva Ecija',
      description: 'Scenic panoramic hilltop overlooking Pantabangan Lake, ideal for sunset views, relaxing lakeside dining, and coffee.',
      phone: null,
      website: null,
      opening_hours: '08:00-20:00',
      estimated_cost_min: 150,
      estimated_cost_max: 450,
      cost_currency: 'PHP',
      image_url: 'assets/images/george_point.png',
      image_license: null,
      source_name: 'CuratedNuevaEcijaMVP',
      source_record_id: 'curated/george_point',
      source_url: null,
      imported_at: '2026-10-30T00:00:00Z',
      verified_at: '2026-10-30T00:00:00Z',
      is_featured: true,
      tags: ['Sunset View', 'Lakeside Coffee', 'Photography'],
      directions_url: 'https://www.google.com/maps/dir/?api=1&destination=15.8200,121.1150',
    },
    {
      id: 'dest-highland-bali',
      name: 'Highland Bali Villas Resort and Spa',
      category: 'hotel_accommodation',
      latitude: 15.818,
      longitude: 121.121,
      municipality_name: 'Pantabangan',
      address_text: 'Pantabangan, Nueva Ecija',
      description: 'Balinese-inspired lakefront retreat with water sports, exotic villas, and breathtaking vistas across the water.',
      phone: null,
      website: null,
      opening_hours: '24 Hours',
      estimated_cost_min: 3500,
      estimated_cost_max: 8000,
      cost_currency: 'PHP',
      image_url: 'assets/images/highland_bali.png',
      image_license: null,
      source_name: 'CuratedNuevaEcijaMVP',
      source_record_id: 'curated/highland_bali',
      source_url: null,
      imported_at: '2026-10-30T00:00:00Z',
      verified_at: '2026-10-30T00:00:00Z',
      is_featured: true,
      tags: ['Water Sports', 'Resort Villas', 'Spa'],
      directions_url: 'https://www.google.com/maps/dir/?api=1&destination=15.8180,121.1210',
    },
    {
      id: 'dest-farm-villaronte',
      name: 'Farm Villaronte',
      category: 'tourist_attraction',
      latitude: 15.785,
      longitude: 120.998,
      municipality_name: 'San Jose City',
      address_text: 'San Jose City, Nueva Ecija',
      description: 'Vibrant flower farm, organic produce picking, rustic pavilions, and family-friendly agro-tourism trails.',
      phone: null,
      website: null,
      opening_hours: '08:00-17:00',
      estimated_cost_min: 50,
      estimated_cost_max: 200,
      cost_currency: 'PHP',
      image_url: 'assets/images/farm_villaronte.png',
      image_license: null,
      source_name: 'CuratedNuevaEcijaMVP',
      source_record_id: 'curated/farm_villaronte',
      source_url: null,
      imported_at: '2026-10-30T00:00:00Z',
      verified_at: '2026-10-30T00:00:00Z',
      is_featured: true,
      tags: ['Sunflower Fields', 'Organic Produce', 'Agri-Tour'],
      directions_url: 'https://www.google.com/maps/dir/?api=1&destination=15.7850,120.9980',
    },
    {
      id: 'dest-casa-batik',
      name: 'Casa Batik',
      category: 'museum_cultural',
      latitude: 15.485,
      longitude: 120.968,
      municipality_name: 'Cabanatuan City',
      address_text: 'Cabanatuan City, Nueva Ecija',
      description: 'Artisan craft space celebrating Philippine textile traditions, local handcrafted coffee, and homegrown culinary heritage.',
      phone: null,
      website: null,
      opening_hours: '09:00-19:00',
      estimated_cost_min: 100,
      estimated_cost_max: 300,
      cost_currency: 'PHP',
      image_url: 'assets/images/casa_batik.png',
      image_license: null,
      source_name: 'CuratedNuevaEcijaMVP',
      source_record_id: 'curated/casa_batik',
      source_url: null,
      imported_at: '2026-10-30T00:00:00Z',
      verified_at: '2026-10-30T00:00:00Z',
      is_featured: true,
      tags: ['Handcrafted Goods', 'Art Cafe', 'Local Heritage'],
      directions_url: 'https://www.google.com/maps/dir/?api=1&destination=15.4850,120.9680',
    },
    {
      id: 'dest-pavillion-farm',
      name: "D' Pavilion Farm and Resort",
      category: 'resort_swimming',
      latitude: 15.584,
      longitude: 120.892,
      municipality_name: 'Muñoz Science City',
      address_text: 'Muñoz Science City, Nueva Ecija',
      description: 'Relaxing agricultural nature resort with refreshing swimming pools, family pavilions, and quiet orchard walks.',
      phone: null,
      website: null,
      opening_hours: '08:00-21:00',
      estimated_cost_min: 200,
      estimated_cost_max: 600,
      cost_currency: 'PHP',
      image_url: 'assets/images/pavillion_farm.png',
      image_license: null,
      source_name: 'CuratedNuevaEcijaMVP',
      source_record_id: 'curated/pavillion_farm',
      source_url: null,
      imported_at: '2026-10-30T00:00:00Z',
      verified_at: '2026-10-30T00:00:00Z',
      is_featured: true,
      tags: ['Swimming Pool', 'Nature Farm', 'Cabanas'],
      directions_url: 'https://www.google.com/maps/dir/?api=1&destination=15.5840,120.8920',
    },
    {
      id: 'dest-lake-farm-marre',
      name: 'Lake Farm de La Marre',
      category: 'hotel_accommodation',
      latitude: 15.772,
      longitude: 120.985,
      municipality_name: 'San Jose City',
      address_text: 'San Jose City, Nueva Ecija',
      description: 'Tranquil countryside lakefront farm estate with boating, peaceful nature retreats, and farm-to-table culinary dining.',
      phone: null,
      website: null,
      opening_hours: '08:00-20:00',
      estimated_cost_min: 500,
      estimated_cost_max: 2500,
      cost_currency: 'PHP',
      image_url: 'assets/images/lake_farm_marre.png',
      image_license: null,
      source_name: 'CuratedNuevaEcijaMVP',
      source_record_id: 'curated/lake_farm_marre',
      source_url: null,
      imported_at: '2026-10-30T00:00:00Z',
      verified_at: '2026-10-30T00:00:00Z',
      is_featured: true,
      tags: ['Lakeside Retreat', 'Nature Farm', 'Boating'],
      directions_url: 'https://www.google.com/maps/dir/?api=1&destination=15.7720,120.9850',
    },
    {
      id: 'dest-la-casa-prime',
      name: 'La Casa Prime Cabins',
      category: 'hotel_accommodation',
      latitude: 15.628,
      longitude: 121.152,
      municipality_name: 'Bongabon',
      address_text: 'Bongabon, Nueva Ecija',
      description: 'Serene mountain cabin sanctuary with overlooking views of Pantabangan Lake and modern glamping amenities.',
      phone: null,
      website: null,
      opening_hours: '24 Hours',
      estimated_cost_min: 2500,
      estimated_cost_max: 6000,
      cost_currency: 'PHP',
      image_url: 'assets/images/la_casa_prime.png',
      image_license: null,
      source_name: 'CuratedNuevaEcijaMVP',
      source_record_id: 'curated/la_casa_prime',
      source_url: null,
      imported_at: '2026-10-30T00:00:00Z',
      verified_at: '2026-10-30T00:00:00Z',
      is_featured: true,
      tags: ['Mountain Cabins', 'Lake View', 'Glamping'],
      directions_url: 'https://www.google.com/maps/dir/?api=1&destination=15.6280,121.1520',
    },
  ];

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
  public getNearbyPlaces(municipality: string = 'Bongabon'): NearbyPlaceItem[] {
    const norm = (municipality || '').toLowerCase();
    
    // Default curated Bongabon places directly from Figma
    return [
      // 1. Restaurants
      { id: 'nb-r-1', name: 'Boss Samgyupsal', category: 'restaurant', openingHours: 'Daily, 10:00 AM to 10:00 PM', municipality: 'Bongabon' },
      { id: 'nb-r-2', name: 'Lomi-Raiyah Foodhouse', category: 'restaurant', openingHours: 'Mon-Sat, 5:00 AM to 8:00 PM', municipality: 'Bongabon' },
      { id: 'nb-r-3', name: 'The Hangover by Y3-J', category: 'restaurant', openingHours: 'Daily, 6:00 AM to 11:30 PM', municipality: 'Bongabon' },
      { id: 'nb-r-4', name: 'Banchan Gogi Unlimited Korean Grill', category: 'restaurant', openingHours: 'Daily, 12:30 PM to 11:00 PM', municipality: 'Bongabon' },
      { id: 'nb-r-5', name: 'Tara G!', category: 'restaurant', openingHours: 'Daily, 24 hrs', municipality: 'Bongabon' },
      { id: 'nb-r-6', name: "Hera's Diner By Rac's Catering", category: 'restaurant', openingHours: 'Tue-Sun, 6:00 AM to 8:00 PM', municipality: 'Bongabon' },

      // 2. Hospital & Pharmacies
      { id: 'nb-h-1', name: 'Bongabon District Hospital', category: 'hospital', openingHours: 'Mon-Sat, 7:00 AM to 5:00 PM', municipality: 'Bongabon' },
      { id: 'nb-h-2', name: 'PharmVille Pharmacy and Medical Supplies', category: 'hospital', openingHours: 'Daily, 7:00 AM to 10:00 PM', municipality: 'Bongabon' },
      { id: 'nb-h-3', name: 'Deb Pharmacy', category: 'hospital', openingHours: 'Mon-Sat, 7:30 AM to 7:00 PM. Sun and Holidays, 9:00 AM to 5:00 PM', municipality: 'Bongabon' },
      { id: 'nb-h-4', name: 'Resma Medical Clinic', category: 'hospital', openingHours: 'Daily, 6:30 AM to 3:30 PM', municipality: 'Bongabon' },

      // 3. Stores
      { id: 'nb-s-1', name: 'J&B- Convenience Store', category: 'store', openingHours: 'Daily, 24 hrs', municipality: 'Bongabon' },
      { id: 'nb-s-2', name: 'Rc Sylvia Store', category: 'store', openingHours: 'Daily, 6:00 AM to 8:00 PM', municipality: 'Bongabon' },
      { id: 'nb-s-3', name: 'Maila Store', category: 'store', openingHours: 'Daily, 6:00 AM to 8:00 PM', municipality: 'Bongabon' },
      { id: 'nb-s-4', name: 'Alfamart Curva Bongabon', category: 'store', openingHours: 'Mon-Fri, 6:00 AM to 11:00 PM. Sat-Sun, 24 hrs', municipality: 'Bongabon' },
      { id: 'nb-s-5', name: 'M2 Mc. Oil', category: 'store', openingHours: 'Daily, 5:30 AM to 8:00 PM', municipality: 'Bongabon' },
      { id: 'nb-s-6', name: "Franks N' Burgers", category: 'store', openingHours: 'Daily, 24 hrs', municipality: 'Bongabon' },
    ];
  }
}

export interface NearbyPlaceItem {
  id: string;
  name: string;
  category: 'restaurant' | 'hospital' | 'store';
  openingHours: string;
  municipality: string;
}

