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
import { ConnectivityService } from './connectivity.service';
import { PlaceService } from './place.service';

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

  const mockConnectivityService = {
    isHostOfflineSnapshot: false,
  };

  const mockPlaceService = {
    findPlaceById: vi.fn(),
    getLoadedPlaces: vi.fn().mockReturnValue([]),
    formatCategoryName: vi.fn().mockReturnValue('Attraction'),
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

    mockConnectivityService.isHostOfflineSnapshot = false;
    mockPlaceService.findPlaceById.mockReset();
    mockPlaceService.getLoadedPlaces.mockReturnValue([]);

    TestBed.configureTestingModule({

      providers: [

        ItineraryService,

        provideHttpClient(),

        provideHttpClientTesting(),

        { provide: AuthService, useValue: mockAuthService },

        { provide: GuestStorageService, useValue: mockGuestStorageService },

        { provide: ConnectivityService, useValue: mockConnectivityService },

        { provide: PlaceService, useValue: mockPlaceService },

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

    it('should update itinerary with days composite payload via HTTP (CR-003)', () => {

      const updatePayload: ItineraryUpdatePayload = {

        title: 'Updated Trip With Days',

        days: [

          {

            day_number: 1,

            travel_date: '2026-11-01',

            title: 'Updated Day 1',

            items: [

              {

                place_id: 'place-uuid-1',

                sort_order: 1,

                duration_minutes: 120,

              },

            ],

          },

        ],

      };

      service.updateItinerary('itin-uuid-1', updatePayload).subscribe((res) => {

        expect(res.title).toBe('Updated Trip With Days');

      });

      const req = httpMock.expectOne(`${environment.apiBaseUrl}/itineraries/itin-uuid-1`);

      expect(req.request.method).toBe('PATCH');

      expect(req.request.body).toEqual(updatePayload);

      req.flush({ ...mockItinerary, title: 'Updated Trip With Days' });

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

    it('should partially update stop via HTTP (UI-06)', () => {
      const patchData = {
        notes: 'Updated personal note',
        duration_minutes: 60,
        estimated_cost_min: 250,
      };

      service.updateStop('itin-uuid-1', 'day-uuid-1', 'item-uuid-1', patchData).subscribe();

      const req = httpMock.expectOne(
        `${environment.apiBaseUrl}/itineraries/itin-uuid-1/days/day-uuid-1/items/item-uuid-1`
      );

      expect(req.request.method).toBe('PATCH');
      expect(req.request.body).toEqual(patchData);

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

    it('should generate suggested itinerary via HTTP', () => {

      const suggestReq = {

        title: 'Bongabon Tour',

        destination: 'Bongabon',

        start_date: '2026-11-01',

        end_date: '2026-11-02',

        daily_budget: 2500,

        preferences: ['nature', 'food'],

      };

      service.suggestItinerary(suggestReq).subscribe((plan) => {

        expect(plan.destination).toBe('Bongabon');

        expect(plan.type).toBe('suggested');

      });

      const req = httpMock.expectOne(`${environment.apiBaseUrl}/itineraries/suggest`);

      expect(req.request.method).toBe('POST');

      expect(req.request.body).toEqual(suggestReq);

      req.flush({ ...mockItinerary, destination: 'Bongabon', type: 'suggested' });

    });

  });

  describe('Guest / Offline Operations', () => {

    it('generates suggested itinerary offline when HTTP fails', async () => {

      const suggestReq = {

        title: 'Offline Suggested Trip',

        destination: 'Pantabangan',

        start_date: '2026-11-10',

        end_date: '2026-11-11',

        daily_budget: 2000,

        preferences: ['scenic'],

      };

      const planPromise = new Promise<Itinerary>((resolve) => {

        service.suggestItinerary(suggestReq).subscribe(resolve);

      });

      const req = httpMock.expectOne(`${environment.apiBaseUrl}/itineraries/suggest`);

      req.error(new ProgressEvent('Network error'));

      const plan = await planPromise;

      expect(plan.destination).toBe('Pantabangan');

      expect(plan.days.length).toBe(2);

      expect(plan.type).toBe('suggested');

      expect(plan.assumptions.length).toBeGreaterThanOrEqual(3);

    });

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

    it('DEF-03: generates suggested stops in strict chronological order with overnight stays at day end', async () => {

      mockAuthService.isAuthenticated.mockReturnValue(false);

      const planPromise = new Promise<Itinerary>((resolve) => {

        service

          .suggestItinerary({

            destination: 'Bongabon',

            start_date: '2026-11-10',

            end_date: '2026-11-11',

            daily_budget: 3000,

            preferences: ['food', 'resort'],

          })

          .subscribe(resolve);

      });

      // Emulate offline fallback by throwing on the HTTP request

      const req = httpMock.expectOne(`${environment.apiBaseUrl}/itineraries/suggest`);

      req.error(new ProgressEvent('error'));

      const plan = await planPromise;

      expect(plan).toBeTruthy();

      expect(plan.days.length).toBe(2);

      // Verify Day 1: Chronological order and overnight stay at the end

      const day1 = plan.days[0];

      expect(day1.items.length).toBe(4);

      expect(day1.items[0].custom_title).toBe('Rohi Paperflower Cafe');

      expect(day1.items[0].sort_order).toBe(1);

      expect(day1.items[1].custom_title).toBe('Museo de Bongabon');

      expect(day1.items[1].sort_order).toBe(2);

      expect(day1.items[2].custom_title).toBe('Thornes Samgyupsal House');

      expect(day1.items[2].sort_order).toBe(3);

      expect(day1.items[3].custom_title).toBe('La Casa Prime Cabins');

      expect(day1.items[3].sort_order).toBe(4);

      // Verify Day 2: North Corridor (San Jose & Pantabangan) strictly chronological (ROUTE-02, DEF-03)
      const day2 = plan.days[1];
      expect(day2.items.length).toBe(4);
      expect(day2.items[0].custom_title).toBe('Farm Villaronte');
      expect(day2.items[0].planned_time).toBe('09:00');
      expect(day2.items[0].sort_order).toBe(1);
      expect(day2.items[1].custom_title).toBe('George Point');
      expect(day2.items[1].planned_time).toBe('12:00');
      expect(day2.items[1].sort_order).toBe(2);
      expect(day2.items[2].custom_title).toBe('Pantabangan Dam and Lake Viewpoint');
      expect(day2.items[2].planned_time).toBe('13:00');
      expect(day2.items[2].sort_order).toBe(3);
      expect(day2.items[3].custom_title).toBe('Highland Bali Villas Resort and Spa');
      expect(day2.items[3].sort_order).toBe(4);

    });

    it('S-BUG-01: anchors place as Stop 1 of Day 1 when anchor_place_id is provided', async () => {
      mockAuthService.isAuthenticated.mockReturnValue(false);
      mockPlaceService.findPlaceById.mockReturnValue({
        id: 'dest-minalungao',
        name: 'Minalungao National Park',
        category: 'nature_park',
        latitude: 15.3012,
        longitude: 121.0543,
        municipality_name: 'General Tinio',
      });

      const planPromise = new Promise<Itinerary>((resolve) => {
        service
          .suggestItinerary({
            destination: 'General Tinio',
            start_date: '2026-11-10',
            end_date: '2026-11-11',
            daily_budget: 2500,
            preferences: ['nature'],
            anchor_place_id: 'dest-minalungao',
          })
          .subscribe(resolve);
      });

      const req = httpMock.expectOne(`${environment.apiBaseUrl}/itineraries/suggest`);
      req.error(new ProgressEvent('error'));

      const plan = await planPromise;
      expect(plan).toBeTruthy();
      expect(plan.days[0].items[0].place_id).toBe('dest-minalungao');
      expect(plan.days[0].items[0].custom_title).toBe('Minalungao National Park');
    });

    it('S-BUG-03: generates dynamic stops from matched destination without repeating places across days', async () => {
      mockAuthService.isAuthenticated.mockReturnValue(false);

      const planPromise = new Promise<Itinerary>((resolve) => {
        service
          .suggestItinerary({
            destination: 'Pantabangan',
            start_date: '2026-11-10',
            end_date: '2026-11-12',
            daily_budget: 2500,
            preferences: ['scenic', 'nature'],
          })
          .subscribe(resolve);
      });

      const req = httpMock.expectOne(`${environment.apiBaseUrl}/itineraries/suggest`);
      req.error(new ProgressEvent('error'));

      const plan = await planPromise;
      expect(plan).toBeTruthy();
      expect(plan.days.length).toBe(3);
      const day1PlaceIds = plan.days[0].items.map((i) => i.place_id);
      const day2PlaceIds = plan.days[1].items.map((i) => i.place_id);
      expect(day1PlaceIds).not.toEqual(day2PlaceIds);
    });

    it('S-BUG-04: short-circuits to offline suggested itinerary in 0ms when host is offline snapshot', async () => {
      mockConnectivityService.isHostOfflineSnapshot = true;

      const planPromise = new Promise<Itinerary>((resolve) => {
        service
          .suggestItinerary({
            destination: 'Bongabon',
            start_date: '2026-11-10',
            end_date: '2026-11-11',
            daily_budget: 2500,
            preferences: ['food'],
          })
          .subscribe(resolve);
      });

      httpMock.expectNone(`${environment.apiBaseUrl}/itineraries/suggest`);
      const plan = await planPromise;
      expect(plan).toBeTruthy();
      expect(plan.type).toBe('suggested');
    });

    it('C-BUG-06: hydrates place and custom_title on guest itinerary stops', async () => {
      mockAuthService.isAuthenticated.mockReturnValue(false);
      mockPlaceService.findPlaceById.mockReturnValue({
        id: 'place-hydrated-1',
        name: 'Camp Pangatian Memorial Shrine',
        category: 'historic_site',
        latitude: 15.4833,
        longitude: 120.9667,
        municipality_name: 'Cabanatuan City',
      });

      const rawGuest: GuestItinerary = {
        id: 'guest-itin-1',
        title: 'Guest Trip',
        destination: 'Cabanatuan City',
        start_date: '2026-11-10',
        end_date: '2026-11-11',
        daily_budget: 1500,
        preferences: [],
        type: 'custom',
        assumptions: [],
        created_at: '2026-11-06T00:00:00Z',
        updated_at: '2026-11-06T00:00:00Z',
        days: [
          {
            id: 'day-1',
            day_number: 1,
            travel_date: '2026-11-10',
            title: 'Day 1',
            items: [
              {
                id: 'item-1',
                place_id: 'place-hydrated-1',
                custom_title: undefined,
                sort_order: 1,
                place: null,
              } as any,
            ],
          },
        ],
      };

      mockGuestStorageService.getItineraries.mockResolvedValue([rawGuest]);

      const planPromise = new Promise<Itinerary>((resolve) => {
        service.getItineraryById('guest-itin-1').subscribe(resolve);
      });

      const plan = await planPromise;
      expect(plan).toBeTruthy();
      const item = plan.days[0].items[0];
      expect(item.custom_title).toBe('Camp Pangatian Memorial Shrine');
      expect(item.place).toBeTruthy();
      expect(item.place?.name).toBe('Camp Pangatian Memorial Shrine');
      expect(item.custom_lat).toBe(15.4833);
      expect(item.custom_lng).toBe(120.9667);
    });

  });

});
