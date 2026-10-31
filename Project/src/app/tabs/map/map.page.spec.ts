import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { of, throwError } from 'rxjs';
import { describe, it, expect, beforeEach, vi } from 'vitest';

import { MapPage, CATEGORY_FILTERS } from './map.page';
import { PlaceService } from '../../core/services/place.service';
import { Place } from '../../core/models/place.models';

describe('MapPage', () => {
  let component: MapPage;
  let fixture: ComponentFixture<MapPage>;

  const mockPlace: Place = {
    id: 'test-place-1',
    name: 'Minalungao National Park',
    category: 'nature_park',
    latitude: 15.2981,
    longitude: 121.1223,
    municipality_name: 'General Tinio',
    address_text: 'Brgy. Pias, General Tinio, Nueva Ecija',
    description: 'Protected limestone canyon along Peñaranda River.',
    opening_hours: '06:00 - 18:00',
    estimated_cost_min: 100,
    estimated_cost_max: 500,
    cost_currency: 'PHP',
    source_name: 'CuratedNuevaEcijaMVP',
    source_record_id: 'curated/minalungao',
    imported_at: '2026-10-30T10:00:00Z',
    is_featured: true,
    tags: ['nature_park', 'adventure'],
    directions_url: 'https://www.google.com/maps/dir/?api=1&destination=15.2981,121.1223',
  };

  const mockPlaceService = {
    searchPlaces: vi.fn().mockReturnValue(
      of({ total: 1, limit: 100, offset: 0, items: [mockPlace] })
    ),
    getFeaturedPlaces: vi.fn().mockReturnValue(of([mockPlace])),
    getPlaceImage: vi.fn().mockReturnValue('assets/images/minalungao.png'),
    formatCategoryName: vi.fn().mockReturnValue('Nature & Parks'),
  };

  beforeEach(async () => {
    vi.clearAllMocks();
    mockPlaceService.searchPlaces.mockReturnValue(
      of({ total: 1, limit: 100, offset: 0, items: [mockPlace] })
    );
    mockPlaceService.getFeaturedPlaces.mockReturnValue(of([mockPlace]));

    await TestBed.configureTestingModule({
      imports: [MapPage],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: PlaceService, useValue: mockPlaceService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(MapPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create the map page component', () => {
    expect(component).toBeTruthy();
  });

  it('should initialize with 17 canonical category filters (1 All + 16 categories)', () => {
    expect(component.categoryFilters.length).toBe(17);
    expect(component.categoryFilters[0].key).toBeNull();
    expect(component.categoryFilters[0].label).toBe('All Places');
    expect(component.selectedCategory).toBeNull();
  });

  it('should load places from PlaceService on initialization', () => {
    expect(mockPlaceService.searchPlaces).toHaveBeenCalledWith({ limit: 100 });
    expect(component.places.length).toBe(1);
    expect(component.places[0].name).toBe('Minalungao National Park');
  });

  it('should filter places when a category is selected', () => {
    component.selectCategory('nature_park');

    expect(component.selectedCategory).toBe('nature_park');
    expect(component.selectedPlace).toBeNull();
    expect(mockPlaceService.searchPlaces).toHaveBeenCalledWith({
      categories: ['nature_park'],
      limit: 100,
    });
  });

  it('should fall back to featured places if searchPlaces fails', () => {
    mockPlaceService.searchPlaces.mockReturnValue(
      throwError(() => new Error('Network error'))
    );

    component.loadPlaces();

    expect(mockPlaceService.getFeaturedPlaces).toHaveBeenCalledWith(25);
    expect(component.places.length).toBe(1);
  });

  it('should format cost ranges honestly and handle null costs', () => {
    expect(component.formatCost(mockPlace)).toBe('₱100 - ₱500');

    const placeMinOnly: Place = { ...mockPlace, estimated_cost_min: 250, estimated_cost_max: null };
    expect(component.formatCost(placeMinOnly)).toBe('From ₱250');

    const placeMaxOnly: Place = { ...mockPlace, estimated_cost_min: null, estimated_cost_max: 1000 };
    expect(component.formatCost(placeMaxOnly)).toBe('Up to ₱1000');

    const placeNoCost: Place = { ...mockPlace, estimated_cost_min: null, estimated_cost_max: null };
    expect(component.formatCost(placeNoCost)).toBe('Cost not provided');
  });

  it('should return directions URL or fallback to coordinate link', () => {
    expect(component.getDirectionsUrl(mockPlace)).toBe(
      'https://www.google.com/maps/dir/?api=1&destination=15.2981,121.1223'
    );

    const placeNoUrl: Place = { ...mockPlace, directions_url: '' };
    expect(component.getDirectionsUrl(placeNoUrl)).toBe(
      'https://www.google.com/maps/dir/?api=1&destination=15.2981,121.1223'
    );
  });

  it('should open and close the bottom sheet', () => {
    component.selectedPlace = mockPlace;
    expect(component.selectedPlace).toBeTruthy();

    component.closeBottomSheet();
    expect(component.selectedPlace).toBeNull();
  });

  it('should safely recenter map when map instance exists', () => {
    const flyToSpy = vi.fn();
    const removeSpy = vi.fn();
    component.map = { flyTo: flyToSpy, remove: removeSpy } as unknown as L.Map;

    component.recenterMap();

    expect(flyToSpy).toHaveBeenCalledWith([15.58, 121.0], 10, { duration: 0.8 });
  });
});

