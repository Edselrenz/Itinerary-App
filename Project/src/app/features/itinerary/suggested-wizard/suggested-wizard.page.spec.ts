import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { of, throwError } from 'rxjs';
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
    end_date: '2026-11-02',
    daily_budget: 2500,
    preferences: ['nature', 'food'],
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
            planned_time: '09:00',
            duration_minutes: 90,
            notes: 'Morning stop',
            estimated_cost_min: 100,
            estimated_cost_max: 200,
            place: {
              id: 'poi-1',
              name: 'Mount Labi Peak',
              category: 'nature_park',
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

  const mockPlaceService = {
    getPlaceImage: vi.fn().mockReturnValue('assets/images/placeholder.jpg'),
    formatCategoryName: vi.fn().mockReturnValue('Nature & Adventure'),
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

  it('should initialize with default values and preferences', () => {
    expect(component).toBeTruthy();
    expect(component.form.get('destination')?.value).toBe('Nueva Ecija');
    expect(component.form.get('daily_budget')?.value).toBe(2500);
    expect(component.isPreferenceSelected('nature')).toBe(true);
    expect(component.isPreferenceSelected('food')).toBe(true);
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
    component.togglePreference('nature');
    expect(component.isPreferenceSelected('nature')).toBe(false);

    component.togglePreference('nature');
    expect(component.isPreferenceSelected('nature')).toBe(true);
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
        daily_budget: 2500,
        save_immediately: false,
      })
    );
    expect(component.generatedPlan).toEqual(mockGeneratedPlan);
    expect(component.budgetSummary).toBeTruthy();
  });

  it('should switch active day tab with selectDay', () => {
    component.selectDay(1);
    expect(component.activeDayIndex).toBe(1);
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
  });

  it('should correctly format place costs', () => {
    expect(component.formatPlaceCost({ estimated_cost_min: 150, estimated_cost_max: 300 })).toBe('₱150 - ₱300');
    expect(component.formatPlaceCost({ estimated_cost_min: 200, estimated_cost_max: 200 })).toBe('₱200');
    expect(component.formatPlaceCost({})).toBe('Price not listed');
  });
});
