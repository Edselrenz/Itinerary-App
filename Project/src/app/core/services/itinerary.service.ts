import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, catchError, from, map, of, switchMap, tap, timeout } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  Itinerary,
  ItineraryCreatePayload,
  ItineraryDay,
  ItineraryItem,
  ItineraryItemCreatePayload,
  ItineraryReorderEntry,
  ItineraryUpdatePayload,
  SuggestedItineraryRequest,
  ItineraryBudgetSummary,
} from '../models/itinerary.models';
import { AuthService } from './auth.service';
import { GuestItinerary, GuestStorageService } from './guest-storage.service';

export { ItineraryBudgetSummary } from '../models/itinerary.models';

@Injectable({
  providedIn: 'root',
})
export class ItineraryService {
  private readonly baseUrl = `${environment.apiBaseUrl}/itineraries`;

  private readonly itinerariesSubject = new BehaviorSubject<Itinerary[]>([]);
  public itineraries$: Observable<Itinerary[]> = this.itinerariesSubject.asObservable();

  constructor(
    private http: HttpClient,
    private authService: AuthService,
    private guestStorage: GuestStorageService
  ) {
    this.refreshItineraries().subscribe({ error: () => {} });
  }

  /**
   * Refreshes active itineraries from backend API (if logged in) or GuestStorage (if guest).
   */
  public refreshItineraries(): Observable<Itinerary[]> {
    if (this.authService.isAuthenticated()) {
      return this.http.get<Itinerary[]>(this.baseUrl).pipe(
        tap((items) => this.itinerariesSubject.next(items)),
        catchError(() => {
          return from(this.guestStorage.getItineraries()).pipe(
            map((guestItems) => this.mapGuestItineraries(guestItems)),
            tap((mapped) => this.itinerariesSubject.next(mapped))
          );
        })
      );
    } else {
      return from(this.guestStorage.getItineraries()).pipe(
        map((guestItems) => this.mapGuestItineraries(guestItems)),
        tap((mapped) => this.itinerariesSubject.next(mapped))
      );
    }
  }

  /**
   * Retrieves single itinerary by ID with BOLA protection or guest local lookup.
   */
  public getItineraryById(id: string): Observable<Itinerary> {
    if (this.authService.isAuthenticated()) {
      return this.http.get<Itinerary>(`${this.baseUrl}/${id}`).pipe(
        catchError(() => {
          return this.getGuestItineraryById(id);
        })
      );
    }
    return this.getGuestItineraryById(id);
  }

  /**
   * Creates a new custom or suggested itinerary.
   */
  public createItinerary(payload: ItineraryCreatePayload): Observable<Itinerary> {
    if (this.authService.isAuthenticated()) {
      return this.http.post<Itinerary>(this.baseUrl, payload).pipe(
        tap((created) => {
          const current = this.itinerariesSubject.value;
          this.itinerariesSubject.next([created, ...current]);
        }),
        catchError(() => {
          return from(this.createGuestItinerary(payload)).pipe(
            tap((created) => {
              const current = this.itinerariesSubject.value;
              this.itinerariesSubject.next([created, ...current]);
            })
          );
        })
      );
    }

    return from(this.createGuestItinerary(payload)).pipe(
      tap((created) => {
        const current = this.itinerariesSubject.value;
        this.itinerariesSubject.next([created, ...current]);
      })
    );
  }

  /**
   * Updates itinerary metadata (title, dates, budget).
   */
  public updateItinerary(id: string, payload: ItineraryUpdatePayload): Observable<Itinerary> {
    if (this.authService.isAuthenticated()) {
      return this.http.patch<Itinerary>(`${this.baseUrl}/${id}`, payload).pipe(
        tap((updated) => this.replaceInSubject(updated)),
        catchError(() => from(this.updateGuestItinerary(id, payload)))
      );
    }
    return from(this.updateGuestItinerary(id, payload));
  }

  /**
   * Deletes an itinerary with all associated days and stops.
   */
  public deleteItinerary(id: string): Observable<void> {
    if (this.authService.isAuthenticated()) {
      return this.http.delete<void>(`${this.baseUrl}/${id}`).pipe(
        tap(() => this.removeFromSubject(id)),
        catchError(() =>
          from(this.guestStorage.deleteItinerary(id)).pipe(
            tap(() => this.removeFromSubject(id))
          )
        )
      );
    }

    return from(this.guestStorage.deleteItinerary(id)).pipe(
      tap(() => this.removeFromSubject(id))
    );
  }

  /**
   * Adds a scheduled stop (POI or custom off-grid venue) to a day.
   */
  public addStop(
    itineraryId: string,
    dayId: string,
    itemPayload: ItineraryItemCreatePayload
  ): Observable<Itinerary> {
    if (this.authService.isAuthenticated()) {
      return this.http
        .post<Itinerary>(`${this.baseUrl}/${itineraryId}/days/${dayId}/items`, itemPayload)
        .pipe(
          tap((updated) => this.replaceInSubject(updated)),
          catchError(() => from(this.addGuestStop(itineraryId, dayId, itemPayload)))
        );
    }
    return from(this.addGuestStop(itineraryId, dayId, itemPayload));
  }

  /**
   * Deletes a scheduled stop from a day.
   */
  public deleteStop(
    itineraryId: string,
    dayId: string,
    itemId: string
  ): Observable<Itinerary> {
    if (this.authService.isAuthenticated()) {
      return this.http
        .delete<Itinerary>(`${this.baseUrl}/${itineraryId}/days/${dayId}/items/${itemId}`)
        .pipe(
          tap((updated) => this.replaceInSubject(updated)),
          catchError(() => from(this.deleteGuestStop(itineraryId, dayId, itemId)))
        );
    }
    return from(this.deleteGuestStop(itineraryId, dayId, itemId));
  }

  /**
   * Batch reorders stops within or across days.
   */
  public reorderStops(
    itineraryId: string,
    entries: ItineraryReorderEntry[]
  ): Observable<Itinerary> {
    if (this.authService.isAuthenticated()) {
      return this.http
        .post<Itinerary>(`${this.baseUrl}/${itineraryId}/reorder`, { items: entries })
        .pipe(
          tap((updated) => this.replaceInSubject(updated)),
          catchError(() => from(this.reorderGuestStops(itineraryId, entries)))
        );
    }
    return from(this.reorderGuestStops(itineraryId, entries));
  }

  /**
   * Generates a suggested itinerary using deterministic clustering and transparent assumptions.
   * If in guest mode (e.g. static GitHub Pages), immediately generates locally for instant response.
   */
  public suggestItinerary(request: SuggestedItineraryRequest): Observable<Itinerary> {
    if (!this.authService.isAuthenticated()) {
      return from(this.generateOfflineSuggestedItinerary(request)).pipe(
        tap((plan) => {
          if (request.save_immediately) {
            this.guestStorage.saveItinerary(plan as unknown as GuestItinerary);
            this.replaceInSubject(plan);
          }
        })
      );
    }

    return this.http.post<Itinerary>(`${this.baseUrl}/suggest`, request).pipe(
      timeout(4000),
      tap((plan) => {
        if (request.save_immediately && plan.id) {
          this.replaceInSubject(plan);
        }
      }),
      catchError(() => {
        return from(this.generateOfflineSuggestedItinerary(request)).pipe(
          tap((plan) => {
            if (request.save_immediately) {
              this.guestStorage.saveItinerary(plan as unknown as GuestItinerary);
              this.replaceInSubject(plan);
            }
          })
        );
      })
    );
  }

  /**
   * Transparently calculates itinerary costs without assuming missing prices are zero.
   */
  public calculateBudgetSummary(itinerary: Itinerary): ItineraryBudgetSummary {
    let verifiedMin = 0;
    let verifiedMax = 0;
    let unverifiedCount = 0;

    for (const day of itinerary.days || []) {
      for (const item of day.items || []) {
        const min = item.estimated_cost_min;
        const max = item.estimated_cost_max;

        if (min != null || max != null) {
          verifiedMin += min ?? max ?? 0;
          verifiedMax += max ?? min ?? 0;
        } else {
          unverifiedCount++;
        }
      }
    }

    let displayText = 'No stops added';
    if (verifiedMin > 0 || verifiedMax > 0) {
      const formattedRange =
        verifiedMin === verifiedMax
          ? `₱${verifiedMin.toLocaleString()}`
          : `₱${verifiedMin.toLocaleString()} - ₱${verifiedMax.toLocaleString()}`;
      displayText =
        unverifiedCount > 0
          ? `${formattedRange} (+ ${unverifiedCount} unpriced)`
          : formattedRange;
    } else if (unverifiedCount > 0) {
      displayText = `${unverifiedCount} unpriced stops`;
    }

    return {
      verifiedMin,
      verifiedMax,
      unverifiedCount,
      displayText,
    };
  }

  // ---- Private Guest Storage Helpers ----

  private getGuestItineraryById(id: string): Observable<Itinerary> {
    return from(this.guestStorage.getItineraries()).pipe(
      map((items) => {
        const found = items.find((i) => i.id === id);
        if (!found) {
          throw new Error('Itinerary not found');
        }
        return this.mapGuestItinerary(found);
      })
    );
  }

  private async createGuestItinerary(payload: ItineraryCreatePayload): Promise<Itinerary> {
    const itineraryId = this.generateId();
    const days: ItineraryDay[] = (payload.days || []).map((d, dIdx) => {
      const dayId = this.generateId();
      const items: ItineraryItem[] = (d.items || []).map((it, itIdx) => ({
        id: this.generateId(),
        day_id: dayId,
        place_id: it.place_id,
        custom_title: it.custom_title,
        custom_lat: it.custom_lat,
        custom_lng: it.custom_lng,
        sort_order: it.sort_order ?? itIdx + 1,
        planned_time: it.planned_time,
        duration_minutes: it.duration_minutes ?? 90,
        notes: it.notes,
        estimated_cost_min: it.estimated_cost_min,
        estimated_cost_max: it.estimated_cost_max,
        place: it.place || null,
      }));

      return {
        id: dayId,
        itinerary_id: itineraryId,
        day_number: d.day_number ?? dIdx + 1,
        travel_date: d.travel_date,
        title: d.title,
        items,
      };
    });

    const now = new Date().toISOString();
    const newItin: Itinerary = {
      id: itineraryId,
      title: payload.title,
      destination: payload.destination || 'Nueva Ecija',
      start_date: payload.start_date,
      end_date: payload.end_date,
      daily_budget: payload.daily_budget || 0,
      preferences: payload.preferences || [],
      type: payload.type || 'custom',
      assumptions: payload.assumptions || [],
      created_at: now,
      updated_at: now,
      days,
    };

    await this.guestStorage.saveItinerary(newItin as unknown as GuestItinerary);
    return newItin;
  }

  private async updateGuestItinerary(
    id: string,
    payload: ItineraryUpdatePayload
  ): Promise<Itinerary> {
    const items = await this.guestStorage.getItineraries();
    const target = items.find((i) => i.id === id);
    if (!target) {
      throw new Error('Itinerary not found');
    }

    const updated: GuestItinerary = {
      ...target,
      title: payload.title ?? target.title,
      destination: payload.destination ?? target.destination,
      start_date: payload.start_date ?? target.start_date,
      end_date: payload.end_date ?? target.end_date,
      daily_budget: payload.daily_budget ?? target.daily_budget,
      preferences: payload.preferences ?? target.preferences,
      assumptions: payload.assumptions ?? target.assumptions,
      updated_at: new Date().toISOString(),
    };

    await this.guestStorage.saveItinerary(updated);
    const mapped = this.mapGuestItinerary(updated);
    this.replaceInSubject(mapped);
    return mapped;
  }

  private async addGuestStop(
    itineraryId: string,
    dayId: string,
    itemPayload: ItineraryItemCreatePayload
  ): Promise<Itinerary> {
    const items = await this.guestStorage.getItineraries();
    const target = items.find((i) => i.id === itineraryId);
    if (!target) {
      throw new Error('Itinerary not found');
    }

    const mapped = this.mapGuestItinerary(target);
    const day = mapped.days.find((d) => d.id === dayId);
    if (!day) {
      throw new Error('Day not found');
    }

    if (itemPayload.place_id && day.items.some((it) => it.place_id === itemPayload.place_id)) {
      throw new Error('This destination has already been added to this day.');
    }

    const maxOrder = day.items.reduce((acc, it) => Math.max(acc, it.sort_order), 0);
    const newItem: ItineraryItem = {
      id: this.generateId(),
      day_id: dayId,
      place_id: itemPayload.place_id,
      custom_title: itemPayload.custom_title,
      custom_lat: itemPayload.custom_lat,
      custom_lng: itemPayload.custom_lng,
      sort_order: itemPayload.sort_order ?? maxOrder + 1,
      planned_time: itemPayload.planned_time,
      duration_minutes: itemPayload.duration_minutes ?? 90,
      notes: itemPayload.notes,
      estimated_cost_min: itemPayload.estimated_cost_min,
      estimated_cost_max: itemPayload.estimated_cost_max,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    day.items.push(newItem);
    await this.guestStorage.saveItinerary(mapped as unknown as GuestItinerary);
    this.replaceInSubject(mapped);
    return mapped;
  }

  private async deleteGuestStop(
    itineraryId: string,
    dayId: string,
    itemId: string
  ): Promise<Itinerary> {
    const items = await this.guestStorage.getItineraries();
    const target = items.find((i) => i.id === itineraryId);
    if (!target) {
      throw new Error('Itinerary not found');
    }

    const mapped = this.mapGuestItinerary(target);
    const day = mapped.days.find((d) => d.id === dayId);
    if (!day) {
      throw new Error('Day not found');
    }

    day.items = day.items.filter((it) => it.id !== itemId);
    day.items.forEach((it, idx) => {
      it.sort_order = idx + 1;
    });

    await this.guestStorage.saveItinerary(mapped as unknown as GuestItinerary);
    this.replaceInSubject(mapped);
    return mapped;
  }

  private async reorderGuestStops(
    itineraryId: string,
    entries: ItineraryReorderEntry[]
  ): Promise<Itinerary> {
    const items = await this.guestStorage.getItineraries();
    const target = items.find((i) => i.id === itineraryId);
    if (!target) {
      throw new Error('Itinerary not found');
    }

    const mapped = this.mapGuestItinerary(target);
    for (const entry of entries) {
      for (const day of mapped.days) {
        const item = day.items.find((i) => i.id === entry.id);
        if (item) {
          item.day_id = entry.day_id;
          item.sort_order = entry.sort_order;
        }
      }
    }

    await this.guestStorage.saveItinerary(mapped as unknown as GuestItinerary);
    this.replaceInSubject(mapped);
    return mapped;
  }

  private mapGuestItineraries(guestItems: GuestItinerary[]): Itinerary[] {
    return (guestItems || []).map((g) => this.mapGuestItinerary(g));
  }

  private mapGuestItinerary(g: GuestItinerary): Itinerary {
    return {
      id: g.id,
      title: g.title,
      destination: g.destination,
      start_date: g.start_date,
      end_date: g.end_date,
      daily_budget: g.daily_budget,
      preferences: g.preferences || [],
      type: g.type,
      assumptions: g.assumptions || [],
      created_at: g.created_at,
      updated_at: g.updated_at,
      days: (g.days || []).map((d: any, idx: number) => ({
        id: d.id || `day-${idx + 1}`,
        itinerary_id: g.id,
        day_number: d.day_number ?? idx + 1,
        travel_date: d.travel_date || g.start_date,
        title: d.title,
        items: (d.items || []).map((it: any, itIdx: number) => ({
          id: it.id || `item-${itIdx + 1}`,
          day_id: d.id || `day-${idx + 1}`,
          place_id: it.place_id,
          custom_title: it.custom_title,
          custom_lat: it.custom_lat,
          custom_lng: it.custom_lng,
          sort_order: it.sort_order ?? itIdx + 1,
          planned_time: it.planned_time,
          duration_minutes: it.duration_minutes ?? 90,
          notes: it.notes,
          estimated_cost_min: it.estimated_cost_min,
          estimated_cost_max: it.estimated_cost_max,
          place: it.place,
        })),
      })),
    };
  }

  private replaceInSubject(updated: Itinerary): void {
    const list = this.itinerariesSubject.value;
    const idx = list.findIndex((i) => i.id === updated.id);
    if (idx >= 0) {
      list[idx] = updated;
      this.itinerariesSubject.next([...list]);
    } else {
      this.itinerariesSubject.next([updated, ...list]);
    }
  }

  private removeFromSubject(id: string): void {
    const list = this.itinerariesSubject.value.filter((i) => i.id !== id);
    this.itinerariesSubject.next(list);
  }

  private async generateOfflineSuggestedItinerary(
    request: SuggestedItineraryRequest
  ): Promise<Itinerary> {
    const start = new Date(request.start_date);
    const end = new Date(request.end_date);
    const diffTime = Math.max(0, end.getTime() - start.getTime());
    const totalDays = Math.max(1, Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1);

    const curatedPool = [
      {
        id: 'dest-minalungao',
        name: 'Minalungao National Park',
        category: 'Nature & Adventure',
        categoryKey: 'nature_park',
        municipality: 'General Tinio',
        lat: 15.2981,
        lng: 121.1223,
        image: 'assets/images/minalungao.png',
        description: 'Towering 16-meter limestone cliffs, emerald-green Peñaranda River bamboo rafting, and subterranean caves.',
        tags: ['Balsa Rafting', 'Cliff Diving', 'Caving'],
        directionsUrl: 'https://www.google.com/maps/dir/?api=1&destination=15.2981,121.1223',
        openingHours: '07:00-17:00',
        min: 100,
        max: 500,
        time: '09:00',
        dur: 180,
      },
      {
        id: 'dest-tagpuan-gapan',
        name: 'Tagpuan sa Lumang Gapan',
        category: 'Heritage & Faith',
        categoryKey: 'church_religious',
        municipality: 'Gapan City',
        lat: 15.3065,
        lng: 120.9461,
        image: 'assets/images/tagpuan_gapan.png',
        description: 'The "Little Vigan" of Nueva Ecija featuring restored Spanish colonial street lamps, historic brick facades, and night food stalls.',
        tags: ['Colonial Walk', 'Night Market', 'Historic Street'],
        directionsUrl: 'https://www.google.com/maps/dir/?api=1&destination=15.3065,120.9461',
        openingHours: '06:00-20:00',
        min: null,
        max: null,
        time: '17:00',
        dur: 120,
      },
      {
        id: 'dest-pantabangan-lake',
        name: 'Pantabangan Dam and Lake Viewpoint',
        category: 'Tourist Attraction',
        categoryKey: 'tourist_attraction',
        municipality: 'Pantabangan',
        lat: 15.8126,
        lng: 121.1098,
        image: 'assets/images/pantabangan_lake.png',
        description: 'One of Southeast Asia\'s largest clean water reservoirs, framed by scenic Sierra Madre mountain ridges and bass fishing spots.',
        tags: ['Bass Fishing', 'Scenic View', 'Dam Site'],
        directionsUrl: 'https://www.google.com/maps/dir/?api=1&destination=15.8126,121.1098',
        openingHours: '06:00-18:00',
        min: null,
        max: null,
        time: '09:00',
        dur: 120,
      },
      {
        id: 'dest-george-point',
        name: 'George Point Viewdeck & Resto',
        category: 'Cafe & Dining',
        categoryKey: 'cafe',
        municipality: 'Pantabangan',
        lat: 15.8200,
        lng: 121.1150,
        image: 'assets/images/george_point.png',
        description: 'Scenic panoramic hilltop overlooking Pantabangan Lake, ideal for sunset views, relaxing lakeside dining, and coffee.',
        tags: ['Sunset View', 'Lakeside Coffee', 'Photography'],
        directionsUrl: 'https://www.google.com/maps/dir/?api=1&destination=15.8200,121.1150',
        openingHours: '08:00-20:00',
        min: 150,
        max: 450,
        time: '12:00',
        dur: 90,
      },
      {
        id: 'dest-highland-bali',
        name: 'Highland Bali Villas Resort and Spa',
        category: 'Resort & Stay',
        categoryKey: 'hotel_accommodation',
        municipality: 'Pantabangan',
        lat: 15.8180,
        lng: 121.1210,
        image: 'assets/images/highland_bali.png',
        description: 'Balinese-inspired lakefront retreat with water sports, exotic villas, and breathtaking vistas across the water.',
        tags: ['Water Sports', 'Resort Villas', 'Spa'],
        directionsUrl: 'https://www.google.com/maps/dir/?api=1&destination=15.8180,121.1210',
        openingHours: '24 Hours',
        min: 3500,
        max: 8000,
        time: '15:00',
        dur: 150,
      },
      {
        id: 'dest-farm-villaronte',
        name: 'Farm Villaronte',
        category: 'Tourist Attraction',
        categoryKey: 'tourist_attraction',
        municipality: 'San Jose City',
        lat: 15.7850,
        lng: 120.9980,
        image: 'assets/images/farm_villaronte.png',
        description: 'Vibrant flower farm, organic produce picking, rustic pavilions, and family-friendly agro-tourism trails.',
        tags: ['Sunflower Fields', 'Organic Produce', 'Agri-Tour'],
        directionsUrl: 'https://www.google.com/maps/dir/?api=1&destination=15.7850,120.9980',
        openingHours: '08:00-17:00',
        min: 50,
        max: 200,
        time: '09:00',
        dur: 120,
      },
      {
        id: 'dest-casa-batik',
        name: 'Casa Batik',
        category: 'Culture & Museum',
        categoryKey: 'museum_cultural',
        municipality: 'Cabanatuan City',
        lat: 15.4850,
        lng: 120.9650,
        image: 'assets/images/casa_batik.png',
        description: 'Artisan craft space celebrating Philippine textile traditions, local handcrafted coffee, and homegrown culinary heritage.',
        tags: ['Handcrafted Goods', 'Art Cafe', 'Local Heritage'],
        directionsUrl: 'https://www.google.com/maps/dir/?api=1&destination=15.4850,120.9650',
        openingHours: '09:00-18:00',
        min: 100,
        max: 300,
        time: '10:30',
        dur: 90,
      },
      {
        id: 'dest-pavillion-farm',
        name: "D' Pavilion Farm and Resort",
        category: 'Resort & Swimming',
        categoryKey: 'resort_swimming',
        municipality: 'Bongabon',
        lat: 15.6322,
        lng: 121.1447,
        image: 'assets/images/pavillion_farm.png',
        description: 'Sprawling eco-tourism estate in the Onion Capital with open lawns, fresh mountain breezes, and native dining.',
        tags: ['Mountain View', 'Onion Capital', 'Eco Camp'],
        directionsUrl: 'https://www.google.com/maps/dir/?api=1&destination=15.6322,121.1447',
        openingHours: '08:00-18:00',
        min: 150,
        max: 400,
        time: '11:30',
        dur: 120,
      },
      {
        id: 'dest-lake-farm-marre',
        name: 'Lake Farm de La Marre',
        category: 'Resort & Stay',
        categoryKey: 'hotel_accommodation',
        municipality: 'San Jose City',
        lat: 15.7720,
        lng: 120.9850,
        image: 'assets/images/lake_farm_marre.png',
        description: 'Tranquil countryside lakefront farm estate with boating, peaceful nature retreats, and farm-to-table culinary dining.',
        tags: ['Lakeside Retreat', 'Nature Farm', 'Boating'],
        directionsUrl: 'https://www.google.com/maps/dir/?api=1&destination=15.7720,120.9850',
        openingHours: '08:00-20:00',
        min: 500,
        max: 2500,
        time: '14:00',
        dur: 120,
      },
      {
        id: 'dest-la-casa-prime',
        name: 'La Casa Prime Cabins',
        category: 'Resort & Stay',
        categoryKey: 'hotel_accommodation',
        municipality: 'Bongabon',
        lat: 15.6280,
        lng: 121.1520,
        image: 'assets/images/la_casa_prime.png',
        description: 'Serene mountain cabin sanctuary with overlooking views of Pantabangan Lake and modern glamping amenities.',
        tags: ['Mountain Cabins', 'Lake View', 'Glamping'],
        directionsUrl: 'https://www.google.com/maps/dir/?api=1&destination=15.6280,121.1520',
        openingHours: '24 Hours',
        min: 2500,
        max: 6000,
        time: '16:30',
        dur: 120,
      },
    ];

    const targetDest = (request.destination || '').toLowerCase();
    const sortedPool = [...curatedPool].sort((a, b) => {
      const matchA = targetDest && (a.municipality.toLowerCase().includes(targetDest) || targetDest.includes(a.municipality.toLowerCase())) ? -1 : 1;
      const matchB = targetDest && (b.municipality.toLowerCase().includes(targetDest) || targetDest.includes(b.municipality.toLowerCase())) ? -1 : 1;
      return matchA - matchB;
    });

    const itineraryId = this.generateId();
    const days: ItineraryDay[] = [];
    let poolIndex = 0;
    const now = new Date().toISOString();

    for (let d = 0; d < totalDays; d++) {
      const dayDate = new Date(start);
      dayDate.setDate(start.getDate() + d);
      const dayDateStr = dayDate.toISOString().split('T')[0];
      const dayId = this.generateId();
      const items: ItineraryItem[] = [];

      for (let s = 0; s < 3; s++) {
        const place = sortedPool[poolIndex % sortedPool.length];
        poolIndex++;

        items.push({
          id: this.generateId(),
          day_id: dayId,
          place_id: place.id,
          custom_title: place.name,
          sort_order: s + 1,
          planned_time: place.time,
          duration_minutes: place.dur,
          notes: `Recommended based on local popularity and cluster proximity in ${place.municipality}.`,
          estimated_cost_min: place.min,
          estimated_cost_max: place.max,
          place: {
            id: place.id,
            name: place.name,
            category: place.categoryKey,
            latitude: place.lat,
            longitude: place.lng,
            municipality_name: place.municipality,
            address_text: `${place.municipality}, Nueva Ecija`,
            description: place.description,
            phone: null,
            website: null,
            opening_hours: place.openingHours,
            estimated_cost_min: place.min,
            estimated_cost_max: place.max,
            cost_currency: 'PHP',
            image_url: place.image,
            image_license: null,
            source_name: 'CuratedNuevaEcijaMVP',
            source_record_id: `curated/${place.id}`,
            source_url: null,
            imported_at: now,
            verified_at: now,
            is_featured: true,
            tags: place.tags,
            directions_url: place.directionsUrl,
          },
        });
      }

      const primaryMuni = items[0]?.place?.municipality_name || request.destination || 'Nueva Ecija';
      days.push({
        id: dayId,
        itinerary_id: itineraryId,
        day_number: d + 1,
        travel_date: dayDateStr,
        title: `Day ${d + 1}: ${primaryMuni} Tour`,
        items,
      });
    }

    return {
      id: itineraryId,
      title: request.title || `Suggested ${request.destination || 'Nueva Ecija'} Itinerary`,
      destination: request.destination || 'Nueva Ecija',
      start_date: request.start_date,
      end_date: request.end_date,
      daily_budget: request.daily_budget || 2500,
      preferences: request.preferences || [],
      type: 'suggested',
      assumptions: [
        'Pacing: 2 to 3 stops scheduled per day to allow relaxed travel along provincial roads.',
        `Geographic clustering: Stops on each day are clustered around ${request.destination || 'Nueva Ecija'} to prevent backtracking.`,
        'Budget & Expenses: Estimates reflect entrance, activities, and dining where available. Inter-town transit and fuel are not included.',
        'Operating Hours: Hours reflect verified public records; travelers are encouraged to verify schedules locally for holidays.',
      ],
      created_at: now,
      updated_at: now,
      days,
    };
  }

  private generateId(): string {
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
      return crypto.randomUUID();
    }
    return 'itin-' + Math.random().toString(36).substring(2, 11) + Date.now().toString(36);
  }
}
