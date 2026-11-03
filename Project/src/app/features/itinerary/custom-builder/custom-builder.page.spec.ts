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
  let mockAlertController: any;
  let mockToastController: any;

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
    mockToastController = { create: vi.fn().mockResolvedValue(mockToast) };
    const mockAlert = { present: vi.fn().mockResolvedValue(undefined) };
    mockAlertController = { create: vi.fn().mockResolvedValue(mockAlert) };

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

  it('should create the custom builder component and initialize in form view', () => {
    expect(component).toBeTruthy();
    expect(component.activeView).toBe('form');
    expect(component.days.length).toBeGreaterThanOrEqual(1);
    expect(component.currentDay).toBeTruthy();
    expect(component.currentDay?.day_number).toBe(1);
  });

  it('supports preference toggling and date duration formatting', () => {
    expect(component.isPreferenceSelected('nature')).toBe(false);
    component.togglePreference('nature');
    expect(component.isPreferenceSelected('nature')).toBe(true);
    component.togglePreference('nature');
    expect(component.isPreferenceSelected('nature')).toBe(false);

    expect(component.formattedTripDateSubtitle).toContain('day');
    component.form.patchValue({ start_date: '', end_date: '' });
    expect(component.formattedTripDateSubtitle).toContain('e.g.');
  });

  it('proceeds to builder browse view and syncs days on find itinerary', () => {
    component.togglePreference('food');
    component.proceedToBuilder();
    expect(component.activeView).toBe('browse');
    expect(component.selectedCategory).toBe('Food');

    component.backToForm();
    expect(component.activeView).toBe('form');
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

  it('removes a stop and recalculates sort order', async () => {
    component.selectPlaceFromPicker(mockPlace);
    expect(component.currentDay?.items.length).toBe(1);

    await component.removeStop(0);
    expect(mockAlertController.create).toHaveBeenCalled();
    component.executeRemoveStop(component.currentDay!, 0);
    expect(component.currentDay?.items.length).toBe(0);
  });

  it('saves itinerary successfully and navigates back to /tabs/home', async () => {
    component.selectPlaceFromPicker(mockPlace);
    await component.saveItinerary();

    expect(mockItineraryService.createItinerary).toHaveBeenCalled();
    expect(router.navigate).toHaveBeenCalledWith(['/tabs/home']);
    expect(component.hasUnsavedChanges).toBe(false);
  });

  it('saves edited itinerary with days and stops intact (CR-003)', async () => {
    component.isEditMode = true;
    component.itineraryId = 'itin-1';
    component.days = [
      {
        id: 'day-1',
        day_number: 1,
        travel_date: '2026-11-01',
        title: 'Day 1',
        items: [
          {
            id: 'stop-1',
            place_id: mockPlace.id,
            name: mockPlace.name,
            category: 'nature',
            municipality: 'General Tinio',
            image: '',
            sort_order: 1,
            duration_minutes: 90,
            estimated_cost_min: 150,
            estimated_cost_max: 450,
            isCustomVenue: false,
          },
        ],
      },
    ];

    await component.saveItinerary();

    expect(mockItineraryService.updateItinerary).toHaveBeenCalledWith(
      'itin-1',
      expect.objectContaining({
        title: expect.any(String),
        days: expect.arrayContaining([
          expect.objectContaining({
            day_number: 1,
            items: expect.arrayContaining([
              expect.objectContaining({ place_id: mockPlace.id }),
            ]),
          }),
        ]),
      })
    );
    expect(router.navigate).toHaveBeenCalledWith(['/tabs/home']);
    expect(component.hasUnsavedChanges).toBe(false);
  });

  it('handles cancel with no unsaved changes cleanly', async () => {
    component.hasUnsavedChanges = false;
    await component.onCancel();
    expect(router.navigate).toHaveBeenCalledWith(['/tabs/home']);
  });
  it('should handle date picker pop-up window workflow correctly', () => {
    expect(component.isDatePickerOpen).toBe(false);

    component.openDatePicker();
    expect(component.isDatePickerOpen).toBe(true);
    expect(component.popupStartDate).toBeTruthy();
    expect(component.popupEndDate).toBeTruthy();

    component.popupStartDate = '2026-11-15';
    component.popupEndDate = '2026-11-18';
    expect(component.tempTripSummary.isValid).toBe(true);
    expect(component.tempTripSummary.days).toBe(4);

    component.setPresetDuration(2);
    expect(component.popupEndDate).toBe('2026-11-16');

    component.applyDatePicker();
    expect(component.isDatePickerOpen).toBe(false);
    expect(component.form.get('start_date')?.value).toBe('2026-11-15');
    expect(component.form.get('end_date')?.value).toBe('2026-11-16');

    expect(component.displayDateRangeText).toContain('Nov 15');
    expect(component.hasSelectedDates).toBe(true);

    component.openDatePicker();
    expect(component.isDatePickerOpen).toBe(true);
    component.closeDatePicker();
    expect(component.isDatePickerOpen).toBe(false);
  });

  it('manages place picker modal tabs and selecting places (UI-03)', async () => {
    expect(component.isPlacePickerOpen).toBe(false);
    component.openPlacePicker();
    expect(component.isPlacePickerOpen).toBe(true);
    expect(component.pickerTab).toBe('browse');
    expect(mockPlaceService.getFeaturedPlaces).toHaveBeenCalled();

    component.setPickerTab('custom');
    expect(component.pickerTab).toBe('custom');

    component.setPickerTab('browse');
    expect(component.pickerTab).toBe('browse');

    // Select a place from picker into current day
    const initialCount = component.currentDay?.items.length || 0;
    await component.selectPlaceFromPicker(mockPlace);

    expect(component.currentDay?.items.length).toBe(initialCount + 1);
    expect(component.isPlacePickerOpen).toBe(false);
  });

  it('allows editing scheduled stop and moving stop across days (UI-06, UI-07)', () => {
    // Add 2 days
    component.addDay();
    expect(component.days.length).toBeGreaterThanOrEqual(2);

    // Add stop to Day 1
    component.activeDayIndex = 0;
    component.selectPlaceFromPicker(mockPlace);
    const stop = component.days[0].items[0];
    expect(stop).toBeTruthy();

    // Open edit modal
    component.openEditStopModal(stop, 0);
    expect(component.isEditStopModalOpen).toBe(true);
    expect(component.editingStop).toBe(stop);

    // Edit fields
    component.editStopTime = '09:00 AM - 11:00 AM';
    component.editStopDuration = 120;
    component.editStopCostMin = 200;
    component.editStopCostMax = 500;
    component.editStopNotes = 'Pack picnic lunch';
    // Move to Day 2
    component.editStopTargetDayIndex = 1;

    component.saveStopEdits();
    expect(component.isEditStopModalOpen).toBe(false);
    expect(component.days[0].items.length).toBe(0);
    expect(component.days[1].items.length).toBe(1);
    expect(component.days[1].items[0].planned_time).toBe('09:00 AM - 11:00 AM');
    expect(component.days[1].items[0].duration_minutes).toBe(120);
    expect(component.days[1].items[0].notes).toBe('Pack picnic lunch');
  });

  it('supports planned time and pin coordinates for off-grid custom venue (UI-08)', async () => {
    component.customVenueTitle = "Nanay's Farmstead";
    component.customVenueAddress = 'Pantabangan';
    component.customPlannedTime = '02:00 PM';
    component.customVenueLat = 15.8200;
    component.customVenueLng = 121.1500;
    component.toggleCustomCoords();
    expect(component.isCustomCoordsExpanded).toBe(true);

    await component.addCustomVenueStop();
    const cur = component.currentDay;
    const addedStop = cur?.items.find((i) => i.name === "Nanay's Farmstead");
    expect(addedStop).toBeTruthy();
    expect(addedStop?.planned_time).toBe('02:00 PM');
    expect(addedStop?.custom_lat).toBe(15.8200);
    expect(addedStop?.custom_lng).toBe(121.1500);
  });

  it('guards unsaved changes on deactivation (UI-10)', async () => {
    component.hasUnsavedChanges = false;
    expect(component.canDeactivate()).toBe(true);

    component.hasUnsavedChanges = true;
    const canDeactPromise = component.canDeactivate();
    expect(canDeactPromise).toBeInstanceOf(Promise);
  });
});