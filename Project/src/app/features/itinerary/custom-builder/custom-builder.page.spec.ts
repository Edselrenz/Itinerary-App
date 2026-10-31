import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { of, throwError } from 'rxjs';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { AlertController, ToastController } from '@ionic/angular';
import { CustomBuilderPage } from './custom-builder.page';
import { ItineraryService } from '../../../core/services/itinerary.service';
import { PlaceService } from '../../../core/services/place.service';
import { Place } from '../../../core/models/place.models';
import { Itinerary } from '../../../core/models/itinerary.models';

describe('CustomBuilderPage', () => {
  let component: CustomBuilderPage;
  let fixture: ComponentFixture<CustomBuilderPage>;
  let router: Router;

  const mockPlace: Place = {
    id: 'poi-test-1',
    name: 'Minalungao National Park',
    category: 'nature_park',
    latitude: 15.2981,
    longitude: 121.1223,
    municipality_name: 'General Tinio',
    address_text: 'Brgy. Pias, General Tinio, Nueva Ecija',
    description: 'Limestone cliffs and river rafting.',
    estimated_cost_min: 150,
    estimated_cost_max: 450,
    cost_currency: 'PHP',
    source_name: 'CuratedNuevaEcijaMVP',
    source_record_id: 'curated/minalungao',
    imported_at: '2026-10-30T10:00:00Z',
    is_featured: true,
    tags: ['nature_park'],
    directions_url: 'https://www.google.com/maps/dir/?api=1&destination=15.2981,121.1223',
  };

  const mockPlaceService = {
    getFeaturedPlaces: vi.fn().mockReturnValue(of([mockPlace])),
    searchPlaces: vi.fn().mockReturnValue(of({ total: 1, limit: 20, offset: 0, items: [mockPlace] })),
    getPlaceImage: vi.fn().mockReturnValue('assets/images/minalungao.png'),
    formatCategoryName: vi.fn().mockReturnValue('Nature & Adventure'),
  };

  const mockItineraryService = {
    getItineraryById: vi.fn().mockReturnValue(
      of({
        id: 'itin-1',
        title: 'Loaded Trip',
        destination: 'Nueva Ecija',
        start_date: '2026-11-01',
        end_date: '2026-11-02',
        daily_budget: 3000,
        preferences: [],
        type: 'custom',
        assumptions: [],
        created_at: '2026-10-31T00:00:00Z',
        days: [
          {
            id: 'day-1',
            itinerary_id: 'itin-1',
            day_number: 1,
            travel_date: '2026-11-01',
            title: 'Day 1',
            items: [],
          },
        ],
      })
    ),
    createItinerary: vi.fn().mockReturnValue(
      of({
        id: 'itin-created',
        title: 'Nueva Ecija Getaway',
        destination: 'Nueva Ecija',
        start_date: '2026-11-01',
        end_date: '2026-11-02',
        daily_budget: 2500,
        days: [],
      })
    ),
    updateItinerary: vi.fn().mockReturnValue(of({})),
    calculateBudgetSummary: vi.fn().mockReturnValue({
      verifiedMin: 150,
      verifiedMax: 450,
      unverifiedCount: 0,
      displayText: '₱150 - ₱450',
    }),
  };

  beforeEach(async () => {
    vi.clearAllMocks();
    mockPlaceService.getFeaturedPlaces.mockReturnValue(of([mockPlace]));
    mockPlaceService.searchPlaces.mockReturnValue(
      of({ total: 1, limit: 20, offset: 0, items: [mockPlace] })
    );

    const mockToast = { present: vi.fn().mockResolvedValue(undefined) };
    const mockToastController = { create: vi.fn().mockResolvedValue(mockToast) };
    const mockAlert = { present: vi.fn().mockResolvedValue(undefined) };
    const mockAlertController = { create: vi.fn().mockResolvedValue(mockAlert) };

    await TestBed.configureTestingModule({
      imports: [CustomBuilderPage],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: PlaceService, useValue: mockPlaceService },
        { provide: ItineraryService, useValue: mockItineraryService },
        { provide: ToastController, useValue: mockToastController },
        { provide: AlertController, useValue: mockAlertController },
      ],
    }).compileComponents();

    router = TestBed.inject(Router);
    vi.spyOn(router, 'navigate').mockImplementation(() => Promise.resolve(true));

    fixture = TestBed.createComponent(CustomBuilderPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create the custom builder component and initialize days', () => {
    expect(component).toBeTruthy();
    expect(component.days.length).toBeGreaterThanOrEqual(1);
    expect(component.currentDay).toBeTruthy();
    expect(component.currentDay?.day_number).toBe(1);
  });

  it('allows adding and selecting a new day', () => {
    const initialDays = component.days.length;
    component.addDay();
    expect(component.days.length).toBe(initialDays + 1);
    expect(component.activeDayIndex).toBe(component.days.length - 1);
    expect(component.hasUnsavedChanges).toBe(true);

    component.selectDay(0);
    expect(component.activeDayIndex).toBe(0);
  });

  it('allows adding and reordering stops in the current day', () => {
    // Add first stop
    component.selectPlaceFromPicker(mockPlace);
    expect(component.currentDay?.items.length).toBe(1);
    expect(component.currentDay?.items[0].place_id).toBe('poi-test-1');
    expect(component.currentDay?.items[0].sort_order).toBe(1);

    // Add a second off-grid stop
    component.customVenueTitle = "Lola's Mango Orchard";
    component.customVenueAddress = 'Bongabon';
    component.customVenueCostMin = 100;
    component.customVenueCostMax = 200;
    component.addCustomVenueStop();

    expect(component.currentDay?.items.length).toBe(2);
    expect(component.currentDay?.items[1].name).toBe("Lola's Mango Orchard");
    expect(component.currentDay?.items[1].sort_order).toBe(2);

    // Move second stop up
    component.moveStopUp(1);
    expect(component.currentDay?.items[0].name).toBe("Lola's Mango Orchard");
    expect(component.currentDay?.items[0].sort_order).toBe(1);
    expect(component.currentDay?.items[1].name).toBe('Minalungao National Park');
    expect(component.currentDay?.items[1].sort_order).toBe(2);

    // Move first stop down
    component.moveStopDown(0);
    expect(component.currentDay?.items[0].name).toBe('Minalungao National Park');
    expect(component.currentDay?.items[1].name).toBe("Lola's Mango Orchard");
  });

  it('removes a stop and recalculates sort order', () => {
    component.selectPlaceFromPicker(mockPlace);
    expect(component.currentDay?.items.length).toBe(1);

    component.removeStop(0);
    expect(component.currentDay?.items.length).toBe(0);
  });

  it('saves itinerary successfully and navigates back to /tabs/home', async () => {
    component.selectPlaceFromPicker(mockPlace);
    await component.saveItinerary();

    expect(mockItineraryService.createItinerary).toHaveBeenCalled();
    expect(router.navigate).toHaveBeenCalledWith(['/tabs/home']);
    expect(component.hasUnsavedChanges).toBe(false);
  });

  it('handles cancel with no unsaved changes cleanly', async () => {
    component.hasUnsavedChanges = false;
    await component.onCancel();
    expect(router.navigate).toHaveBeenCalledWith(['/tabs/home']);
  });
});
