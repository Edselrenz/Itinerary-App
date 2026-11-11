import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import type { Observable} from 'rxjs';
import { BehaviorSubject, catchError, from, map, of, tap, throwError, timeout } from 'rxjs';

import { environment } from '../../../environments/environment';
import type {
  OfflineCuratedPlace} from '../data/offline-places.data';
import {
  getOfflineCuratedPoolForItinerary,
  getOfflineDayClusterPresets
} from '../data/offline-places.data';
import type {
  Itinerary,
  ItineraryCreatePayload,
  ItineraryDay,
  ItineraryItem,
  ItineraryItemCreatePayload,
  ItineraryReorderEntry,
  ItineraryUpdatePayload,
  RouteLegMetadata,
  SuggestedItineraryRequest,
  ItineraryBudgetSummary,
} from '../models/itinerary.models';
import { addDaysLocal, diffDaysLocal, parseLocalIsoDate, toLocalIsoDate } from '../utils/date.utils';
import { encodePolyline, haversineDistanceMeters } from '../utils/polyline.util';

import { AuthService } from './auth.service';
import { ConnectivityService } from './connectivity.service';
import type { GuestItinerary} from './guest-storage.service';
import { GuestStorageService } from './guest-storage.service';
import { PlaceService } from './place.service';

export { ItineraryBudgetSummary } from '../models/itinerary.models';

@Injectable({
  providedIn: 'root',
})
export class ItineraryService {
  private connectivityService = inject(ConnectivityService, { optional: true });
  private placeService = inject(PlaceService, { optional: true });

  private get baseUrl(): string {
    const apiBase = this.connectivityService?.activeApiBaseUrl || environment.apiBaseUrl;
    return `${apiBase}/itineraries`;
  }

  private readonly itinerariesSubject = new BehaviorSubject<Itinerary[]>([]);
  public itineraries$: Observable<Itinerary[]> = this.itinerariesSubject.asObservable();

  private readonly activeDraftSubject = new BehaviorSubject<Itinerary | null>(this.loadDraftFromSession());
  public activeDraftItinerary$: Observable<Itinerary | null> = this.activeDraftSubject.asObservable();

  private loadDraftFromSession(): Itinerary | null {
    if (typeof window === 'undefined' || !window.sessionStorage) return null;
    try {
      const stored = window.sessionStorage.getItem('ne_active_draft_itinerary');
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  }

  /**
   * Caches an in-memory or unsaved suggested wizard draft itinerary in service memory and sessionStorage (GAP-03).
   */
  public setActiveDraftItinerary(itin: Itinerary | null): void {
    this.activeDraftSubject.next(itin);
    if (typeof window !== 'undefined' && window.sessionStorage) {
      try {
        if (itin) {
          window.sessionStorage.setItem('ne_active_draft_itinerary', JSON.stringify(itin));
        } else {
          window.sessionStorage.removeItem('ne_active_draft_itinerary');
        }
      } catch (e) {
        console.warn('Failed to store draft in sessionStorage:', e);
      }
    }
  }

  /**
   * Synchronously retrieves the active draft itinerary.
   */
  public getActiveDraftItinerary(): Itinerary | null {
    return this.activeDraftSubject.value;
  }

  /**
   * Retrieves an itinerary by ID or resolves the active unsaved draft if id is 'draft' or matches (GAP-03).
   */
  public getItineraryOrDraftById(id: string): Observable<Itinerary | null> {
    if (!id || id === 'draft' || id === 'preview') {
      return of(this.getActiveDraftItinerary());
    }
    const draft = this.getActiveDraftItinerary();
    if (draft && draft.id === id) {
      return of(draft);
    }
    return this.getItineraryById(id).pipe(
      catchError(() => of(draft))
    );
  }

  private isNetworkError(err: any): boolean {
    const status = err?.status;
    return (
      status === 0 ||
      status === 502 ||
      status === 503 ||
      status === 504 ||
      err?.name === 'TimeoutError'
    );
  }

  private http = inject(HttpClient);
  private authService = inject(AuthService);
  private guestStorage = inject(GuestStorageService);

  constructor() {
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
   * Synchronously checks in-memory cache for an itinerary by ID.
   */
  public getCachedItineraryById(id: string): Itinerary | null {
    const list = this.itinerariesSubject.value;
    return list.find((i) => i.id === id) || null;
  }

  /**
   * Retrieves single itinerary by ID with BOLA protection, memory fallback, or guest local lookup.
   */
  public getItineraryById(id: string): Observable<Itinerary> {
    const cached = this.getCachedItineraryById(id);
    if (this.authService.isAuthenticated()) {
      return this.http.get<Itinerary>(`${this.baseUrl}/${id}`).pipe(
        tap((updated) => this.replaceInSubject(updated)),
        catchError(() => {
          if (cached) {
            return of(cached);
          }
          return this.getGuestItineraryById(id);
        })
      );
    }
    if (cached) {
      return of(cached);
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
        catchError((err) => {
          if (this.isNetworkError(err)) {
            return from(this.createGuestItinerary(payload)).pipe(
              tap((created) => {
                const current = this.itinerariesSubject.value;
                this.itinerariesSubject.next([created, ...current]);
              })
            );
          }
          return throwError(() => err);
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
        catchError((err) => {
          if (this.isNetworkError(err)) {
            return from(this.updateGuestItinerary(id, payload));
          }
          return throwError(() => err);
        })
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
        catchError((err) => {
          if (this.isNetworkError(err)) {
            return from(this.guestStorage.deleteItinerary(id)).pipe(
              tap(() => this.removeFromSubject(id))
            );
          }
          return throwError(() => err);
        })
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
          catchError((err) => {
            if (this.isNetworkError(err)) {
              return from(this.addGuestStop(itineraryId, dayId, itemPayload));
            }
            return throwError(() => err);
          })
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
          catchError((err) => {
            if (this.isNetworkError(err)) {
              return from(this.deleteGuestStop(itineraryId, dayId, itemId));
            }
            return throwError(() => err);
          })
        );
    }
    return from(this.deleteGuestStop(itineraryId, dayId, itemId));
  }

  /**
   * Partially updates an existing stop in an itinerary day (UI-06).
   */
  public updateStop(
    itineraryId: string,
    dayId: string,
    itemId: string,
    patchPayload: Partial<ItineraryItemCreatePayload>
  ): Observable<Itinerary> {
    if (this.authService.isAuthenticated()) {
      return this.http
        .patch<Itinerary>(`${this.baseUrl}/${itineraryId}/days/${dayId}/items/${itemId}`, patchPayload)
        .pipe(
          tap((updated) => this.replaceInSubject(updated)),
          catchError((err) => {
            if (this.isNetworkError(err)) {
              return from(this.updateGuestStop(itineraryId, dayId, itemId, patchPayload));
            }
            return throwError(() => err);
          })
        );
    }
    return from(this.updateGuestStop(itineraryId, dayId, itemId, patchPayload));
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
          catchError((err) => {
            if (this.isNetworkError(err)) {
              return from(this.reorderGuestStops(itineraryId, entries));
            }
            return throwError(() => err);
          })
        );
    }
    return from(this.reorderGuestStops(itineraryId, entries));
  }

  /**
   * Generates a suggested itinerary using deterministic clustering and transparent assumptions.
   * If in guest mode or host offline, immediately generates locally for instant response (S-BUG-04).
   */
  public suggestItinerary(request: SuggestedItineraryRequest): Observable<Itinerary> {
    const isOffline =
      (typeof navigator !== 'undefined' && !navigator.onLine) ||
      Boolean(this.connectivityService?.isHostOfflineSnapshot);

    if (isOffline) {
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
      timeout(10000),
      tap((plan) => {
        if (request.save_immediately && plan.id) {
          if (this.authService.isAuthenticated()) {
            this.replaceInSubject(plan);
          } else {
            this.guestStorage.saveItinerary(plan as unknown as GuestItinerary);
            this.replaceInSubject(plan);
          }
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
      const items: ItineraryItem[] = (d.items || []).map((it, itIdx) => {
        let itemPlace = it.place;
        if (!itemPlace && it.place_id && this.placeService) {
          itemPlace = this.placeService.findPlaceById(it.place_id) || null;
        }
        const title = it.custom_title || (it as any).name || itemPlace?.name || 'Destination Stop';
        const lat = it.custom_lat ?? itemPlace?.latitude ?? null;
        const lng = it.custom_lng ?? itemPlace?.longitude ?? null;

        return {
          id: this.generateId(),
          day_id: dayId,
          place_id: it.place_id,
          custom_title: title,
          custom_lat: lat,
          custom_lng: lng,
          sort_order: it.sort_order ?? itIdx + 1,
          planned_time: it.planned_time,
          duration_minutes: it.duration_minutes ?? 90,
          notes: it.notes,
          estimated_cost_min: it.estimated_cost_min,
          estimated_cost_max: it.estimated_cost_max,
          place: itemPlace || null,
        };
      });

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

    let updatedDays = target.days;
    if (payload.days) {
      updatedDays = payload.days.map((d, dIdx) => {
        const dayId = this.generateId();
        const dayItems: ItineraryItem[] = (d.items || []).map((it, itIdx) => ({
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
          itinerary_id: id,
          day_number: d.day_number ?? dIdx + 1,
          travel_date: d.travel_date,
          title: d.title,
          items: dayItems,
        };
      });
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
      days: updatedDays,
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

  private async updateGuestStop(
    itineraryId: string,
    dayId: string,
    itemId: string,
    patchPayload: Partial<ItineraryItemCreatePayload>
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

    const item = day.items.find((it) => it.id === itemId);
    if (!item) {
      throw new Error('Item not found');
    }

    if (patchPayload.custom_title !== undefined) item.custom_title = patchPayload.custom_title;
    if (patchPayload.custom_lat !== undefined) item.custom_lat = patchPayload.custom_lat;
    if (patchPayload.custom_lng !== undefined) item.custom_lng = patchPayload.custom_lng;
    if (patchPayload.planned_time !== undefined) item.planned_time = patchPayload.planned_time;
    if (patchPayload.duration_minutes !== undefined) item.duration_minutes = patchPayload.duration_minutes;
    if (patchPayload.notes !== undefined) item.notes = patchPayload.notes;
    if (patchPayload.estimated_cost_min !== undefined) item.estimated_cost_min = patchPayload.estimated_cost_min;
    if (patchPayload.estimated_cost_max !== undefined) item.estimated_cost_max = patchPayload.estimated_cost_max;
    if (patchPayload.sort_order !== undefined) item.sort_order = patchPayload.sort_order;
    item.updated_at = new Date().toISOString();

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
    const allItems: ItineraryItem[] = [];
    for (const day of mapped.days) {
      allItems.push(...day.items);
      day.items = [];
    }
    for (const entry of entries) {
      const it = allItems.find((i) => i.id === entry.id);
      if (it) {
        it.day_id = entry.day_id;
        it.sort_order = entry.sort_order;
        const targetDay = mapped.days.find((d) => d.id === entry.day_id);
        if (targetDay) {
          targetDay.items.push(it);
        }
      }
    }
    for (const it of allItems) {
      if (!entries.some((e) => e.id === it.id)) {
        const d = mapped.days.find((day) => day.id === it.day_id);
        if (d && !d.items.includes(it)) {
          d.items.push(it);
        }
      }
    }
    for (const day of mapped.days) {
      day.items.sort((a, b) => a.sort_order - b.sort_order);
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
        items: (d.items || []).map((it: any, itIdx: number) => {
          let itemPlace = it.place;
          if (!itemPlace && it.place_id && this.placeService) {
            itemPlace = this.placeService.findPlaceById(it.place_id) || null;
          }
          const title = it.custom_title || it.name || itemPlace?.name || 'Destination Stop';
          const lat = it.custom_lat ?? itemPlace?.latitude ?? null;
          const lng = it.custom_lng ?? itemPlace?.longitude ?? null;

          return {
            id: it.id || `item-${itIdx + 1}`,
            day_id: d.id || `day-${idx + 1}`,
            place_id: it.place_id,
            custom_title: title,
            custom_lat: lat,
            custom_lng: lng,
            sort_order: it.sort_order ?? itIdx + 1,
            planned_time: it.planned_time,
            duration_minutes: it.duration_minutes ?? 90,
            notes: it.notes,
            estimated_cost_min: it.estimated_cost_min,
            estimated_cost_max: it.estimated_cost_max,
            place: itemPlace || null,
          };
        }),
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

  public readonly PREFERENCE_CATEGORY_MAP: Record<string, string[]> = {
    nature: ['nature_park', 'tourist_attraction', 'nature'],
    food: ['restaurant', 'cafe', 'food'],
    culture: ['museum_cultural', 'church_religious', 'historical', 'culture'],
    shopping: ['shopping_market', 'convenience_store', 'shopping'],
    resort: ['resort_swimming', 'hotel_accommodation', 'resort'],
  };

  public normalizeVenueName(name: string): string {
    return (name || '')
      .toLowerCase()
      .replace(/\b(viewdeck|viewpoint|and|&|resto|restaurant|cafe|resort|spa|hotel|villas|park|shrine|memorial)\b/g, '')
      .replace(/[^a-z0-9]/g, '');
  }

  public isMountainPeak(name: string): boolean {
    return /^(\bmt\.?\b|\bmount\b)/i.test((name || '').trim());
  }

  public isDiningVenue(categoryKey: string): boolean {
    const key = (categoryKey || '').toLowerCase();
    return key === 'restaurant' || key === 'cafe' || key.includes('food');
  }

  public formatMinutesTo12Hr(minutes: number): string {
    const wrapped = ((minutes % 1440) + 1440) % 1440;
    let hours = Math.floor(wrapped / 60);
    const mins = wrapped % 60;
    const period = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12;
    if (hours === 0) hours = 12;
    const padH = hours < 10 ? `0${hours}` : `${hours}`;
    const padM = mins < 10 ? `0${mins}` : `${mins}`;
    return `${padH}:${padM} ${period}`;
  }

  private parseTimeToMinutes(timeStr: string | null | undefined): number {
    if (!timeStr) return 9 * 60;
    const lower = timeStr.toLowerCase().trim();
    if (
      lower.includes('night') ||
      lower.includes('stay') ||
      lower.includes('check-in')
    ) {
      return 23 * 60 + 59;
    }

    const startPart = timeStr.split('-')[0].trim();
    const match = startPart.match(/^(\d{1,2}):(\d{2})\s*(AM|PM)?$/i);
    if (match) {
      let hours = parseInt(match[1], 10);
      const minutes = parseInt(match[2], 10);
      const meridian = match[3]?.toUpperCase();

      if (meridian === 'PM' && hours < 12) {
        hours += 12;
      } else if (meridian === 'AM' && hours === 12) {
        hours = 0;
      }
      return hours * 60 + minutes;
    }
    return 9 * 60;
  }

  private isOvernightItem(item: ItineraryItem): boolean {
    const cat = (item.place?.category || '').toLowerCase();
    const dur = item.duration_minutes || 0;
    const time = (item.planned_time || '').toLowerCase();
    const tags = (item.place?.tags || []).map((t) => t.toLowerCase());

    if (cat === 'hotel_accommodation') return true;
    if (dur >= 720) return true;
    if (time.includes('night') || time.includes('stay')) return true;
    if (
      tags.some(
        (t) =>
          t.includes('cabin') ||
          t.includes('glamping') ||
          t.includes('resort villas') ||
          t.includes('hotel')
      )
    ) {
      return true;
    }
    return false;
  }

  private isAccommodationPlace(place: OfflineCuratedPlace): boolean {
    const cat = (place.categoryKey || '').toLowerCase();
    const tags = (place.tags || []).map((t) => t.toLowerCase());
    if (cat === 'hotel_accommodation') return true;
    if (
      tags.some(
        (t) =>
          t.includes('cabin') ||
          t.includes('glamping') ||
          t.includes('resort villas') ||
          t.includes('hotel') ||
          t.includes('overnight')
      )
    ) {
      return true;
    }
    return false;
  }

  private async generateOfflineSuggestedItinerary(
    request: SuggestedItineraryRequest
  ): Promise<Itinerary> {
    const totalDays = Math.max(1, diffDaysLocal(request.start_date, request.end_date));
    const start = parseLocalIsoDate(request.start_date);
    const isSingleDay = totalDays === 1;
    const pacing = request.pacing || 'moderate';
    const targetStopsPerDay = pacing === 'relaxed' ? 2 : pacing === 'fast' ? 4 : 3;

    // Canonical curated offline places dataset (DEF-05)
    const curatedPool: OfflineCuratedPlace[] = getOfflineCuratedPoolForItinerary();

    // Augment with loaded OSM places if PlaceService is available
    if (this.placeService) {
      const loaded = this.placeService.getLoadedPlaces();
      for (const lp of loaded) {
        if (!curatedPool.some((cp) => cp.id === lp.id)) {
          curatedPool.push({
            id: lp.id,
            name: lp.name,
            category: this.placeService.formatCategoryName(lp.category),
            categoryKey: lp.category,
            municipality: lp.municipality_name || 'Nueva Ecija',
            lat: lp.latitude,
            lng: lp.longitude,
            image: lp.image_url || 'assets/images/placeholder.png',
            description: lp.description || `${lp.name} in ${lp.municipality_name || 'Nueva Ecija'}`,
            tags: lp.tags || [],
            directionsUrl: lp.directions_url || `https://www.google.com/maps/dir/?api=1&destination=${lp.latitude},${lp.longitude}`,
            openingHours: lp.opening_hours || null,
            min: lp.estimated_cost_min ?? null,
            max: lp.estimated_cost_max ?? null,
            time: '10:00 AM - 12:00 PM',
            dur: 120,
          });
        }
      }
    }

    const targetDest = (request.destination || '').toLowerCase().trim();
    const prefs = (request.preferences || []).map((p) => p.toLowerCase());
    const dailyBudget = request.daily_budget && request.daily_budget > 0 ? request.daily_budget : null;

    // Anchor place lookup (S-BUG-01)
    let anchorPlace: OfflineCuratedPlace | null = null;
    if (request.anchor_place_id) {
      anchorPlace = curatedPool.find((p) => p.id === request.anchor_place_id) || null;
      if (!anchorPlace && this.placeService) {
        const p = this.placeService.findPlaceById(request.anchor_place_id);
        if (p) {
          anchorPlace = {
            id: p.id,
            name: p.name,
            category: this.placeService.formatCategoryName(p.category),
            categoryKey: p.category,
            municipality: p.municipality_name || 'Nueva Ecija',
            lat: p.latitude,
            lng: p.longitude,
            image: p.image_url || 'assets/images/placeholder.png',
            description: p.description || '',
            tags: p.tags || [],
            directionsUrl: p.directions_url || `https://www.google.com/maps/dir/?api=1&destination=${p.latitude},${p.longitude}`,
            openingHours: p.opening_hours || null,
            min: p.estimated_cost_min ?? null,
            max: p.estimated_cost_max ?? null,
            time: '09:00 AM - 11:00 AM',
            dur: 120,
          };
          curatedPool.unshift(anchorPlace);
        }
      }
    }

    // Filter & score pool based on destination municipality and category preferences (CR-009, S-BUG-03)
    let matchedPool = [...curatedPool];
    const isTargetingSpecificMuni = Boolean(
      targetDest &&
      !targetDest.includes('nueva ecija') &&
      !targetDest.includes('province')
    );

    if (isTargetingSpecificMuni) {
      const muniMatches = curatedPool.filter((p) =>
        p.municipality.toLowerCase().includes(targetDest)
      );
      if (muniMatches.length > 0) {
        matchedPool = muniMatches;
      }
    }

    // Build canonical allowed category set from user preferences (PREF-02)
    const allowedCategories = new Set<string>();
    for (const pr of prefs) {
      const mapped = this.PREFERENCE_CATEGORY_MAP[pr] || [pr];
      mapped.forEach((c) => allowedCategories.add(c.toLowerCase()));
    }

    // Sort by preferences and budget with strong preference weighting (PREF-02, PREF-03)
    matchedPool.sort((a, b) => {
      let aScore = 0;
      let bScore = 0;

      if (isTargetingSpecificMuni) {
        if (a.municipality.toLowerCase().includes(targetDest)) aScore += 10;
        if (b.municipality.toLowerCase().includes(targetDest)) bScore += 10;
      }

      if (prefs.length > 0) {
        if (allowedCategories.has(a.categoryKey.toLowerCase())) aScore += 25;
        if (allowedCategories.has(b.categoryKey.toLowerCase())) bScore += 25;

        for (const pr of prefs) {
          if (a.tags.some((t) => t.toLowerCase().includes(pr))) aScore += 5;
          if (b.tags.some((t) => t.toLowerCase().includes(pr))) bScore += 5;
        }
      }

      if (dailyBudget) {
        if ((a.min ?? 0) <= dailyBudget) aScore += 2;
        if ((b.min ?? 0) <= dailyBudget) bScore += 2;
      }

      return bScore - aScore;
    });

    const isExplicitBongabonPreset =
      !anchorPlace &&
      targetDest.includes('bongabon') &&
      prefs.length <= 2;

    // Clustered day-by-day presets from canonical dataset (DEF-03, DEF-05)
    const dayClusterPresets = getOfflineDayClusterPresets(curatedPool);

    const itineraryId = this.generateId();
    const days: ItineraryDay[] = [];
    const now = new Date().toISOString();

    // Cross-day deduplication tracking (PREF-06: ID, fuzzy venue name, and coordinate proximity)
    const usedPlaceIds = new Set<string>();
    const usedVenueNormNames = new Set<string>();
    const usedCoords: { lat: number; lng: number }[] = [];

    const isPlaceDuplicate = (place: OfflineCuratedPlace): boolean => {
      if (usedPlaceIds.has(place.id)) return true;
      const norm = this.normalizeVenueName(place.name);
      if (norm.length >= 4 && usedVenueNormNames.has(norm)) return true;
      if (
        usedCoords.some(
          (c) =>
            haversineDistanceMeters(place.lat, place.lng, c.lat, c.lng) < 200
        )
      ) {
        return true;
      }
      return false;
    };

    const markPlaceUsed = (place: OfflineCuratedPlace): void => {
      usedPlaceIds.add(place.id);
      const norm = this.normalizeVenueName(place.name);
      if (norm.length >= 4) usedVenueNormNames.add(norm);
      usedCoords.push({ lat: place.lat, lng: place.lng });
    };

    for (let d = 0; d < totalDays; d++) {
      const dayDate = addDaysLocal(start, d);
      const dayDateStr = toLocalIsoDate(dayDate);
      const dayId = this.generateId();
      const items: ItineraryItem[] = [];

      let dayPlaces: OfflineCuratedPlace[] = [];
      const cluster = isExplicitBongabonPreset
        ? dayClusterPresets[d % dayClusterPresets.length]
        : null;

      if (cluster) {
        dayPlaces = isSingleDay
          ? cluster.places.filter((p) => !this.isAccommodationPlace(p))
          : [...cluster.places];
        if (dayPlaces.length > targetStopsPerDay) {
          dayPlaces = dayPlaces.slice(0, targetStopsPerDay);
        }
        dayPlaces.forEach((p) => markPlaceUsed(p));
      } else {
        // Dynamic assignment preventing cross-day repetition
        if (d === 0 && anchorPlace) {
          if (!isSingleDay || !this.isAccommodationPlace(anchorPlace)) {
            dayPlaces.push(anchorPlace);
            markPlaceUsed(anchorPlace);
          }
        }

        // Find unused candidates from matchedPool using fuzzy deduplication (PREF-06)
        let candidates = matchedPool.filter((p) => !isPlaceDuplicate(p));
        if (isSingleDay) {
          candidates = candidates.filter((p) => !this.isAccommodationPlace(p));
        }

        if (candidates.length < targetStopsPerDay) {
          // Fill from general curatedPool without duplicating venues
          const extra = curatedPool.filter(
            (p) => !isPlaceDuplicate(p) && !candidates.some((c) => c.id === p.id) && (!isSingleDay || !this.isAccommodationPlace(p))
          );
          candidates = [...candidates, ...extra];
        }

        // Only if ALL unique venues across the entire province are exhausted do we allow recycling, but NEVER within the same day
        if (candidates.length < targetStopsPerDay) {
          const recyclable = curatedPool.filter(
            (p) => !dayPlaces.some((dp) => dp.id === p.id) && (!isSingleDay || !this.isAccommodationPlace(p))
          );
          candidates = [...candidates, ...recyclable];
        }

        // Add places up to targetStopsPerDay stops per day with Smart Midday Dining Anchor (PREF-05) and Max 1 Hike/Day
        while (dayPlaces.length < targetStopsPerDay && candidates.length > 0) {
          const currentSlot = dayPlaces.length;

          // Slot 1 (middle stop around noon): prioritize dining venue if available
          if (currentSlot === 1 && candidates.some((c) => this.isDiningVenue(c.categoryKey))) {
            const diningIdx = candidates.findIndex((c) => this.isDiningVenue(c.categoryKey));
            if (diningIdx >= 0) {
              const diningPlace = candidates.splice(diningIdx, 1)[0];
              dayPlaces.push(diningPlace);
              markPlaceUsed(diningPlace);
              continue;
            }
          }

          // Activity Intensity Guard: Max 1 mountain peak per day (PREF-05)
          const hasMountainAlready = dayPlaces.some((p) => this.isMountainPeak(p.name));
          let nextIdx = 0;
          if (hasMountainAlready) {
            nextIdx = candidates.findIndex((c) => !this.isMountainPeak(c.name));
            if (nextIdx < 0) nextIdx = 0;
          }

          const next = candidates.splice(nextIdx, 1)[0];
          if (next && !dayPlaces.some((p) => p.id === next.id)) {
            dayPlaces.push(next);
            markPlaceUsed(next);
          }
        }
      }

      // Check daily budget and substitute if exceeding daily_budget (only during dynamic generation)
      if (!cluster && dailyBudget && dayPlaces.length > 0) {
        const currentDayMinCost = dayPlaces.reduce((sum, p) => sum + (p.min ?? 0), 0);
        if (currentDayMinCost > dailyBudget) {
          // Try to find a free/cheaper alternative for the most expensive non-anchor place
          const nonAnchorPlaces = dayPlaces.filter((p) => !anchorPlace || p.id !== anchorPlace.id);
          if (nonAnchorPlaces.length > 0) {
            nonAnchorPlaces.sort((a, b) => (b.min ?? 0) - (a.min ?? 0));
            const mostExp = nonAnchorPlaces[0];
            const cheapReplacements = curatedPool.filter(
              (p) => !usedPlaceIds.has(p.id) && !dayPlaces.some((dp) => dp.id === p.id) && (p.min ?? 0) < (mostExp.min ?? 0)
            );
            if (cheapReplacements.length > 0) {
              const repIdx = dayPlaces.findIndex((p) => p.id === mostExp.id);
              if (repIdx >= 0) {
                usedPlaceIds.delete(mostExp.id);
                dayPlaces[repIdx] = cheapReplacements[0];
                usedPlaceIds.add(cheapReplacements[0].id);
              }
            }
          }
        }
      }

      for (let s = 0; s < dayPlaces.length; s++) {
        const place = dayPlaces[s];
        if (!place) continue;

        let plannedTime = place.time;
        if (!plannedTime) {
          if (s === 0) plannedTime = '09:00 AM - 11:30 AM';
          else if (s === 1) plannedTime = '12:30 PM - 02:30 PM';
          else plannedTime = '04:00 PM - 06:30 PM';
        }

        items.push({
          id: this.generateId(),
          day_id: dayId,
          place_id: place.id,
          custom_title: place.name,
          sort_order: s + 1,
          planned_time: plannedTime,
          duration_minutes: place.dur || 120,
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

      // DEF-03: Sort items strictly chronologically with overnight accommodations at day end
      items.sort((a, b) => {
        const aOvernight = this.isOvernightItem(a);
        const bOvernight = this.isOvernightItem(b);
        if (aOvernight && !bOvernight) return 1;
        if (!aOvernight && bOvernight) return -1;
        return this.parseTimeToMinutes(a.planned_time) - this.parseTimeToMinutes(b.planned_time);
      });

      items.forEach((item, idx) => {
        item.sort_order = idx + 1;
      });

      // Calculate offline routes, distances, and polylines
      const coords: [number, number][] = items
        .filter((it) => it.place?.latitude && it.place?.longitude)
        .map((it) => [it.place!.latitude, it.place!.longitude]);

      const dayOverviewPolyline = coords.length >= 2 ? encodePolyline(coords) : null;
      let totalDist = 0;
      let totalDur = 0;
      const routeLegs: RouteLegMetadata[] = [];

      for (let i = 0; i < items.length; i++) {
        const it = items[i];
        if (i === 0) {
          it.travel_distance_meters = null;
          it.travel_duration_seconds = null;
          it.route_polyline_from_prev = null;
          it.travel_mode_from_prev = 'DRIVE';
        } else {
          const prev = items[i - 1];
          const dist = Math.round(
            haversineDistanceMeters(
              prev.place!.latitude,
              prev.place!.longitude,
              it.place!.latitude,
              it.place!.longitude
            )
          );
          // Estimated driving speed 40 km/h (11.11 m/s)
          const dur = Math.round(dist / 11.11);
          const legPoly = encodePolyline([
            [prev.place!.latitude, prev.place!.longitude],
            [it.place!.latitude, it.place!.longitude],
          ]);

          it.travel_distance_meters = dist;
          it.travel_duration_seconds = dur;
          it.route_polyline_from_prev = legPoly;
          it.travel_mode_from_prev = 'DRIVE';

          totalDist += dist;
          totalDur += dur;

          routeLegs.push({
            start_location: { latitude: prev.place!.latitude, longitude: prev.place!.longitude },
            end_location: { latitude: it.place!.latitude, longitude: it.place!.longitude },
            distance_meters: dist,
            duration_seconds: dur,
            polyline: legPoly,
            steps: [
              {
                instruction: `Drive to ${it.place?.name || 'next stop'} (${dist}m)`,
                distance_meters: dist,
                duration_seconds: dur,
                polyline: legPoly,
                maneuver: 'straight',
              },
            ],
          });
        }
      }

      // Assign sequential, non-overlapping rolling time windows taking transit into account (PREF-04)
      const DEFAULT_SLOT_STARTS = [9 * 60 + 30, 12 * 60 + 0, 15 * 60 + 0]; // 09:30 AM, 12:00 PM, 03:00 PM
      let rollingMinutes = 9 * 60 + 30;

      items.forEach((item, idx) => {
        const dur = item.duration_minutes || (idx === 1 ? 90 : 120);
        const travelMins = idx > 0 && item.travel_duration_seconds
          ? Math.max(15, Math.round(item.travel_duration_seconds / 60))
          : (idx > 0 ? 20 : 0);
        const startMins = Math.max(DEFAULT_SLOT_STARTS[idx] ?? rollingMinutes, rollingMinutes + travelMins);
        const endMins = startMins + dur;
        item.planned_time = `${this.formatMinutesTo12Hr(startMins)} - ${this.formatMinutesTo12Hr(endMins)}`;
        rollingMinutes = endMins;
      });

      const primaryMuni =
        cluster?.municipality ||
        items[0]?.place?.municipality_name ||
        request.destination ||
        'Nueva Ecija';

      days.push({
        id: dayId,
        itinerary_id: itineraryId,
        day_number: d + 1,
        travel_date: dayDateStr,
        title: `Day ${d + 1}: ${primaryMuni}`,
        items,
        day_overview_polyline: dayOverviewPolyline,
        total_distance_meters: totalDist,
        total_travel_duration_seconds: totalDur,
        route_legs: routeLegs,
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
        `Pacing: ${targetStopsPerDay} stops scheduled per day to allow ${pacing} travel along provincial roads.`,
        `Geographic clustering: Stops on each day are clustered around ${request.destination || 'Nueva Ecija'} to prevent backtracking.`,
        'Budget & Expenses: Estimates reflect entrance, activities, and dining where available. Inter-town transit and fuel are not included.',
        'Operating Hours: Hours reflect verified public records; travelers are encouraged to verify schedules locally for holidays.',
        ...(isSingleDay ? ['Single-Day Itinerary: Planned as a day-trip getaway without overnight lodging.'] : []),
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