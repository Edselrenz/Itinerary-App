import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter, Router, ActivatedRoute } from '@angular/router';
import { of } from 'rxjs';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { AlertController, ToastController } from '@ionic/angular';
import { ItineraryDetailPage } from './itinerary-detail.page';
import { ItineraryService } from '../../../core/services/itinerary.service';
import { PlaceService } from '../../../core/services/place.service';
import { Itinerary } from '../../../core/models/itinerary.models';

describe('ItineraryDetailPage', () => {
  let component: ItineraryDetailPage;
  let fixture: ComponentFixture<ItineraryDetailPage>;
  let router: Router;

  const mockItinerary: Itinerary = {
    id: 'itin-detail-1',
    title: 'Bongabon Gateway Tour',
    destination: 'Bongabon',
    start_date: '2026-11-01',
    end_date: '2026-11-03',
    daily_budget: 3000,
    preferences: ['Food Trip', 'Culture & History', 'Resort'],
    type: 'suggested',
    assumptions: ['Lunch stop scheduled at 12:00 PM'],
    created_at: '2026-10-31T00:00:00Z',
    days: [
      {
        id: 'day-1',
        itinerary_id: 'itin-detail-1',
        day_number: 1,
        travel_date: '2026-11-01',
        title: 'Day 1: Bongabon Welcome',
        items: [
          {
            id: 'item-1',
            day_id: 'day-1',
            place_id: 'place-1',
            sort_order: 1,
            planned_time: '12:00 PM - 2:00 PM (2 hrs)',
            duration_minutes: 120,
            estimated_cost_min: 150,
            estimated_cost_max: 300,
            place: {
              id: 'place-1',
              name: 'Rohi Paperflower Cafe',
              category: 'cafe',
              latitude: 15.632,
              longitude: 121.144,
              municipality_name: 'Bongabon',
              address_text: 'Bongabon, Nueva Ecija',
              description: 'Lovely cafe with floral ambiance',
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
      {
        id: 'day-2',
        itinerary_id: 'itin-detail-1',
        day_number: 2,
        travel_date: '2026-11-02',
        title: 'Day 2: City Exploration',
        items: [],
      },
    ],
  };

  const mockNearbyPlaces = [
    {
      id: 'r1',
      name: 'Boss Samgyupsal',
      category: 'restaurant',
      openingHours: 'Daily, 10:00 AM to 10:00 PM',
      municipality: 'Bongabon',
    },
    {
      id: 'h1',
      name: 'Bongabon District Hospital',
      category: 'hospital',
      openingHours: 'Mon-Sat, 7:00 AM to 5:00 PM',
      municipality: 'Bongabon',
    },
    {
      id: 's1',
      name: 'J&B- Convenience Store',
      category: 'store',
      openingHours: 'Daily, 24 hrs',
      municipality: 'Bongabon',
    },
  ];

  const mockItineraryService = {
    getItineraryById: vi.fn().mockReturnValue(of(mockItinerary)),
    getCachedItineraryById: vi.fn().mockReturnValue(null),
    updateItinerary: vi.fn().mockReturnValue(of({ ...mockItinerary, title: 'Updated Bongabon Tour' })),
    calculateBudgetSummary: vi.fn().mockReturnValue({
      verifiedMin: 150,
      verifiedMax: 300,
      unverifiedCount: 0,
      displayText: '₱150 - ₱300',
    }),
    deleteItinerary: vi.fn().mockReturnValue(of(undefined)),
  };

  const mockPlaceService = {
    getPlaceImage: vi.fn().mockReturnValue('assets/images/rohi_paperflower.png'),
    formatCategoryName: vi.fn().mockReturnValue('Cafe & Dining'),
    getNearbyPlaces: vi.fn().mockReturnValue(mockNearbyPlaces),
  };

  const mockAlert = { present: vi.fn().mockResolvedValue(undefined) };
  const mockAlertController = { create: vi.fn().mockResolvedValue(mockAlert) };
  const mockToast = { present: vi.fn().mockResolvedValue(undefined) };
  const mockToastController = { create: vi.fn().mockResolvedValue(mockToast) };

  beforeEach(async () => {
    vi.clearAllMocks();
    const testItinerary = JSON.parse(JSON.stringify(mockItinerary));
    mockItineraryService.getItineraryById.mockReturnValue(of(testItinerary));
    mockItineraryService.deleteItinerary.mockReturnValue(of(undefined));
    mockPlaceService.getNearbyPlaces.mockReturnValue(mockNearbyPlaces);

    await TestBed.configureTestingModule({
      imports: [ItineraryDetailPage],
      providers: [
        provideRouter([]),
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: { paramMap: { get: () => 'itin-detail-1' } },
          },
        },
        { provide: ItineraryService, useValue: mockItineraryService },
        { provide: PlaceService, useValue: mockPlaceService },
        { provide: AlertController, useValue: mockAlertController },
        { provide: ToastController, useValue: mockToastController },
      ],
    }).compileComponents();

    router = TestBed.inject(Router);
    vi.spyOn(router, 'navigate').mockResolvedValue(true);

    fixture = TestBed.createComponent(ItineraryDetailPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create and load itinerary from route parameter', () => {
    expect(component).toBeTruthy();
    expect(component.itinerary).toEqual(mockItinerary);
    expect(component.isLoading).toBe(false);
    expect(component.itineraryId).toBe('itin-detail-1');
  });

  it('should calculate days, total stops count, and date span correctly', () => {
    expect(component.computedTripDays).toBe(2);
    expect(component.totalStopsCount).toBe(1);
    expect(component.formattedDateSpan).toContain('Nov 1');
  });

  it('allows day switching and updates activeDayIndex', () => {
    component.selectDay(1);
    expect(component.activeDayIndex).toBe(1);
    expect(component.currentDay?.day_number).toBe(2);
  });

  it('formats stop title, category, image, and cost correctly', () => {
    const stop = mockItinerary.days[0].items[0];
    expect(component.getStopTitle(stop)).toBe('Rohi Paperflower Cafe');
    expect(component.getStopCategory(stop)).toBe('Cafe & Dining');
    expect(component.getStopCost(stop)).toBe('₱150 - ₱300');
  });

  it('opens and closes stop details modal', () => {
    const stop = mockItinerary.days[0].items[0];
    component.openStopDetail(stop);
    expect(component.isStopModalOpen).toBe(true);
    expect(component.selectedStop).toBe(stop);

    component.closeStopDetail();
    expect(component.isStopModalOpen).toBe(false);
    expect(component.selectedStop).toBeNull();
  });

  it('handles nearby places toggle, category filtering and back action', () => {
    component.openNearbyPlaces();
    expect(component.viewMode).toBe('nearby');

    component.setNearbyTab('hospitals');
    expect(component.activeNearbyTab).toBe('hospitals');
    expect(component.filteredNearbyPlaces.length).toBe(1);
    expect(component.filteredNearbyPlaces[0].name).toBe('Bongabon District Hospital');

    component.onBack();
    expect(component.viewMode).toBe('itinerary');
  });

  it('navigates to custom builder on onEdit', () => {
    component.onEdit();
    expect(router.navigate).toHaveBeenCalledWith(['/custom-builder', 'itin-detail-1']);
  });

  it('triggers delete confirmation alert on onDelete', async () => {
    await component.onDelete();
    expect(mockAlertController.create).toHaveBeenCalled();
    expect(mockAlert.present).toHaveBeenCalled();
  });

  it('navigates to history tab on onBack when in itinerary view', () => {
    component.onBack();
    expect(router.navigate).toHaveBeenCalledWith(['/tabs/history']);
  });

  it('renders budget summary and assumptions box when loaded (UI-02)', () => {
    fixture.detectChanges();
    const budgetCard = fixture.nativeElement.querySelector('.verified-budget-card');
    expect(budgetCard).toBeTruthy();
    expect(budgetCard.textContent).toContain('Verified Estimated Costs');

    const assumptionsBox = fixture.nativeElement.querySelector('.assumptions-info-box');
    expect(assumptionsBox).toBeTruthy();
    expect(assumptionsBox.textContent).toContain('Lunch stop scheduled at 12:00 PM');
  });

  it('correctly computes dynamic schedule, flexible budget and category subtitles (UI-09)', () => {
    // Budget formatting
    expect(component.formatDailyBudget({ daily_budget: 0 } as any)).toBe('Flexible Budget');
    expect(component.formatDailyBudget({ daily_budget: 2500 } as any)).toBe('₱ 2,500/day');

    // Timing formatting
    const stopWithPlan = { planned_time: '01:00 PM - 03:00 PM' } as any;
    expect(component.getTimingTime(stopWithPlan)).toBe('01:00 PM - 03:00 PM');

    const stopWithoutPlan = { planned_time: null, duration_minutes: 60 } as any;
    const computedTime = component.getTimingTime(stopWithoutPlan, 0);
    expect(computedTime).toBe('8:30 AM - 9:30 AM');

    // Day Subtitle
    const subtitle = component.getDaySubtitle(component.itinerary?.days[0]);
    expect(subtitle).toContain('Bongabon');
  });

  it('resolves commute guide and travel reminder for stop (UI-13)', () => {
    const stop = component.itinerary!.days[0].items[0];
    const commute = component.getCommuteInfo(stop);

    expect(commute.transitMode).toContain('UV Express');
    expect(commute.departureHub).toBe('Cabanatuan City Central Terminal');
    expect(commute.dropOffPoint).toContain('Ricky Food House');
    expect(commute.estimatedTravelTime).toBe('1 hr – 1 hr 30 mins');
    expect(commute.travelReminder).toBeTruthy();
  });

  it('adds nearby place to active day and updates budget in detail view (UI-14)', async () => {
    const initialItemCount = component.currentDay!.items.length;
    const nearbyPlace = {
      id: 'nb-test-1',
      name: 'Test Dining Spot',
      category: 'restaurant' as const,
      openingHours: '10 AM - 10 PM',
      municipality: 'Bongabon',
    };

    await component.addNearbyPlaceToActiveDay(nearbyPlace);
    expect(component.currentDay!.items.length).toBe(initialItemCount + 1);
    const added = component.currentDay!.items[initialItemCount];
    expect(added.custom_title).toBe('Test Dining Spot');
  });

  it('opens nearby directions in Google Maps (UI-14)', () => {
    const windowSpy = vi.spyOn(window, 'open').mockImplementation(() => null);
    const nearbyPlace = {
      id: 'nb-test-1',
      name: 'Test Dining Spot',
      category: 'restaurant' as const,
      openingHours: '10 AM - 10 PM',
      municipality: 'Bongabon',
    };

    component.openNearbyInMaps(nearbyPlace);
    expect(windowSpy).toHaveBeenCalledWith(
      expect.stringContaining('Test%20Dining%20Spot'),
      '_blank',
      'noopener,noreferrer'
    );
  });

  it('toggles assumptions expansion and parses category metadata', () => {
    expect(component.isAssumptionsExpanded).toBe(false);
    component.toggleAssumptions();
    expect(component.isAssumptionsExpanded).toBe(true);
    component.toggleAssumptions();
    expect(component.isAssumptionsExpanded).toBe(false);

    const parsed = component.parseAssumption('Operating Hours: Verified public records');
    expect(parsed.tag).toBe('Schedule');
    expect(parsed.title).toBe('Operating Hours');
    expect(parsed.description).toBe('Verified public records');
    expect(parsed.icon).toBe('time-outline');
  });

  it('formats SQL time strings into friendly timing windows', () => {
    const formatted = component.getTimingTime({
      id: 'item-time',
      day_id: 'day-1',
      sort_order: 1,
      planned_time: '14:00:00',
      duration_minutes: 60,
    });
    expect(formatted).toBe('2:00 PM - 3:00 PM');
  });

  describe('Share & Export Features (UI-23)', () => {
    it('manages share modal visibility state', () => {
      expect(component.isShareModalOpen).toBe(false);
      component.openShareModal();
      expect(component.isShareModalOpen).toBe(true);
      component.closeShareModal();
      expect(component.isShareModalOpen).toBe(false);
    });

    it('exports .ics calendar file and presents feedback toast', async () => {
      component.openShareModal();
      await component.exportIcs();
      expect(component.isShareModalOpen).toBe(false);
      expect(mockToastController.create).toHaveBeenCalledWith(
        expect.objectContaining({
          message: expect.stringContaining('.ics'),
        })
      );
    });

    it('copies formatted text summary to clipboard and closes modal', async () => {
      Object.assign(navigator, {
        clipboard: {
          writeText: vi.fn().mockResolvedValue(undefined),
        },
      });
      component.openShareModal();
      await component.copySummary();
      expect(component.isShareModalOpen).toBe(false);
      expect(mockToastController.create).toHaveBeenCalledWith(
        expect.objectContaining({
          message: expect.stringContaining('copied to clipboard'),
        })
      );
    });

    it('triggers native share and closes modal', async () => {
      component.openShareModal();
      await component.shareNative();
      expect(component.isShareModalOpen).toBe(false);
    });

    it('provides print formatting date string', () => {
      expect(component.printDateFormatted).toBeDefined();
      expect(typeof component.printDateFormatted).toBe('string');
      expect(component.printDateFormatted.length).toBeGreaterThan(0);
    });
  });

  describe('In-Place Edit Mode (Image 2 & 3)', () => {
    it('initializes editForm and toggles between view and edit modes', () => {
      expect(component.isEditMode).toBe(false);
      component.toggleEditMode();
      expect(component.isEditMode).toBe(true);
      expect(component.editForm.title).toBe('Bongabon Gateway Tour');
      expect(component.editForm.days.length).toBe(2);

      component.cancelEdit();
      expect(component.isEditMode).toBe(false);
    });

    it('adds and removes days in editForm', async () => {
      component.toggleEditMode();
      const initialDayCount = component.editForm.days.length;
      component.addDay();
      expect(component.editForm.days.length).toBe(initialDayCount + 1);

      await component.removeDay(component.editForm.days.length - 1);
      expect(component.editForm.days.length).toBe(initialDayCount);
    });

    it('adds, removes, and reorders activities within a day', () => {
      component.toggleEditMode();
      component.addActivity(0);
      const day1Activities = component.editForm.days[0].items;
      expect(day1Activities.length).toBe(2);

      // Reorder
      const firstActTitle = day1Activities[0].custom_title;
      component.moveActivityDown(0, 0);
      expect(day1Activities[1].custom_title).toBe(firstActTitle);

      component.moveActivityUp(0, 1);
      expect(day1Activities[0].custom_title).toBe(firstActTitle);

      // Delete activity
      component.deleteActivity(0, 1);
      expect(day1Activities.length).toBe(1);
    });

    it('moves an activity to a different day', () => {
      component.toggleEditMode();
      expect(component.editForm.days[0].items.length).toBe(1);
      expect(component.editForm.days[1].items.length).toBe(0);

      component.moveActivityToDifferentDay(0, 0, 1);
      expect(component.editForm.days[0].items.length).toBe(0);
      expect(component.editForm.days[1].items.length).toBe(1);
    });

    it('saves changes using itineraryService and exits edit mode', async () => {
      component.toggleEditMode();
      component.editForm.title = 'Updated Bongabon Tour';
      await component.saveChanges();

      expect(mockItineraryService.updateItinerary).toHaveBeenCalledWith(
        'itin-detail-1',
        expect.objectContaining({ title: 'Updated Bongabon Tour' })
      );
      expect(component.isEditMode).toBe(false);
      expect(mockToastController.create).toHaveBeenCalledWith(
        expect.objectContaining({ message: expect.stringContaining('saved successfully') })
      );
    });

    it('calculates total activity expenses and day/night label accurately', () => {
      const expenses = component.calculateTotalActivityExpenses();
      expect(expenses).toBeGreaterThanOrEqual(150);

      const label = component.getDaysNightsLabel(component.itinerary);
      expect(label).toBe('2 Days - 1 Night');
    });

    // --- Phase 25.3: Embedded Route Preview & Day Navigation ---

    it('formats meters to km and travel duration seconds', () => {
      expect(component.formatMetersToKm(undefined)).toBe('');
      expect(component.formatMetersToKm(850)).toBe('850 m');
      expect(component.formatMetersToKm(14500)).toBe('14.5 km');

      expect(component.formatTravelDurationSeconds(undefined)).toBe('');
      expect(component.formatTravelDurationSeconds(45)).toBe('1 min');
      expect(component.formatTravelDurationSeconds(1200)).toBe('20 min');
      expect(component.formatTravelDurationSeconds(4200)).toBe('1h 10m');
    });

    it('toggles route preview map expansion', () => {
      expect(component.isPreviewMapExpanded).toBe(true);
      component.togglePreviewMap();
      expect(component.isPreviewMapExpanded).toBe(false);
      component.togglePreviewMap();
      expect(component.isPreviewMapExpanded).toBe(true);
    });

    it('starts route tracking and navigates to map on startNavigationForActiveDay', () => {
      const trackingSpy = vi.spyOn(component.routeTrackingService, 'startTracking');
      component.startNavigationForActiveDay();

      expect(trackingSpy).toHaveBeenCalledWith(component.currentDay);
      expect(router.navigate).toHaveBeenCalledWith(['/tabs/map'], {
        queryParams: {
          followRoute: 'true',
          dayNumber: 1,
        },
      });
    });
  });
});
