import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ToastController } from '@ionic/angular';
import { GuestMigrationService } from './guest-migration.service';
import { AuthService } from './auth.service';
import { GuestItinerary, GuestStorageService } from './guest-storage.service';
import { ItineraryService } from './itinerary.service';
import { Itinerary } from '../models/itinerary.models';

describe('GuestMigrationService', () => {
  let service: GuestMigrationService;

  const mockGuestItinerary: GuestItinerary = {
    id: 'guest-itin-1',
    title: 'Guest Trip to Bongabon',
    destination: 'Bongabon',
    start_date: '2026-11-01',
    end_date: '2026-11-02',
    daily_budget: 3000,
    preferences: ['food'],
    type: 'custom',
    assumptions: [],
    days: [
      {
        day_number: 1,
        travel_date: '2026-11-01',
        title: 'Day 1',
        items: [],
      },
    ],
    created_at: '2026-10-31T00:00:00Z',
    updated_at: '2026-10-31T00:00:00Z',
  };

  const mockCreatedItinerary: Itinerary = {
    id: 'server-itin-1',
    title: 'Guest Trip to Bongabon',
    destination: 'Bongabon',
    start_date: '2026-11-01',
    end_date: '2026-11-02',
    daily_budget: 3000,
    preferences: ['food'],
    type: 'custom',
    assumptions: [],
    days: [],
    created_at: '2026-10-31T00:00:00Z',
  };

  const mockAuthService = {
    isAuthenticated: vi.fn().mockReturnValue(true),
  };

  const mockGuestStorage = {
    getItineraries: vi.fn().mockResolvedValue([mockGuestItinerary]),
    clearGuestData: vi.fn().mockResolvedValue(undefined),
  };

  const mockItineraryService = {
    createItinerary: vi.fn().mockReturnValue(of(mockCreatedItinerary)),
    refreshItineraries: vi.fn().mockReturnValue(of([mockCreatedItinerary])),
  };

  const mockToast = { present: vi.fn().mockResolvedValue(undefined) };
  const mockToastController = { create: vi.fn().mockResolvedValue(mockToast) };

  beforeEach(() => {
    vi.clearAllMocks();
    mockAuthService.isAuthenticated.mockReturnValue(true);
    mockGuestStorage.getItineraries.mockResolvedValue([mockGuestItinerary]);
    mockItineraryService.createItinerary.mockReturnValue(of(mockCreatedItinerary));
    mockItineraryService.refreshItineraries.mockReturnValue(of([mockCreatedItinerary]));

    TestBed.configureTestingModule({
      providers: [
        GuestMigrationService,
        { provide: AuthService, useValue: mockAuthService },
        { provide: GuestStorageService, useValue: mockGuestStorage },
        { provide: ItineraryService, useValue: mockItineraryService },
        { provide: ToastController, useValue: mockToastController },
      ],
    });

    service = TestBed.inject(GuestMigrationService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('returns count of unsynced guest itineraries', async () => {
    const count = await service.getUnsyncedCount();
    expect(count).toBe(1);
    expect(mockGuestStorage.getItineraries).toHaveBeenCalled();
  });

  it('migrates guest itineraries when authenticated and clears guest data', async () => {
    const count = await service.migrateGuestData(true);

    expect(count).toBe(1);
    expect(mockItineraryService.createItinerary).toHaveBeenCalled();
    expect(mockGuestStorage.clearGuestData).toHaveBeenCalled();
    expect(mockToastController.create).toHaveBeenCalled();
    expect(mockToast.present).toHaveBeenCalled();
  });

  it('does nothing if not authenticated', async () => {
    mockAuthService.isAuthenticated.mockReturnValue(false);

    const count = await service.migrateGuestData();
    expect(count).toBe(0);
    expect(mockItineraryService.createItinerary).not.toHaveBeenCalled();
  });

  it('does nothing if guest storage is empty', async () => {
    mockGuestStorage.getItineraries.mockResolvedValue([]);

    const count = await service.migrateGuestData();
    expect(count).toBe(0);
    expect(mockItineraryService.createItinerary).not.toHaveBeenCalled();
  });
});

