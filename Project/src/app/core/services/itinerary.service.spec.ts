import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { ItineraryService } from './itinerary.service';
import { AuthService } from './auth.service';
import { GuestItinerary, GuestStorageService } from './guest-storage.service';
import { environment } from '../../../environments/environment';
import {
  Itinerary,
  ItineraryCreatePayload,
  ItineraryItemCreatePayload,
  ItineraryReorderEntry,
  ItineraryUpdatePayload,
} from '../models/itinerary.models';

describe('ItineraryService', () => {
  let service: ItineraryService;
  let httpMock: HttpTestingController;

  const mockAuthService = {
    isAuthenticated: vi.fn(),
  };

  const mockGuestStorageService = {
    getItineraries: vi.fn(),
    saveItinerary: vi.fn(),
    deleteItinerary: vi.fn(),
  };

  const mockItinerary: Itinerary = {
    id: 'itin-uuid-1',
    user_id: 'user-uuid-1',
    title: 'Nueva Ecija Eco Tour',
    destination: 'Nueva Ecija',
    start_date: '2026-11-01',
    end_date: '2026-11-03',
    daily_budget: 3500,
    preferences: ['nature', 'culture'],
    type: 'custom',
    assumptions: ['Budget excludes private transport'],
    created_at: '2026-10-31T00:00:00Z',
    updated_at: '2026-10-31T00:00:00Z',
    days: [
      {
        id: 'day-uuid-1',
        itinerary_id: 'itin-uuid-1',
        day_number: 1,
        travel_date: '2026-11-01',
        title: 'Day 1: Nature Exploration',
        items: [
          {
            id: 'item-uuid-1',
            day_id: 'day-uuid-1',
            place_id: 'place-uuid-1',
            custom_title: null,
            sort_order: 1,
            duration_minutes: 120,
            estimated_cost_min: 200,
            estimated_cost_max: 500,
          },
          {
            id: 'item-uuid-2',
            day_id: 'day-uuid-1',
            place_id: 'place-uuid-2',
            custom_title: null,
            sort_order: 2,
            duration_minutes: 60,
            estimated_cost_min: null,
            estimated_cost_max: null,
          },
        ],
      },
    ],
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockAuthService.isAuthenticated.mockReturnValue(true);
    mockGuestStorageService.getItineraries.mockResolvedValue([]);
    mockGuestStorageService.saveItinerary.mockResolvedValue(undefined);
    mockGuestStorageService.deleteItinerary.mockResolvedValue(undefined);

    TestBed.configureTestingModule({
      providers: [
        ItineraryService,
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: AuthService, useValue: mockAuthService },
        { provide: GuestStorageService, useValue: mockGuestStorageService },
      ],
    });

    service = TestBed.inject(ItineraryService);
    httpMock = TestBed.inject(HttpTestingController);

    // Initial constructor call triggers refreshItineraries()
    const initReq = httpMock.expectOne(`${environment.apiBaseUrl}/itineraries`);
    expect(initReq.request.method).toBe('GET');
    initReq.flush([mockItinerary]);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created and emit initial itineraries', async () => {
    expect(service).toBeTruthy();
    const items = await new Promise<Itinerary[]>((resolve) => {
      service.itineraries$.subscribe(resolve);
    });
    expect(items.length).toBe(1);
    expect(items[0].id).toBe('itin-uuid-1');
  });

  describe('Budget Calculations', () => {
    it('calculates verified budget ranges and counts unpriced stops correctly', () => {
      const summary = service.calculateBudgetSummary(mockItinerary);
      expect(summary.verifiedMin).toBe(200);
      expect(summary.verifiedMax).toBe(500);
      expect(summary.unverifiedCount).toBe(1);
      expect(summary.displayText).toBe('₱200 - ₱500 (+ 1 unpriced)');
    });

    it('returns "No stops added" when itinerary has no items', () => {
      const emptyItin: Itinerary = {
        ...mockItinerary,
        days: [{ id: 'd1', itinerary_id: 'i1', day_number: 1, travel_date: '2026-11-01', items: [] }],
      };
      const summary = service.calculateBudgetSummary(emptyItin);
      expect(summary.displayText).toBe('No stops added');
      expect(summary.verifiedMin).toBe(0);
      expect(summary.verifiedMax).toBe(0);
    });

    it('displays single price if min equals max', () => {
      const singlePriceItin: Itinerary = {
        ...mockItinerary,
        days: [
          {
            id: 'd1',
            itinerary_id: 'i1',
            day_number: 1,
            travel_date: '2026-11-01',
            items: [
              {
                id: 'it1',
                day_id: 'd1',
                sort_order: 1,
                duration_minutes: 60,
                estimated_cost_min: 150,
                estimated_cost_max: 150,
              },
            ],
          },
        ],
      };
      const summary = service.calculateBudgetSummary(singlePriceItin);
      expect(summary.displayText).toBe('₱150');
    });
  });

  describe('Authenticated API Operations', () => {
    it('should get single itinerary by ID via HTTP', () => {
      service.getItineraryById('itin-uuid-1').subscribe((result) => {
        expect(result.id).toBe('itin-uuid-1');
        expect(result.title).toBe(mockItinerary.title);
      });

      const req = httpMock.expectOne(`${environment.apiBaseUrl}/itineraries/itin-uuid-1`);
      expect(req.request.method).toBe('GET');
      req.flush(mockItinerary);
    });

    it('should create new itinerary via HTTP and prepend to subject', () => {
      const payload: ItineraryCreatePayload = {
        title: 'New Trip',
        destination: 'Nueva Ecija',
        start_date: '2026-12-01',
        end_date: '2026-12-02',
        daily_budget: 2000,
      };

      const createdResponse: Itinerary = {
        id: 'itin-new',
        title: 'New Trip',
        destination: 'Nueva Ecija',
        start_date: '2026-12-01',
        end_date: '2026-12-02',
        daily_budget: 2000,
        preferences: [],
        type: 'custom',
        assumptions: [],
        created_at: '2026-10-31T01:00:00Z',
        days: [],
      };

      service.createItinerary(payload).subscribe((res) => {
        expect(res.id).toBe('itin-new');
      });

      const req = httpMock.expectOne(`${environment.apiBaseUrl}/itineraries`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual(payload);
      req.flush(createdResponse);
    });

    it('should update itinerary metadata via HTTP', () => {
      const updatePayload: ItineraryUpdatePayload = {
        title: 'Updated Trip Title',
      };

      service.updateItinerary('itin-uuid-1', updatePayload).subscribe((res) => {
        expect(res.title).toBe('Updated Trip Title');
      });

      const req = httpMock.expectOne(`${environment.apiBaseUrl}/itineraries/itin-uuid-1`);
      expect(req.request.method).toBe('PATCH');
      req.flush({ ...mockItinerary, title: 'Updated Trip Title' });
    });

    it('should delete itinerary via HTTP and remove from subject', () => {
      service.deleteItinerary('itin-uuid-1').subscribe();

      const req = httpMock.expectOne(`${environment.apiBaseUrl}/itineraries/itin-uuid-1`);
      expect(req.request.method).toBe('DELETE');
      req.flush(null);
    });

    it('should add stop via HTTP', () => {
      const stopPayload: ItineraryItemCreatePayload = {
        place_id: 'place-uuid-3',
        duration_minutes: 90,
      };

      service.addStop('itin-uuid-1', 'day-uuid-1', stopPayload).subscribe((res) => {
        expect(res.id).toBe('itin-uuid-1');
      });

      const req = httpMock.expectOne(
        `${environment.apiBaseUrl}/itineraries/itin-uuid-1/days/day-uuid-1/items`
      );
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual(stopPayload);
      req.flush(mockItinerary);
    });

    it('should delete stop via HTTP', () => {
      service.deleteStop('itin-uuid-1', 'day-uuid-1', 'item-uuid-1').subscribe();

      const req = httpMock.expectOne(
        `${environment.apiBaseUrl}/itineraries/itin-uuid-1/days/day-uuid-1/items/item-uuid-1`
      );
      expect(req.request.method).toBe('DELETE');
      req.flush(mockItinerary);
    });

    it('should reorder stops via HTTP', () => {
      const entries: ItineraryReorderEntry[] = [
        { id: 'item-uuid-2', day_id: 'day-uuid-1', sort_order: 1 },
        { id: 'item-uuid-1', day_id: 'day-uuid-1', sort_order: 2 },
      ];

      service.reorderStops('itin-uuid-1', entries).subscribe();

      const req = httpMock.expectOne(`${environment.apiBaseUrl}/itineraries/itin-uuid-1/reorder`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual({ items: entries });
      req.flush(mockItinerary);
    });
  });

  describe('Guest / Offline Operations', () => {
    it('creates and saves guest itinerary offline', async () => {
      mockAuthService.isAuthenticated.mockReturnValue(false);

      const payload: ItineraryCreatePayload = {
        title: 'Offline Guest Itinerary',
        destination: 'Nueva Ecija',
        start_date: '2026-11-05',
        end_date: '2026-11-06',
        daily_budget: 1500,
        days: [
          {
            day_number: 1,
            travel_date: '2026-11-05',
            items: [],
          },
        ],
      };

      const result = await new Promise<Itinerary>((resolve) => {
        service.createItinerary(payload).subscribe(resolve);
      });

      expect(result.id).toBeTruthy();
      expect(result.title).toBe('Offline Guest Itinerary');
      expect(result.days.length).toBe(1);
      expect(mockGuestStorageService.saveItinerary).toHaveBeenCalled();
    });

    it('guards against duplicate places on the same day in guest mode', async () => {
      mockAuthService.isAuthenticated.mockReturnValue(false);

      const existingGuestItin: GuestItinerary = {
        id: 'guest-itin-1',
        title: 'Guest Trip',
        destination: 'Nueva Ecija',
        start_date: '2026-11-05',
        end_date: '2026-11-06',
        daily_budget: 1000,
        preferences: [],
        type: 'custom',
        assumptions: [],
        created_at: '2026-10-31T00:00:00Z',
        updated_at: '2026-10-31T00:00:00Z',
        days: [
          {
            id: 'g-day-1',
            itinerary_id: 'guest-itin-1',
            day_number: 1,
            travel_date: '2026-11-05',
            items: [
              {
                id: 'g-item-1',
                day_id: 'g-day-1',
                place_id: 'poi-dup-1',
                sort_order: 1,
              },
            ],
          },
        ],
      };

      mockGuestStorageService.getItineraries.mockResolvedValue([existingGuestItin]);

      let caughtError: any = null;
      try {
        await new Promise((resolve, reject) => {
          service
            .addStop('guest-itin-1', 'g-day-1', {
              place_id: 'poi-dup-1',
            })
            .subscribe({ next: resolve, error: reject });
        });
      } catch (err) {
        caughtError = err;
      }

      expect(caughtError).toBeTruthy();
      expect(caughtError.message).toContain('already been added');
    });
  });
});
