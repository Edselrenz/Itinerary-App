import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import type { Place } from '../models/place.models';
import { getOfflinePlacesAsPlaceEntities } from '../data/offline-places.data';

@Injectable({
  providedIn: 'root',
})
export class FavoritesService {
  private static readonly STORAGE_KEY = 'ne_favorite_places_v1';
  private favoritesSubject = new BehaviorSubject<Place[]>([]);
  public favorites$: Observable<Place[]> = this.favoritesSubject.asObservable();

  constructor() {
    this.loadFavorites();
  }

  public getFavorites(): Place[] {
    return this.favoritesSubject.value;
  }

  public isFavorite(placeId: string): boolean {
    if (!placeId) return false;
    return this.favoritesSubject.value.some((p) => p.id === placeId);
  }

  public toggleFavorite(place: Place): boolean {
    if (!place || !place.id) return false;
    const current = this.favoritesSubject.value;
    const exists = current.some((p) => p.id === place.id);

    let updated: Place[];
    if (exists) {
      updated = current.filter((p) => p.id !== place.id);
    } else {
      updated = [place, ...current];
    }

    this.saveFavorites(updated);
    return !exists;
  }

  public addFavorite(place: Place): void {
    if (!place || !place.id || this.isFavorite(place.id)) return;
    const updated = [place, ...this.favoritesSubject.value];
    this.saveFavorites(updated);
  }

  public removeFavorite(placeId: string): void {
    if (!placeId) return;
    const updated = this.favoritesSubject.value.filter((p) => p.id !== placeId);
    this.saveFavorites(updated);
  }

  public clearFavorites(): void {
    this.saveFavorites([]);
  }

  private loadFavorites(): void {
    try {
      if (typeof localStorage !== 'undefined') {
        const raw = localStorage.getItem(FavoritesService.STORAGE_KEY);
        if (raw) {
          const parsed = JSON.parse(raw);
          if (Array.isArray(parsed) && parsed.length > 0) {
            this.favoritesSubject.next(parsed);
            return;
          }
        }
      }
    } catch {
      // Fallback
    }

    // Default seed with 3 iconic featured Nueva Ecija places so Favorites tab is not empty on first visit
    const seedPlaces = getOfflinePlacesAsPlaceEntities().slice(0, 3);
    this.saveFavorites(seedPlaces);
  }

  private saveFavorites(places: Place[]): void {
    this.favoritesSubject.next(places);
    try {
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem(FavoritesService.STORAGE_KEY, JSON.stringify(places));
      }
    } catch {
      // Storage unavailable
    }
  }
}
