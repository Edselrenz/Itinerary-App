import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { of, throwError } from 'rxjs';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { AlertController, ToastController } from '@ionic/angular';
import { CustomBuilderPage, BuilderStop } from './custom-builder.page';
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
    updateItinerary: vi.fn().mockReturnValue(
      of({
        id: 'itin-1',
        title: 'Nueva Ecija Getaway',
        destination: 'Nueva Ecija',
        start_date: '2026-11-01',
        end_date: '2026-11-02',
        daily_budget: 2500,
        days: [],
      })
    ),
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
    expect(component.selectedCategory).toBe('All');
    expect(component.activeBrowseCategories).toContain('✨ Recommended for You');

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

  it('saves itinerary successfully and redirects to /itinerary/:id', async () => {
    component.selectPlaceFromPicker(mockPlace);
    await component.saveItinerary();

    expect(mockItineraryService.createItinerary).toHaveBeenCalled();
    expect(router.navigate).toHaveBeenCalledWith(['/itinerary', 'itin-created']);
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
    expect(router.navigate).toHaveBeenCalledWith(['/itinerary', 'itin-1']);
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

  it('C-BUG-01: renders Trip Title input and sets destination & budget quick chips', () => {
    fixture.detectChanges();
    const titleInput = fixture.nativeElement.querySelector('#custom-title-input');
    expect(titleInput).toBeTruthy();

    component.setDestination('Pantabangan');
    expect(component.form.get('destination')?.value).toBe('Pantabangan');

    component.setBudgetPreset(4000);
    expect(component.form.get('daily_budget')?.value).toBe(4000);
  });

  it('C-BUG-02: maps all 16 canonical categories in catMap', () => {
    const transitPlace: Place = {
      ...mockPlace,
      id: 'poi-transit-1',
      name: 'Cabanatuan Central Terminal',
      category: 'transport_terminal',
    };
    component.allCuratedPlaces = [mockPlace, transitPlace];

    component.setBrowseCategory('Transit & Essentials');
    expect(component.displayedPlaces.length).toBe(1);
    expect(component.displayedPlaces[0].id).toBe('poi-transit-1');

    component.setBrowseCategory('All');
    expect(component.displayedPlaces.length).toBe(2);
  });

  it('C-BUG-05: reactively synchronizes days array and travel dates when date range changes', () => {
    component.form.patchValue({
      start_date: '2026-11-10',
      end_date: '2026-11-13',
    });

    component.syncDaysWithDateRange();
    expect(component.days.length).toBe(4);
    expect(component.days[0].travel_date).toBe('2026-11-10');
    expect(component.days[3].travel_date).toBe('2026-11-13');

    // Shrinking dates preserves stops by moving them to the last day
    component.days[3].items.push({
      id: 'stop-last-day',
      name: 'Stop on day 4',
      sort_order: 1,
      duration_minutes: 60,
      isCustomVenue: false,
      municipality: 'Bongabon',
      image: '',
      category: 'Food',
    });

    component.form.patchValue({
      start_date: '2026-11-10',
      end_date: '2026-11-11',
    });
    component.syncDaysWithDateRange();
    expect(component.days.length).toBe(2);
    expect(component.days[1].items.some((it) => it.id === 'stop-last-day')).toBe(true);
  });

  it('UC-C4: openPlacePicker directly supports custom venue tab', () => {
    component.openPlacePicker('custom');
    expect(component.isPlacePickerOpen).toBe(true);
    expect(component.pickerTab).toBe('custom');

    component.openPlacePicker('browse');
    expect(component.pickerTab).toBe('browse');
  });

  it('S-BUG-06: populateFromItinerary restores draft plan and auto-calculates stop times', () => {
    const draftPlan: any = {
      id: 'draft-plan-1',
      title: 'Pantabangan Adventure',
      destination: 'Pantabangan',
      start_date: '2026-11-15',
      end_date: '2026-11-16',
      daily_budget: 4000,
      preferences: ['nature', 'food'],
      days: [
        {
          id: 'day-1',
          day_number: 1,
          travel_date: '2026-11-15',
          title: 'Day 1',
          items: [
            {
              id: 'd-stop-1',
              place_id: mockPlace.id,
              place: mockPlace,
              duration_minutes: 90,
            },
            {
              id: 'd-stop-2',
              custom_title: 'Scenic Viewpoint',
              duration_minutes: 60,
            },
          ],
        },
      ],
    };

    component.populateFromItinerary(draftPlan);

    expect(component.form.get('title')?.value).toBe('Pantabangan Adventure');
    expect(component.form.get('destination')?.value).toBe('Pantabangan');
    expect(component.days.length).toBe(1);
    expect(component.days[0].items.length).toBe(2);
    expect(component.days[0].items[0].planned_time).toBe('09:00 AM');
    // Stop 2 starts at 09:00 AM + 90 min + 30 min buffer = 11:00 AM
    expect(component.days[0].items[1].planned_time).toBe('11:00 AM');
  });

  it('C-BUG-04: inspectPlace opens inspection sheet and addPlaceFromDetailSheet adds to day', () => {
    expect(component.selectedPlaceForDetail).toBeNull();

    component.inspectPlace(mockPlace);
    expect(component.selectedPlaceForDetail).toBe(mockPlace);

    component.addPlaceFromDetailSheet(mockPlace);
    expect(component.selectedPlaceForDetail).toBeNull();
    expect(component.currentDay?.items.some((it) => it.place_id === mockPlace.id)).toBe(true);

    component.closePlaceDetailSheet();
    expect(component.selectedPlaceForDetail).toBeNull();
  });

  it('autoOptimizeDaySchedule recalculates sequential times with 30-min transit buffer', () => {
    const cur = component.currentDay!;
    cur.items = [
      {
        id: 'stop-a',
        name: 'Stop A',
        category: 'Food',
        municipality: 'Bongabon',
        image: '',
        sort_order: 1,
        duration_minutes: 60,
        planned_time: '10:00 AM',
        isCustomVenue: false,
      },
      {
        id: 'stop-b',
        name: 'Stop B',
        category: 'Nature',
        municipality: 'Bongabon',
        image: '',
        sort_order: 2,
        duration_minutes: 90,
        planned_time: '10:00 AM', // Unoptimized duplicate time
        isCustomVenue: false,
      },
    ];

    component.autoOptimizeDaySchedule();

    expect(cur.items[0].planned_time).toBe('09:00 AM');
    // Stop 1 is 60m duration + 30m buffer = 90m -> 10:30 AM
    expect(cur.items[1].planned_time).toBe('10:30 AM');
    expect(component.hasUnsavedChanges).toBe(true);
  });

  it('CUST-01: provides balanced browsing by default and populates Recommended tab with user preferences (Finding 5)', () => {
    // Single preference maintains balanced All view while adding Recommended pill
    component.selectedPreferences.clear();
    component.togglePreference('culture');
    component.proceedToBuilder();
    expect(component.selectedCategory).toBe('All');
    expect(component.activeBrowseCategories).toContain('✨ Recommended for You');

    // Tapping Recommended pill filters places by culture
    component.setBrowseCategory('✨ Recommended for You');
    expect(component.selectedCategory).toBe('✨ Recommended for You');

    // Multi-preference
    component.selectedPreferences.clear();
    component.togglePreference('food');
    component.togglePreference('resort');
    component.proceedToBuilder();
    expect(component.selectedCategory).toBe('All');
    expect(component.activeBrowseCategories).toContain('✨ Recommended for You');
  });

  it('CUST-02: queries municipality-specific places across the catalog when destination is selected', () => {
    component.form.patchValue({ destination: 'Gabaldon' });
    component.loadBrowsePlaces();
    expect(mockPlaceService.searchPlaces).toHaveBeenCalledWith({
      municipality_name: 'Gabaldon',
      limit: 100,
    });
  });

  it('CUST-03: computes dynamic inter-stop transit buffer based on coordinate distance', () => {
    const stop1: BuilderStop = {
      id: 's1',
      name: 'Stop 1',
      category: 'Nature',
      municipality: 'General Tinio',
      image: '',
      sort_order: 1,
      duration_minutes: 60,
      planned_time: '09:00 AM',
      custom_lat: 15.35,
      custom_lng: 121.05,
      isCustomVenue: false,
    };
    const stop2: BuilderStop = {
      id: 's2',
      name: 'Stop 2',
      category: 'Food',
      municipality: 'General Tinio',
      image: '',
      sort_order: 2,
      duration_minutes: 60,
      planned_time: '10:00 AM',
      // Approx 15 km away
      custom_lat: 15.48,
      custom_lng: 121.05,
      isCustomVenue: false,
    };

    const nextTime = component.calculateNextStopTime([stop1], stop2);
    // Stop 1 ends at 10:00 AM, distance ~14.4 km driving is ~22 min + 10 min buffer = ~32 min transit buffer -> ~10:32 AM
    expect(nextTime).toMatch(/10:3\d AM/);
  });
});
