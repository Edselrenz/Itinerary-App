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
});
