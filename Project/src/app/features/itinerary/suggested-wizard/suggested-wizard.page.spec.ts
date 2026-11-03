import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { of } from 'rxjs';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ToastController } from '@ionic/angular';
import { SuggestedWizardPage } from './suggested-wizard.page';
import { ItineraryService } from '../../../core/services/itinerary.service';
import { PlaceService } from '../../../core/services/place.service';
import { Itinerary } from '../../../core/models/itinerary.models';

describe('SuggestedWizardPage', () => {
  let component: SuggestedWizardPage;
  let fixture: ComponentFixture<SuggestedWizardPage>;
  let router: Router;

  const mockGeneratedPlan: Itinerary = {
    id: 'itin-sugg-1',
    title: 'Suggested Bongabon Trip',
    destination: 'Bongabon',
    start_date: '2026-11-01',
    end_date: '2026-11-03',
    daily_budget: 3000,
    preferences: ['food', 'culture', 'resort'],
    type: 'suggested',
    assumptions: ['3 stops scheduled per day', 'Lunch stop anchored at 12:00 PM'],
    created_at: '2026-10-31T00:00:00Z',
    days: [
      {
        id: 'day-1',
        itinerary_id: 'itin-sugg-1',
        day_number: 1,
        travel_date: '2026-11-01',
        title: 'Day 1: Bongabon Gateway',
        items: [
          {
            id: 'item-1',
            day_id: 'day-1',
            place_id: 'poi-1',
            sort_order: 0,
            planned_time: '12:00 PM - 2:00 PM',
            duration_minutes: 120,
            notes: 'Morning stop',
            estimated_cost_min: 100,
            estimated_cost_max: 200,
            place: {
              id: 'poi-1',
              name: 'Rohi Paperflower Cafe',
              category: 'cafe',
              latitude: 15.632,
              longitude: 121.144,
              municipality_name: 'Bongabon',
              address_text: 'Bongabon, Nueva Ecija',
              description: 'Mountain trail',
              estimated_cost_min: 100,
              estimated_cost_max: 200,
              cost_currency: 'PHP',
              source_name: 'Curated',
              source_record_id: 'c1',
              imported_at: '2026-10-30T00:00:00Z',
              is_featured: true,
              tags: [],
              directions_url: '',
            },
          },
        ],
      },
    ],
  };

  const mockNearbyPlaces = [
    { id: 'nb-1', name: 'Boss Samgyupsal', category: 'restaurant' as const, openingHours: 'Daily, 10:00 AM to 10:00 PM', municipality: 'Bongabon' },
    { id: 'nb-2', name: 'Bongabon District Hospital', category: 'hospital' as const, openingHours: 'Mon-Sat, 7:00 AM to 5:00 PM', municipality: 'Bongabon' },
    { id: 'nb-3', name: 'J&B- Convenience Store', category: 'store' as const, openingHours: 'Daily, 24 hrs', municipality: 'Bongabon' },
  ];

  const mockPlaceService = {
    getPlaceImage: vi.fn().mockReturnValue('assets/images/placeholder.jpg'),
    formatCategoryName: vi.fn().mockReturnValue('Cafe & Dining'),
    getNearbyPlaces: vi.fn().mockReturnValue(mockNearbyPlaces),
  };

  const mockItineraryService = {
    suggestItinerary: vi.fn().mockReturnValue(of(mockGeneratedPlan)),
    createItinerary: vi.fn().mockReturnValue(of(mockGeneratedPlan)),
    calculateBudgetSummary: vi.fn().mockReturnValue({
      verifiedMin: 100,
      verifiedMax: 200,
      unverifiedCount: 0,
      displayText: '₱100 - ₱200',
    }),
  };

  beforeEach(async () => {
    vi.clearAllMocks();
    mockItineraryService.suggestItinerary.mockReturnValue(of(mockGeneratedPlan));
    mockItineraryService.createItinerary.mockReturnValue(of(mockGeneratedPlan));
    mockItineraryService.calculateBudgetSummary.mockReturnValue({
      verifiedMin: 100,
      verifiedMax: 200,
      unverifiedCount: 0,
      displayText: '₱100 - ₱200',
    });
    mockPlaceService.getNearbyPlaces.mockReturnValue(mockNearbyPlaces);

    const mockToast = { present: vi.fn().mockResolvedValue(undefined) };
    const mockToastController = { create: vi.fn().mockResolvedValue(mockToast) };

    await TestBed.configureTestingModule({
      imports: [SuggestedWizardPage],
      providers: [
        provideRouter([]),
        { provide: PlaceService, useValue: mockPlaceService },
        { provide: ItineraryService, useValue: mockItineraryService },
        { provide: ToastController, useValue: mockToastController },
      ],
    }).compileComponents();

    router = TestBed.inject(Router);
    vi.spyOn(router, 'navigate').mockResolvedValue(true);

    fixture = TestBed.createComponent(SuggestedWizardPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should initialize with default values and preferences matching Figma', () => {
    expect(component).toBeTruthy();
    expect(component.form.get('destination')?.value).toBe('Nueva Ecija');
    expect(component.form.get('daily_budget')?.value).toBe(3000);
    expect(component.isPreferenceSelected('food')).toBe(true);
    expect(component.isPreferenceSelected('culture')).toBe(true);
    expect(component.isPreferenceSelected('resort')).toBe(true);
  });

  it('should update destination when setDestination is called', () => {
    component.setDestination('Pantabangan');
    expect(component.form.get('destination')?.value).toBe('Pantabangan');
  });

  it('should update budget preset when setBudgetPreset is called', () => {
    component.setBudgetPreset(4000);
    expect(component.form.get('daily_budget')?.value).toBe(4000);
  });

  it('should toggle preferences correctly', () => {
    component.togglePreference('resort');
    expect(component.isPreferenceSelected('resort')).toBe(false);

    component.togglePreference('resort');
    expect(component.isPreferenceSelected('resort')).toBe(true);
  });

  it('should calculate computedTripDays correctly', () => {
    component.form.patchValue({
      start_date: '2026-11-01',
      end_date: '2026-11-03',
    });
    expect(component.computedTripDays).toBe(3);
  });

  it('should call suggestItinerary and populate plan on form submission', () => {
    component.generateItinerary();

    expect(mockItineraryService.suggestItinerary).toHaveBeenCalledWith(
      expect.objectContaining({
        destination: 'Nueva Ecija',
        daily_budget: 3000,
        save_immediately: false,
      })
    );
    expect(component.generatedPlan).toEqual(mockGeneratedPlan);
    expect(component.viewMode).toBe('itinerary');
  });

  it('should switch active day tab with selectDay', () => {
    component.selectDay(1);
    expect(component.activeDayIndex).toBe(1);
  });

  it('should open and close nearby places correctly', () => {
    component.openNearbyPlaces();
    expect(component.viewMode).toBe('nearby');

    component.setNearbyTab('hospitals');
    expect(component.activeNearbyTab).toBe('hospitals');
    expect(component.filteredNearbyPlaces.length).toBe(1);
    expect(component.filteredNearbyPlaces[0].name).toBe('Bongabon District Hospital');

    component.closeNearbyPlaces();
    expect(component.viewMode).toBe('itinerary');
  });

  it('should save itinerary and navigate home on acceptAndSave', async () => {
    component.generatedPlan = mockGeneratedPlan;

    await component.acceptAndSave();

    expect(mockItineraryService.createItinerary).toHaveBeenCalled();
    expect(router.navigate).toHaveBeenCalledWith(['/tabs/home']);
  });

  it('should reset plan on backToForm', () => {
    component.generatedPlan = mockGeneratedPlan;
    component.backToForm();
    expect(component.generatedPlan).toBeNull();
    expect(component.viewMode).toBe('form');
  });

  it('should correctly format place timing and duration', () => {
    expect(component.getTimingTime({ planned_time: '12:00 PM - 2:00 PM' })).toBe('12:00 PM - 2:00 PM');
    expect(component.getTimingDuration({ planned_time: '1 Night · 2 Days' })).toBe('22 hrs');
    expect(component.getTimingDuration({ duration_minutes: 180 })).toBe('3 hrs');
  });
  it('should handle date picker pop-up window workflow correctly', () => {
    expect(component.isDatePickerOpen).toBe(false);

    component.openDatePicker();
    expect(component.isDatePickerOpen).toBe(true);
    expect(component.popupStartDate).toBeTruthy();
    expect(component.popupEndDate).toBeTruthy();

    component.popupStartDate = '2026-11-10';
    component.popupEndDate = '2026-11-14';
    expect(component.tempTripSummary.isValid).toBe(true);
    expect(component.tempTripSummary.days).toBe(5);

    component.setPresetDuration(3);
    expect(component.popupEndDate).toBe('2026-11-12');

    component.applyDatePicker();
    expect(component.isDatePickerOpen).toBe(false);
    expect(component.form.get('start_date')?.value).toBe('2026-11-10');
    expect(component.form.get('end_date')?.value).toBe('2026-11-12');

    expect(component.displayDateRangeText).toContain('Nov 10');
    expect(component.hasSelectedDates).toBe(true);

    component.openDatePicker();
    expect(component.isDatePickerOpen).toBe(true);
    component.closeDatePicker();
    expect(component.isDatePickerOpen).toBe(false);
  });

  it('renders quick destination chips and updates destination on click (UI-01)', () => {
    fixture.detectChanges();
    const chips = fixture.nativeElement.querySelectorAll('.quick-dest-chip');
    expect(chips.length).toBe(component.quickDestinations.length);

    chips[1].click(); // 'Pantabangan'
    expect(component.form.get('destination')?.value).toBe('Pantabangan');
  });

  it('renders budget summary and assumptions box when plan is generated (UI-02)', () => {
    const testFixture = TestBed.createComponent(SuggestedWizardPage);
    const testComp = testFixture.componentInstance;
    testComp.generatedPlan = mockGeneratedPlan;
    testComp.viewMode = 'itinerary';
    testComp.budgetSummary = {
      verifiedMin: 100,
      verifiedMax: 200,
      unverifiedCount: 0,
      displayText: '₱100 - ₱200',
    };
    testFixture.detectChanges();

    const budgetCard = testFixture.nativeElement.querySelector('.verified-budget-card');
    expect(budgetCard).toBeTruthy();
    expect(budgetCard.textContent).toContain('Verified Estimated Costs');
    expect(budgetCard.textContent).toContain('₱100 - ₱200');

    const assumptionsBox = testFixture.nativeElement.querySelector('.assumptions-info-box');
    expect(assumptionsBox).toBeTruthy();
    expect(assumptionsBox.textContent).toContain('Trip Assumptions & Travel Notes');
    expect(assumptionsBox.textContent).toContain('3 stops scheduled per day');
  });

  it('opens and closes stop detail modal on stop card click (UI-12)', () => {
    const stop = mockGeneratedPlan.days[0].items[0];
    expect(component.isStopModalOpen).toBe(false);

    component.openStopDetail(stop);
    expect(component.isStopModalOpen).toBe(true);
    expect(component.selectedStop).toEqual(stop);

    component.closeStopDetail();
    expect(component.isStopModalOpen).toBe(false);
    expect(component.selectedStop).toBeNull();
  });

  it('resolves commute guide and travel reminder for stop (UI-13)', () => {
    const stop = mockGeneratedPlan.days[0].items[0];
    const commute = component.getCommuteInfo(stop);

    expect(commute.transitMode).toContain('UV Express');
    expect(commute.departureHub).toBe('Cabanatuan City Central Terminal');
    expect(commute.dropOffPoint).toContain('Ricky Food House');
    expect(commute.estimatedTravelTime).toBe('1 hr – 1 hr 30 mins');
    expect(commute.travelReminder).toBeTruthy();
  });

  it('adds nearby place to active day and updates budget (UI-14)', async () => {
    component.generatedPlan = JSON.parse(JSON.stringify(mockGeneratedPlan));
    component.activeDayIndex = 0;
    const initialItemCount = component.generatedPlan!.days[0].items.length;

    const nearbyItem = mockNearbyPlaces[0];
    await component.addNearbyPlaceToActiveDay(nearbyItem);

    expect(component.generatedPlan!.days[0].items.length).toBe(initialItemCount + 1);
    const addedItem = component.generatedPlan!.days[0].items[initialItemCount];
    expect(addedItem.custom_title).toBe('Boss Samgyupsal');
    expect(addedItem.place?.municipality_name).toBe('Bongabon');
  });

  it('opens nearby directions in Google Maps (UI-14)', () => {
    const windowSpy = vi.spyOn(window, 'open').mockImplementation(() => null);
    component.openNearbyInMaps(mockNearbyPlaces[0]);
    expect(windowSpy).toHaveBeenCalledWith(
      expect.stringContaining('Boss%20Samgyupsal'),
      '_blank',
      'noopener,noreferrer'
    );
  });
});