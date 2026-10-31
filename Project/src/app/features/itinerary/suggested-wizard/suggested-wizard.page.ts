import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import {
  IonContent,
  IonHeader,
  IonIcon,
  IonSpinner,
  IonToolbar,
  ToastController,
} from '@ionic/angular';
import { addIcons } from 'ionicons';
import {
  arrowBack,
  arrowForwardOutline,
  calendarOutline,
  cartOutline,
  cashOutline,
  alertCircleOutline,
      checkmarkCircle,
  closeOutline,
  createOutline,
  informationCircleOutline,
  locationOutline,
  locationSharp,
  medkitOutline,
  restaurantOutline,
  searchOutline,
  sparkles,
  storefrontOutline,
  timeOutline,
} from 'ionicons/icons';
import { Itinerary, ItineraryBudgetSummary, ItineraryDay } from '../../../core/models/itinerary.models';
import { ItineraryService } from '../../../core/services/itinerary.service';
import { NearbyPlaceItem, PlaceService } from '../../../core/services/place.service';

export interface PreferenceOption {
  key: string;
  label: string;
}

@Component({
  selector: 'app-suggested-wizard',
  templateUrl: './suggested-wizard.page.html',
  styleUrls: ['./suggested-wizard.page.scss'],
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    IonContent,
    IonHeader,
    IonToolbar,
    IonIcon,
    IonSpinner,
  ],
})
export class SuggestedWizardPage implements OnInit {
  public form: FormGroup;
  public isGenerating = false;
  public isSaving = false;
  public generatedPlan: Itinerary | null = null;
  public activeDayIndex = 0;
  public budgetSummary: ItineraryBudgetSummary | null = null;

  // View state: 'form' (Screen 1) | 'itinerary' (Screen 2) | 'nearby' (Screen 3-5)
  public viewMode: 'form' | 'itinerary' | 'nearby' = 'form';
  public activeNearbyTab: 'restaurants' | 'hospitals' | 'stores' = 'restaurants';
  public nearbyPlacesList: NearbyPlaceItem[] = [];

  public quickDestinations = [
    'Bongabon',
    'Pantabangan',
    'Cabanatuan City',
    'Gapan City',
    'General Tinio',
    'Nueva Ecija',
  ];

  public budgetPresets = [1500, 2500, 4000, 6000];

  // 5 preferences matching Figma Flow 2 Screen 1
  public preferenceOptions: PreferenceOption[] = [
    { key: 'nature', label: 'Nature & Parks' },
    { key: 'food', label: 'Food Trip' },
    { key: 'culture', label: 'Culture & History' },
    { key: 'shopping', label: 'Shopping' },
    { key: 'resort', label: 'Resort' },
  ];

  public selectedPreferences: Set<string> = new Set(['food', 'culture', 'resort']);

  // Date Picker Pop-Up Window State ("From" and "To")
  public isDatePickerOpen = false;
  public popupStartDate = '';
  public popupEndDate = '';
  public minDate = new Date().toISOString().split('T')[0];

  constructor(
    private fb: FormBuilder,
    private router: Router,
    private itineraryService: ItineraryService,
    public placeService: PlaceService,
    private toastController: ToastController
  ) {
    addIcons({
      arrowBack,
      arrowForwardOutline,
      sparkles,
      searchOutline,
      locationOutline,
      locationSharp,
      calendarOutline,
      cashOutline,
      timeOutline,
      alertCircleOutline,
      checkmarkCircle,
      createOutline,
      informationCircleOutline,
      closeOutline,
      restaurantOutline,
      medkitOutline,
      cartOutline,
      storefrontOutline,
    });

    const today = new Date();
    const endDay = new Date();
    endDay.setDate(today.getDate() + 2); // 3 days, 2 nights default

    this.form = this.fb.group({
      destination: ['Nueva Ecija', [Validators.required]],
      start_date: [today.toISOString().split('T')[0], [Validators.required]],
      end_date: [endDay.toISOString().split('T')[0], [Validators.required]],
      daily_budget: [3000, [Validators.required, Validators.min(0)]],
    });
  }

  public ngOnInit(): void {
    this.nearbyPlacesList = this.placeService.getNearbyPlaces('Bongabon');
  }

  public setDestination(dest: string): void {
    this.form.patchValue({ destination: dest });
  }

  public setBudgetPreset(budget: number): void {
    this.form.patchValue({ daily_budget: budget });
  }

  public togglePreference(key: string): void {
    if (this.selectedPreferences.has(key)) {
      this.selectedPreferences.delete(key);
    } else {
      this.selectedPreferences.add(key);
    }
  }

  public isPreferenceSelected(key: string): boolean {
    return this.selectedPreferences.has(key);
  }

  // --- Travel Dates Pop-Up Controls ("From" and "To") ---

  public openDatePicker(): void {
    const currentStart = this.form.get('start_date')?.value;
    const currentEnd = this.form.get('end_date')?.value;
    this.popupStartDate = currentStart || this.minDate;
    if (currentEnd) {
      this.popupEndDate = currentEnd;
    } else {
      const end = new Date(this.popupStartDate);
      end.setDate(end.getDate() + 2);
      this.popupEndDate = end.toISOString().split('T')[0];
    }
    this.isDatePickerOpen = true;
  }

  public closeDatePicker(): void {
    this.isDatePickerOpen = false;
  }

  public onPopupDateChange(): void {
    if (this.popupStartDate && this.popupEndDate && this.popupEndDate < this.popupStartDate) {
      this.popupEndDate = this.popupStartDate;
    }
  }

    public isPresetActive(days: number): boolean {
    return this.tempTripSummary.isValid && this.tempTripSummary.days === days;
  }

  public setPresetDuration(days: number): void {
    const start = this.popupStartDate ? new Date(this.popupStartDate) : new Date();
    this.popupStartDate = start.toISOString().split('T')[0];
    const end = new Date(start);
    end.setDate(end.getDate() + Math.max(0, days - 1));
    this.popupEndDate = end.toISOString().split('T')[0];
  }

  public applyDatePicker(): void {
    if (!this.tempTripSummary.isValid) return;
    this.form.patchValue({
      start_date: this.popupStartDate,
      end_date: this.popupEndDate,
    });
    this.isDatePickerOpen = false;
  }

  public get displayDateRangeText(): string {
    const startStr = this.form.get('start_date')?.value;
    const endStr = this.form.get('end_date')?.value;
    if (!startStr || !endStr) {
      return 'Select start and end dates';
    }
    const start = new Date(startStr);
    const end = new Date(endStr);
    const startMonth = start.toLocaleDateString('en-US', { month: 'short' });
    const endMonth = end.toLocaleDateString('en-US', { month: 'short' });
    const startYear = start.getFullYear();
    const endYear = end.getFullYear();

    if (startYear !== endYear) {
      return `${startMonth} ${start.getDate()}, ${startYear} – ${endMonth} ${end.getDate()}, ${endYear}`;
    }
    if (startMonth === endMonth) {
      return `${startMonth} ${start.getDate()} – ${end.getDate()}, ${startYear}`;
    }
    return `${startMonth} ${start.getDate()} – ${endMonth} ${end.getDate()}, ${startYear}`;
  }

  public get hasSelectedDates(): boolean {
    return !!(this.form.get('start_date')?.value && this.form.get('end_date')?.value);
  }

  public get tempTripSummary(): { days: number; nights: number; isValid: boolean; label: string } {
    if (!this.popupStartDate || !this.popupEndDate) {
      return { days: 0, nights: 0, isValid: false, label: 'Select both departure (From) and return (To) dates' };
    }
    const start = new Date(this.popupStartDate);
    const end = new Date(this.popupEndDate);
    if (end < start) {
      return { days: 0, nights: 0, isValid: false, label: 'Return date must be on or after departure date' };
    }
    const diff = Math.max(0, end.getTime() - start.getTime());
    const days = Math.max(1, Math.ceil(diff / (1000 * 60 * 60 * 24)) + 1);
    const nights = Math.max(0, days - 1);
    const label = `${days} ${days === 1 ? 'Day' : 'Days'}, ${nights} ${nights === 1 ? 'Night' : 'Nights'} in Nueva Ecija`;
    return { days, nights, isValid: true, label };
  }

  public formatFriendlyDate(dateStr: string): string {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' });
  }

  public get computedTripDays(): number {
    const startStr = this.form.get('start_date')?.value;
    const endStr = this.form.get('end_date')?.value;
    if (!startStr || !endStr) return 1;

    const start = new Date(startStr);
    const end = new Date(endStr);
    const diff = Math.max(0, end.getTime() - start.getTime());
    return Math.max(1, Math.ceil(diff / (1000 * 60 * 60 * 24)) + 1);
  }

  public get formattedTripDateSubtitle(): string {
    const startStr = this.form.get('start_date')?.value;
    const endStr = this.form.get('end_date')?.value;
    if (!startStr || !endStr) {
      return 'e.g., Oct 30 – Nov 2 (4 days, 3 nights)';
    }

    const start = new Date(startStr);
    const end = new Date(endStr);
    const days = this.computedTripDays;
    const nights = Math.max(0, days - 1);

    const startMonth = start.toLocaleDateString('en-US', { month: 'short' });
    const endMonth = end.toLocaleDateString('en-US', { month: 'short' });

    let rangeStr = `${startMonth} ${start.getDate()} – ${endMonth} ${end.getDate()}`;
    if (startMonth === endMonth) {
      rangeStr = `${startMonth} ${start.getDate()} – ${end.getDate()}`;
    }

    return `${rangeStr} (${days} ${days === 1 ? 'day' : 'days'}, ${nights} ${nights === 1 ? 'night' : 'nights'})`;
  }

  public generateItinerary(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.isGenerating = true;
    const vals = this.form.value;

    const req = {
      title: `Suggested ${vals.destination} Trip`,
      destination: vals.destination,
      start_date: vals.start_date,
      end_date: vals.end_date,
      daily_budget: Number(vals.daily_budget),
      preferences: Array.from(this.selectedPreferences),
      save_immediately: false,
    };

    this.itineraryService.suggestItinerary(req).subscribe({
      next: (plan) => {
        this.isGenerating = false;
        this.generatedPlan = plan;
        this.activeDayIndex = 0;
        this.viewMode = 'itinerary';
        this.budgetSummary = this.itineraryService.calculateBudgetSummary(plan);
        this.refreshNearbyPlaces();
      },
      error: async (err) => {
        this.isGenerating = false;
        const toast = await this.toastController.create({
          message: err?.error?.detail || 'Failed to generate itinerary. Please try again.',
          duration: 3000,
          color: 'danger',
          position: 'top',
        });
        await toast.present();
      },
    });
  }

  public selectDay(index: number): void {
    this.activeDayIndex = index;
    this.refreshNearbyPlaces();
  }

  public refreshNearbyPlaces(): void {
    const curDay = this.generatedPlan?.days[this.activeDayIndex];
    const muni = this.getDayLocationName(curDay);
    this.nearbyPlacesList = this.placeService.getNearbyPlaces(muni);
  }

  public openNearbyPlaces(stop?: any): void {
    this.viewMode = 'nearby';
  }

  public closeNearbyPlaces(): void {
    this.viewMode = 'itinerary';
  }

  public setNearbyTab(tab: 'restaurants' | 'hospitals' | 'stores'): void {
    this.activeNearbyTab = tab;
  }

  public get filteredNearbyPlaces(): NearbyPlaceItem[] {
    const catMap: Record<string, string> = {
      restaurants: 'restaurant',
      hospitals: 'hospital',
      stores: 'store',
    };
    const targetCat = catMap[this.activeNearbyTab];
    return this.nearbyPlacesList.filter((p) => p.category === targetCat);
  }

  public async acceptAndSave(targetRoute: string = '/tabs/home'): Promise<void> {
    if (!this.generatedPlan) return;

    this.isSaving = true;
    const payload = {
      title: this.generatedPlan.title,
      destination: this.generatedPlan.destination,
      start_date: this.generatedPlan.start_date,
      end_date: this.generatedPlan.end_date,
      daily_budget: this.generatedPlan.daily_budget,
      preferences: this.generatedPlan.preferences,
      type: 'suggested' as const,
      assumptions: this.generatedPlan.assumptions,
      days: this.generatedPlan.days.map((d) => ({
        day_number: d.day_number,
        travel_date: d.travel_date,
        title: d.title,
        items: d.items.map((it) => ({
          place_id: it.place_id,
          custom_title: it.custom_title,
          custom_lat: it.custom_lat,
          custom_lng: it.custom_lng,
          sort_order: it.sort_order,
          planned_time: it.planned_time,
          duration_minutes: it.duration_minutes,
          notes: it.notes,
          estimated_cost_min: it.estimated_cost_min,
          estimated_cost_max: it.estimated_cost_max,
          place: it.place,
        })),
      })),
    };

    return new Promise<void>((resolve, reject) => {
      this.itineraryService.createItinerary(payload).subscribe({
        next: async (saved) => {
          this.isSaving = false;
          const toast = await this.toastController.create({
            message: `Suggested itinerary "${saved.title}" saved successfully!`,
            duration: 2500,
            color: 'success',
            position: 'top',
          });
          await toast.present();
          if (targetRoute === '/custom-builder') {
            await this.router.navigate(['/custom-builder', saved.id]);
          } else {
            await this.router.navigate([targetRoute]);
          }
          resolve();
        },
        error: async (err) => {
          this.isSaving = false;
          const toast = await this.toastController.create({
            message: err?.error?.detail || 'Failed to save itinerary.',
            duration: 3000,
            color: 'danger',
            position: 'top',
          });
          await toast.present();
          reject(err);
        },
      });
    });
  }

  public customizeInBuilder(): void {
    if (!this.generatedPlan) return;
    this.acceptAndSave('/custom-builder');
  }

  public backToForm(): void {
    this.generatedPlan = null;
    this.viewMode = 'form';
  }

  public onBack(): void {
    if (this.viewMode === 'nearby') {
      this.closeNearbyPlaces();
    } else if (this.viewMode === 'itinerary' || this.generatedPlan) {
      this.backToForm();
    } else {
      this.router.navigate(['/tabs/home']);
    }
  }

  public formatPlaceCost(item: any): string {
    if (item.estimated_cost_min != null || item.estimated_cost_max != null) {
      const min = item.estimated_cost_min ?? item.estimated_cost_max;
      const max = item.estimated_cost_max ?? item.estimated_cost_min;
      return min === max ? `₱${min}` : `₱${min} - ₱${max}`;
    }
    return 'Price not listed';
  }

  public getDayLocationName(day: ItineraryDay | undefined): string {
    if (!day || !day.items || day.items.length === 0) {
      return this.generatedPlan?.destination || 'Nueva Ecija';
    }
    const itemWithMuni = day.items.find((it) => it.place?.municipality_name);
    return itemWithMuni?.place?.municipality_name || this.generatedPlan?.destination || 'Nueva Ecija';
  }

  public getDaySubtitle(day: ItineraryDay | undefined): string {
    const muni = this.getDayLocationName(day);
    if (muni === 'Bongabon') {
      return 'Food spots, local culture, and historic sites!';
    }
    return `Food spots, local culture, and historic sites in ${muni}!`;
  }

  public getTimingTime(stop: any): string {
    if (stop.planned_time) {
      return stop.planned_time;
    }
    return '12:00 PM - 2:00 PM';
  }

  public getTimingDuration(stop: any): string {
    if (stop.planned_time && stop.planned_time.includes('Night')) {
      return '22 hrs';
    }
    if (stop.duration_minutes) {
      const hrs = Math.round(stop.duration_minutes / 60);
      return hrs >= 1 ? `${hrs} hrs` : `${stop.duration_minutes} mins`;
    }
    return '2 hrs';
  }
}
