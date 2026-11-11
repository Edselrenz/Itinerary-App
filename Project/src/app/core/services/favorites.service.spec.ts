import { TestBed } from '@angular/core/testing';
import { FavoritesService } from './favorites.service';
import type { Place } from '../models/place.models';

describe('FavoritesService', () => {
  let service: FavoritesService;

  const mockPlace: Place = {
    id: 'place-test-1',
    name: 'Minalungao National Park',
    municipality_name: 'General Tinio',
    category: 'Nature & Parks',
    latitude: 15.2981,
    longitude: 121.1223,
    description: 'Iconic limestone river valley',
    estimated_cost_min: 100,
    estimated_cost_max: 300,
    cost_currency: 'PHP',
    source_name: 'manual',
    source_record_id: '1',
    imported_at: '2026-11-10T00:00:00Z',
    is_featured: true,
    tags: ['Nature'],
    directions_url: 'https://maps.google.com/?q=15.2981,121.1223',
  };

  const mockPlace2: Place = {
    id: 'place-test-2',
    name: 'Highland Bali Villas',
    municipality_name: 'Pantabangan',
    category: 'Resorts & Stays',
    latitude: 15.821,
    longitude: 121.145,
    description: 'Balinese resort overlooking Pantabangan lake',
    estimated_cost_min: 2500,
    estimated_cost_max: 5000,
    cost_currency: 'PHP',
    source_name: 'manual',
    source_record_id: '2',
    imported_at: '2026-11-10T00:00:00Z',
    is_featured: true,
    tags: ['Resort'],
    directions_url: 'https://maps.google.com/?q=15.821,121.145',
  };

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [FavoritesService],
    });
    service = TestBed.inject(FavoritesService);
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('should be created and initialize with default seed favorites', () => {
    expect(service).toBeTruthy();
    expect(service.getFavorites().length).toBeGreaterThan(0);
  });

  it('should toggle favorite places correctly', () => {
    service.clearFavorites();
    expect(service.getFavorites().length).toBe(0);

    const isFavNow = service.toggleFavorite(mockPlace);
    expect(isFavNow).toBe(true);
    expect(service.isFavorite(mockPlace.id)).toBe(true);
    expect(service.getFavorites().length).toBe(1);

    const isFavAfter = service.toggleFavorite(mockPlace);
    expect(isFavAfter).toBe(false);
    expect(service.isFavorite(mockPlace.id)).toBe(false);
    expect(service.getFavorites().length).toBe(0);
  });

  it('should add and remove favorite by id', () => {
    service.clearFavorites();
    service.addFavorite(mockPlace);
    service.addFavorite(mockPlace2);
    expect(service.getFavorites().length).toBe(2);

    service.removeFavorite(mockPlace.id);
    expect(service.getFavorites().length).toBe(1);
    expect(service.isFavorite(mockPlace.id)).toBe(false);
    expect(service.isFavorite(mockPlace2.id)).toBe(true);
  });
});
