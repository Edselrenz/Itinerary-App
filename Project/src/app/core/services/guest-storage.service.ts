import { Injectable } from '@angular/core';
import { Storage } from '@ionic/storage-angular';
import { BehaviorSubject, Observable } from 'rxjs';

export interface GuestItinerary {
  id: string;
  title: string;
  destination: string;
  start_date: string;
  end_date: string;
  daily_budget: number;
  preferences: string[];
  type: 'suggested' | 'custom';
  assumptions: string[];
  days: any[];
  created_at: string;
  updated_at: string;
}

@Injectable({
  providedIn: 'root',
})
export class GuestStorageService {
  private static readonly STORAGE_KEY = 'ne_guest_itineraries_v1';
  private static readonly GUEST_MODE_KEY = 'ne_is_guest_mode_v1';

  private storageInstance: Storage | null = null;
  private readonly initPromise: Promise<void>;

  private readonly guestModeSubject = new BehaviorSubject<boolean>(false);
  public isGuestMode$: Observable<boolean> = this.guestModeSubject.asObservable();

  private readonly itinerariesSubject = new BehaviorSubject<GuestItinerary[]>([]);
  public itineraries$: Observable<GuestItinerary[]> = this.itinerariesSubject.asObservable();

  constructor(private storage: Storage) {
    this.initPromise = this.init();
  }

  private async init(): Promise<void> {
    try {
      this.storageInstance = await this.storage.create();
    } catch {
      // Fallback in case of mock/web environment
      this.storageInstance = null;
    }

    const savedMode = await this.getItem<boolean>(GuestStorageService.GUEST_MODE_KEY);
    this.guestModeSubject.next(savedMode === true);

    const itineraries = (await this.getItem<GuestItinerary[]>(GuestStorageService.STORAGE_KEY)) || [];
    this.itinerariesSubject.next(itineraries);
  }

  public async setGuestMode(active: boolean): Promise<void> {
    await this.initPromise;
    await this.setItem(GuestStorageService.GUEST_MODE_KEY, active);
    this.guestModeSubject.next(active);
  }

  public isGuest(): boolean {
    return this.guestModeSubject.value;
  }

  public async getItineraries(): Promise<GuestItinerary[]> {
    await this.initPromise;
    const items = (await this.getItem<GuestItinerary[]>(GuestStorageService.STORAGE_KEY)) || [];
    this.itinerariesSubject.next(items);
    return items;
  }

  public async saveItinerary(itinerary: GuestItinerary): Promise<void> {
    await this.initPromise;
    const current = await this.getItineraries();
    const existingIndex = current.findIndex((i) => i.id === itinerary.id);

    if (existingIndex >= 0) {
      current[existingIndex] = { ...itinerary, updated_at: new Date().toISOString() };
    } else {
      current.unshift(itinerary);
    }

    await this.setItem(GuestStorageService.STORAGE_KEY, current);
    this.itinerariesSubject.next([...current]);
  }

  public async deleteItinerary(id: string): Promise<void> {
    await this.initPromise;
    const current = await this.getItineraries();
    const filtered = current.filter((i) => i.id !== id);
    await this.setItem(GuestStorageService.STORAGE_KEY, filtered);
    this.itinerariesSubject.next([...filtered]);
  }

  public async clearGuestData(): Promise<void> {
    await this.initPromise;
    await this.removeItem(GuestStorageService.STORAGE_KEY);
    await this.removeItem(GuestStorageService.GUEST_MODE_KEY);
    this.guestModeSubject.next(false);
    this.itinerariesSubject.next([]);
  }

  private async getItem<T>(key: string): Promise<T | null> {
    if (this.storageInstance) {
      return await this.storageInstance.get(key);
    }
    const val = localStorage.getItem(key);
    return val ? (JSON.parse(val) as T) : null;
  }

  private async setItem<T>(key: string, value: T): Promise<void> {
    if (this.storageInstance) {
      await this.storageInstance.set(key, value);
    } else {
      localStorage.setItem(key, JSON.stringify(value));
    }
  }

  private async removeItem(key: string): Promise<void> {
    if (this.storageInstance) {
      await this.storageInstance.remove(key);
    } else {
      localStorage.removeItem(key);
    }
  }
}

