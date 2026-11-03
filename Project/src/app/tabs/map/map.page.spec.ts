import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { ActivatedRoute, Router } from '@angular/router';
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
    getMunicipalities: vi.fn().mockReturnValue(
      of([{ id: 'm-1', name: 'General Tinio' }, { id: 'm-2', name: 'Bongabon' }])
    ),
  };

  const mockRouter = {
    navigate: vi.fn(),
  };

  beforeEach(async () => {
    vi.clearAllMocks();
    mockPlaceService.searchPlaces.mockReturnValue(
      of({ total: 1, limit: 100, offset: 0, items: [mockPlace] })
    );
    mockPlaceService.getFeaturedPlaces.mockReturnValue(of([mockPlace]));
    mockPlaceService.getMunicipalities.mockReturnValue(
      of([{ id: 'm-1', name: 'General Tinio' }, { id: 'm-2', name: 'Bongabon' }])
    );

    await TestBed.configureTestingModule({
      imports: [MapPage],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: PlaceService, useValue: mockPlaceService },
        { provide: Router, useValue: mockRouter },
        {
          provide: ActivatedRoute,
          useValue: {
            queryParams: of({}),
          },
        },
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

  it('should filter places when a category is selected via quick pill', () => {
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

    expect(mockPlaceService.getFeaturedPlaces).toHaveBeenCalledWith(50);
    expect(component.places.length).toBe(1);
  });

  it('should format cost ranges honestly and handle null costs', () => {
    expect(component.formatCost(mockPlace)).toBe('₱100 - ₱500');

    const placeMinOnly: Place = { ...mockPlace, estimated_cost_min: 250, estimated_cost_max: null };
    expect(component.formatCost(placeMinOnly)).toBe('From ₱250');

    const placeMaxOnly: Place = { ...mockPlace, estimated_cost_min: null, estimated_cost_max: 1000 };
    expect(component.formatCost(placeMaxOnly)).toBe('Up to ₱1000');

    const placeNoCost: Place = { ...mockPlace, estimated_cost_min: null, estimated_cost_max: null };
    expect(component.formatCost(placeNoCost)).toBe('Fee: Not verified / Not provided');

    const placeFree: Place = { ...mockPlace, estimated_cost_min: 0, estimated_cost_max: 0 };
    expect(component.formatCost(placeFree)).toBe('Free Admission (₱0)');
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

  it('should initialize hasTileError as false', () => {
    expect(component.hasTileError).toBe(false);
  });

  it('creates accessible map pins with role="button" and tabindex="0" (DEF-09)', () => {
    const addedMarkers: any[] = [];
    component.markerCluster = {
      clearLayers: vi.fn(),
      addLayer: vi.fn((marker: any) => addedMarkers.push(marker)),
    } as any;

    component.places = [mockPlace];
    component.updateMarkers();

    expect(addedMarkers.length).toBe(1);
    const iconHtml = addedMarkers[0].options.icon.options.html as string;
    expect(iconHtml).toContain('tabindex="0"');
    expect(iconHtml).toContain('role="button"');
    expect(iconHtml).toContain('aria-label="Minalungao National Park, General Tinio"');
    expect(iconHtml).toContain('title="Minalungao National Park"');
  });

  // --- Phase 19: UI-16 Floating Search Bar & Multi-Select Filter Sheet ---

  it('should handle search input and clear search (UI-16)', () => {
    component.onSearchInput({ target: { value: 'Minalungao' } } as unknown as Event);
    expect(component.searchQuery).toBe('Minalungao');

    component.clearSearch();
    expect(component.searchQuery).toBe('');
  });

  it('should toggle multi-select categories and calculate active filter count (UI-16)', () => {
    expect(component.activeFilterCount).toBe(0);

    component.toggleCategoryFilter('nature_park');
    expect(component.isCategorySelected('nature_park')).toBe(true);
    expect(component.activeFilterCount).toBe(1);

    component.toggleCategoryFilter('restaurant');
    expect(component.isCategorySelected('restaurant')).toBe(true);
    expect(component.activeFilterCount).toBe(2);

    component.toggleCategoryFilter('nature_park');
    expect(component.isCategorySelected('nature_park')).toBe(false);
    expect(component.activeFilterCount).toBe(1);
  });

  it('should select municipality and price tier filters (UI-16)', () => {
    component.selectMunicipality('General Tinio');
    expect(component.selectedMunicipality).toBe('General Tinio');
    expect(component.activeFilterCount).toBe(1);

    component.selectPriceTier('budget');
    expect(component.selectedPriceTier).toBe('budget');
    expect(component.activeFilterCount).toBe(2);

    // Toggle off municipality
    component.selectMunicipality('General Tinio');
    expect(component.selectedMunicipality).toBeNull();
    expect(component.activeFilterCount).toBe(1);
  });

  it('should reset all filters (UI-16)', () => {
    component.toggleCategoryFilter('nature_park');
    component.selectMunicipality('General Tinio');
    component.selectPriceTier('free');
    expect(component.activeFilterCount).toBe(3);

    component.resetFilters();
    expect(component.selectedCategories.size).toBe(0);
    expect(component.selectedCategory).toBeNull();
    expect(component.selectedMunicipality).toBeNull();
    expect(component.selectedPriceTier).toBe('all');
    expect(component.activeFilterCount).toBe(0);
  });

  it('should open and close the filter bottom sheet (UI-16)', () => {
    expect(component.isFilterSheetOpen).toBe(false);

    component.openFilterSheet();
    expect(component.isFilterSheetOpen).toBe(true);

    component.closeFilterSheet();
    expect(component.isFilterSheetOpen).toBe(false);
  });

  // --- Phase 19: UI-16 Accessible Collapsible POI List Drawer ---

  it('should toggle and select place from POI list drawer (UI-16)', () => {
    expect(component.isPoiDrawerOpen).toBe(false);

    component.openPoiDrawer();
    expect(component.isPoiDrawerOpen).toBe(true);

    component.togglePoiDrawer();
    expect(component.isPoiDrawerOpen).toBe(false);

    component.openPoiDrawer();
    component.selectPlaceFromDrawer(mockPlace);

    expect(component.selectedPlace).toEqual(mockPlace);
    expect(component.isPoiDrawerOpen).toBe(false);
  });

  // --- Phase 19: UI-17 Bottom Sheet Itinerary Integration Actions ---

  it('should navigate to suggested wizard with "Start Trip Here" CTA (UI-17)', () => {
    component.startTripHere(mockPlace);

    expect(mockRouter.navigate).toHaveBeenCalledWith(['/suggested-wizard'], {
      queryParams: {
        destination: 'General Tinio',
        placeId: 'test-place-1',
      },
    });
  });

  it('should navigate to custom builder with "Add to Custom Trip" CTA (UI-17)', () => {
    component.addToCustomTrip(mockPlace);

    expect(mockRouter.navigate).toHaveBeenCalledWith(['/custom-builder'], {
      queryParams: {
        destination: 'General Tinio',
        addPlaceId: 'test-place-1',
      },
    });
  });

  // --- Phase 19: UI-17 Viewport Bounds Querying ---

  it('should pass viewport bounds to PlaceService when bounds are provided (UI-17)', () => {
    const mockBounds = {
      getSouth: () => 15.2,
      getNorth: () => 15.6,
      getWest: () => 120.8,
      getEast: () => 121.2,
    } as unknown as L.LatLngBounds;

    component.loadPlaces(mockBounds);

    expect(mockPlaceService.searchPlaces).toHaveBeenCalledWith({
      min_lat: 15.2,
      max_lat: 15.6,
      min_lng: 120.8,
      max_lng: 121.2,
      limit: 150,
    });
  });
});
