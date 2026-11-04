import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, catchError, from, map, of, switchMap, tap, throwError, timeout } from 'rxjs';
import { addDaysLocal, diffDaysLocal, parseLocalIsoDate, toLocalIsoDate } from '../utils/date.utils';
import {
  getOfflineCuratedPoolForItinerary,
  getOfflineDayClusterPresets,
  OfflineCuratedPlace,
} from '../data/offline-places.data';
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
  private get baseUrl(): string {
    return `${environment.apiBaseUrl}/itineraries`;
  }

  private readonly itinerariesSubject = new BehaviorSubject<Itinerary[]>([]);
  public itineraries$: Observable<Itinerary[]> = this.itinerariesSubject.asObservable();

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
   * If in guest mode (e.g. static GitHub Pages), immediately generates locally for instant response.
   */
  public suggestItinerary(request: SuggestedItineraryRequest): Observable<Itinerary> {
    return this.http.post<Itinerary>(`${this.baseUrl}/suggest`, request).pipe(
      timeout(4000),
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

  private async generateOfflineSuggestedItinerary(
    request: SuggestedItineraryRequest
  ): Promise<Itinerary> {
    const totalDays = diffDaysLocal(request.start_date, request.end_date);
    const start = parseLocalIsoDate(request.start_date);

    // Canonical curated offline places dataset (DEF-05)
    const curatedPool: OfflineCuratedPlace[] = getOfflineCuratedPoolForItinerary();

    const targetDest = (request.destination || '').toLowerCase().trim();
    const prefs = (request.preferences || []).map((p) => p.toLowerCase());

    // Dynamically filter or prioritize pool based on destination municipality and category preferences (CR-009)
    let matchedPool = curatedPool;
    if (targetDest && !targetDest.includes('nueva ecija')) {
      const muniMatches = curatedPool.filter((p) => p.municipality.toLowerCase().includes(targetDest));
      if (muniMatches.length > 0) {
        matchedPool = muniMatches;
      }
    }

    if (prefs.length > 0) {
      matchedPool = [...matchedPool].sort((a: OfflineCuratedPlace, b: OfflineCuratedPlace) => {
        const aMatches = prefs.some(
          (pr: string) => a.categoryKey.toLowerCase().includes(pr) || a.tags.some((t: string) => t.toLowerCase().includes(pr))
        ) ? 1 : 0;
        const bMatches = prefs.some(
          (pr: string) => b.categoryKey.toLowerCase().includes(pr) || b.tags.some((t: string) => t.toLowerCase().includes(pr))
        ) ? 1 : 0;
        return bMatches - aMatches;
      });
    }

    const isProvincialOrBongabon = !targetDest || targetDest.includes('nueva') || targetDest.includes('ecija') || targetDest.includes('bongabon');

    // Clustered day-by-day presets from canonical dataset (DEF-03, DEF-05)
    const dayClusterPresets = getOfflineDayClusterPresets(curatedPool);

    const itineraryId = this.generateId();
    const days: ItineraryDay[] = [];
    const now = new Date().toISOString();

    for (let d = 0; d < totalDays; d++) {
      const dayDate = addDaysLocal(start, d);
      const dayDateStr = toLocalIsoDate(dayDate);
      const dayId = this.generateId();
      const items: ItineraryItem[] = [];

      const cluster = isProvincialOrBongabon
        ? dayClusterPresets[d % dayClusterPresets.length]
        : null;

      const dayPlaces = cluster?.places || [
        curatedPool[0],
        curatedPool[1],
        curatedPool[2],
      ];

      for (let s = 0; s < dayPlaces.length; s++) {
        const place = dayPlaces[s];
        if (!place) continue;

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

      const primaryMuni = cluster?.municipality || items[0]?.place?.municipality_name || request.destination || 'Nueva Ecija';
      days.push({
        id: dayId,
        itinerary_id: itineraryId,
        day_number: d + 1,
        travel_date: dayDateStr,
        title: `Day ${d + 1}: ${primaryMuni}`,
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