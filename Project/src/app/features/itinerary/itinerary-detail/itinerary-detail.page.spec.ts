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
    mockItineraryService.getItineraryById.mockReturnValue(of(mockItinerary));
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
});
