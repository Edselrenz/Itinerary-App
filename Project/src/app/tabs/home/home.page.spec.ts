import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { BehaviorSubject, of } from 'rxjs';
import { vi } from 'vitest';
import { HomePage } from './home.page';
import { PlaceService } from '../../core/services/place.service';
import { GuestItinerary, GuestStorageService } from '../../core/services/guest-storage.service';
import { Place } from '../../core/models/place.models';

describe('HomePage', () => {
  let component: HomePage;
  let fixture: ComponentFixture<HomePage>;

  const mockPlace: Place = {
    id: 'test-uuid-1',
    name: 'Minalungao National Park',
    category: 'nature_park',
    latitude: 15.2981,
    longitude: 121.1223,
    municipality_name: 'General Tinio',
    address_text: 'Brgy. Pias, General Tinio, Nueva Ecija',
    description: 'Protected limestone canyon along Peñaranda River.',
    estimated_cost_min: 100,
    estimated_cost_max: 500,
    cost_currency: 'PHP',
    source_name: 'CuratedNuevaEcijaMVP',
    source_record_id: 'curated/minalungao',
    imported_at: '2026-10-30T10:00:00Z',
    is_featured: true,
    tags: ['nature_park', 'Family-Friendly'],
    directions_url: 'https://www.google.com/maps/dir/?api=1&destination=15.2981,121.1223',
  };

  const isGuestModeSub = new BehaviorSubject<boolean>(true);
  const itinerariesSub = new BehaviorSubject<GuestItinerary[]>([]);

  const mockGuestStorage = {
    isGuestMode$: isGuestModeSub.asObservable(),
    itineraries$: itinerariesSub.asObservable(),
  };

  const mockPlaceService = {
    getFeaturedPlaces: vi.fn().mockReturnValue(of([mockPlace])),
    searchPlaces: vi.fn().mockReturnValue(of({ total: 1, limit: 20, offset: 0, items: [mockPlace] })),
    getPlaceImage: vi.fn().mockReturnValue('assets/images/minalungao.png'),
    formatCategoryName: vi.fn().mockReturnValue('Nature & Adventure'),
  };

  beforeEach(async () => {
    vi.clearAllMocks();
    mockPlaceService.getFeaturedPlaces.mockReturnValue(of([mockPlace]));
    mockPlaceService.searchPlaces.mockReturnValue(
      of({ total: 1, limit: 20, offset: 0, items: [mockPlace] })
    );

    await TestBed.configureTestingModule({
      imports: [HomePage],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: PlaceService, useValue: mockPlaceService },
        { provide: GuestStorageService, useValue: mockGuestStorage },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(HomePage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should load featured places on init', () => {
    expect(mockPlaceService.getFeaturedPlaces).toHaveBeenCalled();
    expect(component.destinations.length).toBeGreaterThan(0);
    expect(component.destinations[0].name).toBe('Minalungao National Park');
  });

  it('should execute debounced search and update search results', () => {
    vi.useFakeTimers();
    try {
      component.searchControl.setValue('Minalungao');
      vi.advanceTimersByTime(350); // wait for 300ms debounce
      fixture.detectChanges();

      expect(mockPlaceService.searchPlaces).toHaveBeenCalledWith({
        q: 'Minalungao',
        limit: 20,
      });
      expect(component.isSearching).toBe(true);
      expect(component.searchResults.length).toBe(1);
      expect(component.searchResults[0].name).toBe('Minalungao National Park');
    } finally {
      vi.useRealTimers();
    }
  });

  it('should clear search input and reset search results', () => {
    component.searchControl.setValue('Pantabangan');
    component.clearSearch();
    expect(component.searchControl.value).toBe('');
    expect(component.isSearching).toBe(false);
    expect(component.searchResults.length).toBe(0);
  });

  it('should open and close destination detail modal', () => {
    const dest = component.destinations[0];
    component.openDestinationDetail(dest);
    expect(component.isDetailModalOpen).toBe(true);
    expect(component.selectedDestination).toEqual(dest);

    component.closeDestinationDetail();
    expect(component.isDetailModalOpen).toBe(false);
    expect(component.selectedDestination).toBeNull();
  });

  it('should map honest prices with range or single cost', () => {
    const mapped = component.mapPlaceToDestination(mockPlace);
    expect(mapped.costDisplay).toBe('₱100 - ₱500');

    const placeNoCost: Place = { ...mockPlace, estimated_cost_min: null, estimated_cost_max: null };
    const mappedNoCost = component.mapPlaceToDestination(placeNoCost);
    expect(mappedNoCost.costDisplay).toBe('Cost not provided');
  });
});
