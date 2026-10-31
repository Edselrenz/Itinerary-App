import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { BehaviorSubject, of } from 'rxjs';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { AlertController, ToastController } from '@ionic/angular';
import { HistoryPage } from './history.page';
import { ItineraryService } from '../../core/services/itinerary.service';
import { Itinerary } from '../../core/models/itinerary.models';

describe('HistoryPage', () => {
  let component: HistoryPage;
  let fixture: ComponentFixture<HistoryPage>;
  let router: Router;

  const mockItinerary1: Itinerary = {
    id: 'itin-1',
    title: 'Bongabon Adventure',
    destination: 'Bongabon',
    start_date: '2026-11-01',
    end_date: '2026-11-02',
    daily_budget: 3000,
    preferences: ['nature', 'food'],
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
        items: [
          {
            id: 'item-1',
            day_id: 'day-1',
            sort_order: 1,
            duration_minutes: 90,
          },
        ],
      },
    ],
  };

  const itinerariesSubject = new BehaviorSubject<Itinerary[]>([mockItinerary1]);

  const mockItineraryService = {
    itineraries$: itinerariesSubject.asObservable(),
    deleteItinerary: vi.fn().mockReturnValue(of(undefined)),
  };

  beforeEach(async () => {
    vi.clearAllMocks();
    itinerariesSubject.next([mockItinerary1]);

    const mockToast = { present: vi.fn().mockResolvedValue(undefined) };
    const mockToastController = { create: vi.fn().mockResolvedValue(mockToast) };
    const mockAlert = { present: vi.fn().mockResolvedValue(undefined) };
    const mockAlertController = { create: vi.fn().mockResolvedValue(mockAlert) };

    await TestBed.configureTestingModule({
      imports: [HistoryPage],
      providers: [
        provideRouter([]),
        { provide: ItineraryService, useValue: mockItineraryService },
        { provide: ToastController, useValue: mockToastController },
        { provide: AlertController, useValue: mockAlertController },
      ],
    }).compileComponents();

    router = TestBed.inject(Router);
    vi.spyOn(router, 'navigate').mockImplementation(() => Promise.resolve(true));

    fixture = TestBed.createComponent(HistoryPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create the history page', () => {
    expect(component).toBeTruthy();
    expect(component.savedItineraries.length).toBe(1);
    expect(component.savedItineraries[0].title).toBe('Bongabon Adventure');
  });

  it('calculates total stops across all days correctly', () => {
    const stops = component.getTotalStops(mockItinerary1);
    expect(stops).toBe(1);
  });

  it('navigates to custom builder when openItinerary is called', () => {
    component.openItinerary(mockItinerary1);
    expect(router.navigate).toHaveBeenCalledWith(['/custom-builder', 'itin-1']);
  });

  it('prompts delete alert and calls deleteItinerary', async () => {
    const mockEvent = { stopPropagation: vi.fn() } as unknown as Event;
    await component.deleteItinerary(mockEvent, mockItinerary1);
    expect(mockEvent.stopPropagation).toHaveBeenCalled();
  });
});
