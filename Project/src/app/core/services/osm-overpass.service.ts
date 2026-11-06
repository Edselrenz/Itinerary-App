import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, catchError, map, of, timeout } from 'rxjs';
import { Place } from '../models/place.models';

export interface OverpassElement {
  type: 'node' | 'way';
  id: number;
  lat?: number;
  lon?: number;
  center?: { lat: number; lon: number };
  tags?: Record<string, string>;
}

export interface OverpassResponse {
  version?: number;
  generator?: string;
  elements: OverpassElement[];
}

@Injectable({
  providedIn: 'root',
})
export class OsmOverpassService {
  private readonly overpassEndpoints = [
    'https://overpass-api.de/api/interpreter',
    'https://maps.mail.ru/osm/tools/overpass/api/interpreter',
  ];

  constructor(private http: HttpClient) {}

  /**
   * Maps raw OpenStreetMap tags into one of our canonical application categories.
   */
  public mapOsmTagsToCategory(tags: Record<string, string>): string {
    const amenity = tags['amenity'] || '';
    const tourism = tags['tourism'] || '';
    const leisure = tags['leisure'] || '';
    const shop = tags['shop'] || '';
    const historic = tags['historic'] || '';

    if (amenity === 'cafe') return 'cafe';
    if (amenity === 'restaurant' || amenity === 'fast_food' || amenity === 'food_court') return 'restaurant';
    if (tourism === 'hotel' || tourism === 'motel' || tourism === 'guest_house' || tourism === 'hostel') return 'hotel_accommodation';
    if (tourism === 'attraction' || tourism === 'viewpoint' || historic === 'monument' || historic === 'memorial') return 'tourist_attraction';
    if (tourism === 'museum' || historic === 'archaeological_site') return 'museum_cultural';
    if (amenity === 'place_of_worship') return 'church_religious';
    if (leisure === 'park' || leisure === 'nature_reserve' || leisure === 'garden') return 'nature_park';
    if (leisure === 'water_park' || leisure === 'swimming_pool' || tourism === 'resort') return 'resort_swimming';
    if (amenity === 'hospital' || amenity === 'clinic' || amenity === 'doctors') return 'hospital_clinic';
    if (amenity === 'pharmacy') return 'pharmacy';
    if (amenity === 'bank' || amenity === 'atm') return 'bank_atm';
    if (amenity === 'fuel') return 'fuel_station';
    if (amenity === 'bus_station' || amenity === 'taxi' || tags['railway'] === 'station') return 'transport_terminal';
    if (shop === 'supermarket' || shop === 'convenience') return 'convenience_store';
    if (shop || amenity === 'marketplace') return 'shopping_market';
    if (amenity === 'townhall' || amenity === 'police' || amenity === 'post_office') return 'public_facility';

    return 'tourist_attraction';
  }

  /**
   * Queries live OpenStreetMap Overpass API for POIs within a bounding box.
   */
  public fetchLiveOsmPlaces(bounds: {
    minLat: number;
    maxLat: number;
    minLng: number;
    maxLng: number;
  }): Observable<Place[]> {
    const { minLat, minLng, maxLat, maxLng } = bounds;
    const bbox = `${minLat},${minLng},${maxLat},${maxLng}`;

    const query = `
      [out:json][timeout:15];
      (
        node["amenity"~"cafe|restaurant|fast_food|bank|atm|pharmacy|hospital|clinic|fuel|place_of_worship|bus_station|townhall"](${bbox});
        node["tourism"~"attraction|hotel|motel|guest_house|museum|viewpoint|resort"](${bbox});
        node["leisure"~"park|resort|water_park|nature_reserve|swimming_pool"](${bbox});
        node["shop"~"supermarket|convenience|mall|department_store"](${bbox});
        way["tourism"~"attraction|hotel|resort|museum"](${bbox});
        way["leisure"~"park|resort|water_park"](${bbox});
      );
      out center body;
    `;

    const url = `${this.overpassEndpoints[0]}?data=${encodeURIComponent(query)}`;

    return this.http.get<OverpassResponse>(url).pipe(
      timeout(12000),
      map((resp) => {
        if (!resp || !resp.elements) {
          return [];
        }

        const places: Place[] = [];
        for (const el of resp.elements) {
          const tags = el.tags || {};
          const name = tags['name'] || tags['name:en'] || tags['alt_name'];
          if (!name) continue;

          const lat = el.lat ?? el.center?.lat;
          const lng = el.lon ?? el.center?.lon;
          if (lat == null || lng == null) continue;

          const category = this.mapOsmTagsToCategory(tags);
          const city = tags['addr:city'] || tags['addr:municipality'] || 'Nueva Ecija';
          const street = tags['addr:street'] || '';
          const address = street ? `${street}, ${city}` : city;
          const osmId = `${el.type}/${el.id}`;

          places.push({
            id: `osm-${el.type}-${el.id}`,
            name: name.trim(),
            category,
            latitude: lat,
            longitude: lng,
            municipality_name: city,
            address_text: address,
            description: tags['description'] || tags['tourism:description'] || '',
            phone: tags['phone'] || tags['contact:phone'] || null,
            website: tags['website'] || tags['contact:website'] || null,
            opening_hours: tags['opening_hours'] || null,
            cost_currency: 'PHP',
            source_name: 'OpenStreetMap Live',
            source_record_id: osmId,
            source_url: `https://www.openstreetmap.org/${osmId}`,
            imported_at: new Date().toISOString(),
            is_featured: false,
            tags: Object.keys(tags).filter((k) => !k.startsWith('addr:')),
            directions_url: `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`,
          });
        }
        return places;
      }),
      catchError((err) => {
        console.warn('[OsmOverpassService] Live Overpass query failed or timed out:', err);
        return of([]);
      })
    );
  }
}

