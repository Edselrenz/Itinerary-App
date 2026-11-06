import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
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
  addCircleOutline,
  alertCircleOutline,
  arrowBack,
  arrowForwardOutline,
  bicycleOutline,
  busOutline,
  calendarOutline,
  carOutline,
  cartOutline,
  cashOutline,
  checkmarkCircle,
  chevronDownOutline,
  chevronUpOutline,
  closeOutline,
  compassOutline,
  createOutline,
  informationCircle,
  informationCircleOutline,
  locationOutline,
  locationSharp,
  mapOutline,
  medkitOutline,
  openOutline,
  restaurantOutline,
  searchOutline,
  shieldCheckmarkOutline,
  sparkles,
  star,
  starHalf,
  storefrontOutline,
  timeOutline,
  walkOutline,
} from 'ionicons/icons';
import { Itinerary, ItineraryBudgetSummary, ItineraryDay, ItineraryItem, SuggestedItineraryRequest } from '../../../core/models/itinerary.models';
import { Place } from '../../../core/models/place.models';
import { addDaysLocal, diffDaysLocal, formatDateRange, parseLocalIsoDate, toLocalIsoDate } from '../../../core/utils/date.utils';
import { haversineDistanceMeters } from '../../../core/utils/polyline.util';
import { ItineraryService } from '../../../core/services/itinerary.service';
import { NearbyPlaceItem, PlaceService } from '../../../core/services/place.service';
import { CommuteInfo, getCommuteInfoForMunicipality } from '../../../core/data/commute-guide.data';
import { PlaceDetailSheetComponent } from '../../../shared/components/place-detail-sheet/place-detail-sheet.component';
import { ItineraryRouteMapComponent } from '../../../shared/components/itinerary-route-map/itinerary-route-map.component';

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
    PlaceDetailSheetComponent,
    ItineraryRouteMapComponent,
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
  public minDate = toLocalIsoDate();

  // Wizard GIS & Quality Options (Phase 25)
  public travelMode: 'DRIVE' | 'TWO_WHEELER' | 'WALK' = 'DRIVE';
  public minRating: number = 0; // 0 = All, 4.0 = 4.0+, 4.5 = 4.5+

  public travelModeOptions = [
    { value: 'DRIVE' as const, label: 'Drive / Car', icon: 'car-outline' },
    { value: 'TWO_WHEELER' as const, label: 'Motorcycle / Tricycle', icon: 'bicycle-outline' },
    { value: 'WALK' as const, label: 'Walking / Transit', icon: 'walk-outline' },
  ];

  public minRatingOptions = [
    { value: 0, label: 'All Ratings' },
    { value: 4.0, label: '4.0+ ★' },
    { value: 4.5, label: '4.5+ ★' },
  ];

  public isStopModalOpen = false;
  public selectedStop: ItineraryItem | null = null;
  public activeStopIndex: number | null = null;
  public isAssumptionsExpanded = false;
  public anchorPlaceId?: string;

  constructor(
    private fb: FormBuilder,
    private router: Router,
    private route: ActivatedRoute,
    private itineraryService: ItineraryService,
    public placeService: PlaceService,
    private toastController: ToastController
  ) {
    addIcons({
      addCircleOutline,
      arrowBack,
      arrowForwardOutline,
      bicycleOutline,
      busOutline,
      carOutline,
      sparkles,
      star,
      starHalf,
      searchOutline,
      locationOutline,
      locationSharp,
      calendarOutline,
      cashOutline,
      timeOutline,
      alertCircleOutline,
      checkmarkCircle,
      chevronDownOutline,
      chevronUpOutline,
      compassOutline,
      createOutline,
      informationCircle,
      informationCircleOutline,
      closeOutline,
      mapOutline,
      openOutline,
      restaurantOutline,
      medkitOutline,
      cartOutline,
      shieldCheckmarkOutline,
      storefrontOutline,
      walkOutline,
    });

    const today = new Date();
    const endDay = addDaysLocal(today, 2); // 3 days, 2 nights default

    this.form = this.fb.group({
      destination: ['Nueva Ecija', [Validators.required]],
      start_date: [toLocalIsoDate(today), [Validators.required]],
      end_date: [toLocalIsoDate(endDay), [Validators.required]],
      daily_budget: [3000, [Validators.required, Validators.min(0)]],
    });
  }

  public ngOnInit(): void {
    this.nearbyPlacesList = this.placeService.getNearbyPlaces('Bongabon');

    // Pre-save draft hydration: restore unsaved wizard plan if returning from Full Map (GAP-03)
    if (!this.generatedPlan) {
      const existingDraft = this.itineraryService.getActiveDraftItinerary();
      if (existingDraft && existingDraft.days && existingDraft.days.length > 0) {
        this.generatedPlan = existingDraft;
        this.activeDayIndex = 0;
        this.viewMode = 'itinerary';
        this.budgetSummary = this.itineraryService.calculateBudgetSummary(existingDraft);
        this.refreshNearbyPlaces();
      }
    }

    this.route.queryParams.subscribe((params) => {
      if (params['destination']) {
        this.setDestination(params['destination']);
      }
      if (params['placeId']) {
        this.anchorPlaceId = params['placeId'];
        const p = this.placeService.findPlaceById(params['placeId']);
        if (p?.municipality_name && (!params['destination'] || this.form.get('destination')?.value === 'Nueva Ecija')) {
          this.setDestination(p.municipality_name);
        }
      }
    });
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
      const start = parseLocalIsoDate(this.popupStartDate);
      this.popupEndDate = toLocalIsoDate(addDaysLocal(start, 2));
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
    const start = this.popupStartDate ? parseLocalIsoDate(this.popupStartDate) : new Date();
    this.popupStartDate = toLocalIsoDate(start);
    const end = addDaysLocal(start, Math.max(0, days - 1));
    this.popupEndDate = toLocalIsoDate(end);
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
    return formatDateRange(startStr, endStr);
  }

  public get hasSelectedDates(): boolean {
    return !!(this.form.get('start_date')?.value && this.form.get('end_date')?.value);
  }

  public get tempTripSummary(): { days: number; nights: number; isValid: boolean; label: string } {
    if (!this.popupStartDate || !this.popupEndDate) {
      return { days: 0, nights: 0, isValid: false, label: 'Select both departure (From) and return (To) dates' };
    }
    const start = parseLocalIsoDate(this.popupStartDate);
    const end = parseLocalIsoDate(this.popupEndDate);
    if (end < start) {
      return { days: 0, nights: 0, isValid: false, label: 'Return date must be on or after departure date' };
    }
    const days = diffDaysLocal(this.popupStartDate, this.popupEndDate);
    const nights = Math.max(0, days - 1);
    const label = `${days} ${days === 1 ? 'Day' : 'Days'}, ${nights} ${nights === 1 ? 'Night' : 'Nights'} in Nueva Ecija`;
    return { days, nights, isValid: true, label };
  }

  public formatFriendlyDate(dateStr: string): string {
    if (!dateStr) return '';
    const d = parseLocalIsoDate(dateStr);
    return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' });
  }

  public get computedTripDays(): number {
    const startStr = this.form.get('start_date')?.value;
    const endStr = this.form.get('end_date')?.value;
    return diffDaysLocal(startStr, endStr);
  }

  public get displayPreferences(): string[] {
    if (this.generatedPlan?.preferences && this.generatedPlan.preferences.length > 0) {
      return this.generatedPlan.preferences.map((k) => {
        const found = this.preferenceOptions.find((p) => p.key === k);
        return found ? found.label : k;
      });
    }
    return ['Food Trip', 'Culture & History', 'Resort'];
  }

  public get formattedTripDateSubtitle(): string {
    const startStr = this.form.get('start_date')?.value;
    const endStr = this.form.get('end_date')?.value;
    if (!startStr || !endStr) {
      return 'e.g., Oct 30 – Nov 2 (4 days, 3 nights)';
    }

    const days = this.computedTripDays;
    const nights = Math.max(0, days - 1);
    const rangeStr = formatDateRange(startStr, endStr);

    return `${rangeStr} (${days} ${days === 1 ? 'day' : 'days'}, ${nights} ${nights === 1 ? 'night' : 'nights'})`;
  }

  public setTravelMode(mode: 'DRIVE' | 'TWO_WHEELER' | 'WALK'): void {
    this.travelMode = mode;
  }

  public setMinRating(rating: number): void {
    this.minRating = rating;
  }

  public generateItinerary(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.isGenerating = true;
    const vals = this.form.value;

    const req: SuggestedItineraryRequest = {
      title: `Suggested ${vals.destination} Trip`,
      destination: vals.destination,
      start_date: vals.start_date,
      end_date: vals.end_date,
      daily_budget: Number(vals.daily_budget),
      preferences: Array.from(this.selectedPreferences),
      save_immediately: false,
      travel_mode: this.travelMode,
      min_rating: this.minRating > 0 ? this.minRating : undefined,
      include_live_places: true,
      anchor_place_id: this.anchorPlaceId,
    };

    this.itineraryService.suggestItinerary(req).subscribe({
      next: (plan) => {
        this.isGenerating = false;
        this.generatedPlan = plan;
        this.activeDayIndex = 0;
        this.viewMode = 'itinerary';
        this.itineraryService.setActiveDraftItinerary(plan);
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

  public openStopDetail(stop: ItineraryItem): void {
    this.selectedStop = stop;
    this.isStopModalOpen = true;
  }

  public closeStopDetail(): void {
    this.isStopModalOpen = false;
    this.selectedStop = null;
  }

  public getStopImage(stop: ItineraryItem): string {
    return this.placeService.getPlaceImage(
      stop.place?.name || stop.custom_title || '',
      stop.place?.image_url
    );
  }

  public getStopCategory(stop: ItineraryItem): string {
    if (stop.place?.category) {
      return this.placeService.formatCategoryName(stop.place.category);
    }
    return 'Attraction';
  }

  public getStopCost(stop: ItineraryItem): string {
    if (stop.place?.estimated_cost_min !== null && stop.place?.estimated_cost_min !== undefined) {
      if (
        stop.place.estimated_cost_max !== null &&
        stop.place.estimated_cost_max !== undefined &&
        stop.place.estimated_cost_max > stop.place.estimated_cost_min
      ) {
        return `₱${Math.round(stop.place.estimated_cost_min)} - ₱${Math.round(stop.place.estimated_cost_max)}`;
      }
      return `₱${Math.round(stop.place.estimated_cost_min)}`;
    }
    return 'Cost not provided';
  }

  public getCommuteInfo(stop: ItineraryItem): CommuteInfo {
    return getCommuteInfoForMunicipality(
      stop.place?.municipality_name || this.generatedPlan?.destination || 'Nueva Ecija',
      stop.place?.name || stop.custom_title
    );
  }

  public openInGoogleMaps(stop: ItineraryItem): void {
    const url =
      stop.place?.directions_url ||
      `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(
        (stop.place?.name || stop.custom_title || '') + ' Nueva Ecija'
      )}`;
    window.open(url, '_blank', 'noopener,noreferrer');
  }

  public openNearbyInMaps(place: NearbyPlaceItem): void {
    const url = `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(
      place.name + ' ' + place.municipality + ' Nueva Ecija'
    )}`;
    window.open(url, '_blank', 'noopener,noreferrer');
  }

  public async addNearbyPlaceToActiveDay(place: NearbyPlaceItem): Promise<void> {
    if (!this.generatedPlan || !this.generatedPlan.days || !this.generatedPlan.days[this.activeDayIndex]) {
      return;
    }
    const currentDay = this.generatedPlan.days[this.activeDayIndex];
    if (!currentDay.items) {
      currentDay.items = [];
    }

    const newStop: ItineraryItem = {
      id: `nearby-added-${Date.now()}`,
      day_id: currentDay.id || `day-${currentDay.day_number}`,
      sort_order: currentDay.items.length + 1,
      duration_minutes: 60,
      planned_time: '12:00 PM',
      custom_title: place.name,
      place: {
        id: place.id,
        google_place_id: place.google_place_id,
        name: place.name,
        category: place.category === 'restaurant' ? 'restaurant' : place.category === 'hospital' ? 'pharmacy' : 'convenience_store',
        latitude: place.latitude ?? 15.63,
        longitude: place.longitude ?? 121.14,
        municipality_name: place.municipality,
        opening_hours: place.openingHours,
        cost_currency: 'PHP',
        is_featured: false,
        source_name: 'NearbyEssential',
        source_record_id: place.id,
        imported_at: new Date().toISOString(),
      } as Place,
    };

    currentDay.items.push(newStop);
    this.budgetSummary = this.itineraryService.calculateBudgetSummary(this.generatedPlan);

    const toast = await this.toastController.create({
      message: `Added ${place.name} to Day ${currentDay.day_number}!`,
      duration: 2000,
      color: 'dark',
      position: 'bottom',
    });
    await toast.present();
  }

  public get selectedStopPlace(): Place | null {
    if (!this.selectedStop) return null;
    if (this.selectedStop.place) {
      const p = { ...this.selectedStop.place };
      if (p.estimated_cost_min == null && this.selectedStop.estimated_cost_min != null) {
        p.estimated_cost_min = this.selectedStop.estimated_cost_min;
      }
      if (p.estimated_cost_max == null && this.selectedStop.estimated_cost_max != null) {
        p.estimated_cost_max = this.selectedStop.estimated_cost_max;
      }
      return p;
    }
    return {
      id: this.selectedStop.place_id || `stop-${this.selectedStop.id}`,
      name: this.selectedStop.custom_title || 'Stop',
      latitude: this.selectedStop.custom_lat ?? 15.58,
      longitude: this.selectedStop.custom_lng ?? 121.0,
      category: 'attraction',
      municipality_name: this.generatedPlan?.destination || 'Nueva Ecija',
      description: this.selectedStop.notes,
      estimated_cost_min: this.selectedStop.estimated_cost_min,
      estimated_cost_max: this.selectedStop.estimated_cost_max,
      is_featured: false,
      source_name: 'CustomStop',
      imported_at: new Date().toISOString(),
    } as Place;
  }

  public get selectedStopCommuteInfo(): CommuteInfo | undefined {
    if (!this.selectedStop) return undefined;
    return this.getCommuteInfo(this.selectedStop);
  }

  public formatMetersToKm(meters: number | null | undefined): string {
    if (meters == null) return '';
    if (meters < 1000) return `${Math.round(meters)} m`;
    return `${(meters / 1000).toFixed(1)} km`;
  }

  public formatTravelDurationSeconds(seconds: number | null | undefined): string {
    if (seconds == null) return '';
    const mins = Math.round(seconds / 60);
    if (mins < 60) return `${mins} min`;
    const hrs = Math.floor(mins / 60);
    const remMins = mins % 60;
    return `${hrs}h ${remMins}m`;
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
          this.itineraryService.setActiveDraftItinerary(null);
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
          this.itineraryService.setActiveDraftItinerary(null);
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
    this.itineraryService.setActiveDraftItinerary(this.generatedPlan);
    this.router.navigate(['/custom-builder'], {
      state: { draftItinerary: this.generatedPlan },
    });
  }

  public backToForm(): void {
    this.generatedPlan = null;
    this.viewMode = 'form';
    this.itineraryService.setActiveDraftItinerary(null);
  }

  public onStopMarkerSelected(idx: number): void {
    this.activeStopIndex = idx;
    if (typeof document !== 'undefined') {
      const cardEl = document.getElementById(`wizard-stop-card-${idx}`);
      if (cardEl) {
        cardEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    }
  }

  public onStopCardClicked(stop: ItineraryItem, idx: number): void {
    this.activeStopIndex = idx;
    this.openStopDetail(stop);
  }

  public getLegCommute(
    curDay: ItineraryDay,
    sIdx: number
  ): { distanceText: string; driveText: string; tricycleText: string; fareText: string } | null {
    if (sIdx <= 0 || !curDay?.items || !curDay.items[sIdx]) return null;
    const current = curDay.items[sIdx];
    const prev = curDay.items[sIdx - 1];

    let meters = current.travel_distance_meters;
    let seconds = current.travel_duration_seconds;

    if (!meters || meters <= 0) {
      const prevLat = prev.place?.latitude ?? prev.custom_lat;
      const prevLng = prev.place?.longitude ?? prev.custom_lng;
      const curLat = current.place?.latitude ?? current.custom_lat;
      const curLng = current.place?.longitude ?? current.custom_lng;
      if (prevLat != null && prevLng != null && curLat != null && curLng != null) {
        const straightMeters = haversineDistanceMeters(prevLat, prevLng, curLat, curLng);
        meters = Math.round(straightMeters * 1.28);
        seconds = Math.round((meters / 1000 / 32) * 3600);
      }
    }

    if (!meters || meters <= 0) return null;
    const km = meters / 1000;
    const driveMins = seconds ? Math.max(1, Math.round(seconds / 60)) : Math.max(3, Math.round((km / 32) * 60));
    const trikeMins = Math.max(5, Math.round((km / 22) * 60));
    const minFare = Math.max(30, Math.round(30 + km * 10));
    const maxFare = Math.max(50, Math.round(50 + km * 15));

    return {
      distanceText: `${km.toFixed(1)} km`,
      driveText: `~${driveMins} mins drive`,
      tricycleText: `${trikeMins} mins tricycle`,
      fareText: `Est. Fare ₱${minFare}–₱${maxFare}`,
    };
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

  public toggleAssumptions(): void {
    this.isAssumptionsExpanded = !this.isAssumptionsExpanded;
  }

  public parseAssumption(note: string): { tag: string; title: string; description: string; icon: string } {
    if (!note) {
      return { tag: 'Tip', title: 'Travel Note', description: '', icon: 'compass-outline' };
    }
    const match = note.match(/^([A-Za-z\s&/]{2,30}):\s+(.+)$/);
    let title = '';
    let description = '';

    if (match) {
      title = match[1].trim();
      description = match[2].trim();
    } else {
      title = '';
      description = note.trim();
    }

    const lower = (title + ' ' + description).toLowerCase();
    let icon = 'compass-outline';
    let tag = 'Advice';

    if (lower.includes('pacing') || lower.includes('speed')) {
      icon = 'walk-outline';
      tag = 'Pacing';
    } else if (lower.includes('geographic') || lower.includes('cluster') || lower.includes('route') || lower.includes('backtrack')) {
      icon = 'map-outline';
      tag = 'Routing';
    } else if (lower.includes('budget') || lower.includes('cost') || lower.includes('expense') || lower.includes('fare') || lower.includes('pricing') || lower.includes('unpriced')) {
      icon = 'cash-outline';
      tag = 'Budget';
    } else if (lower.includes('hour') || lower.includes('schedule') || lower.includes('holiday') || lower.includes('time') || lower.includes('pm') || lower.includes('am')) {
      icon = 'time-outline';
      tag = 'Schedule';
    } else if (lower.includes('stop')) {
      icon = 'walk-outline';
      tag = 'Pacing';
    }

    return { tag, title, description, icon };
  }

  public getTimingTime(stop: any): string {
    if (stop.planned_time) {
      const raw = String(stop.planned_time).trim();
      if (raw.includes('AM') || raw.includes('PM') || raw.includes('Night')) {
        return raw;
      }
      const match = raw.match(/^(\d{1,2}):(\d{2})(?::\d{2})?$/);
      if (match) {
        const h = parseInt(match[1], 10);
        const m = parseInt(match[2], 10);
        const ampm = h >= 12 ? 'PM' : 'AM';
        const h12 = h % 12 || 12;
        const mm = m < 10 ? `0${m}` : `${m}`;
        const startTime = `${h12}:${mm} ${ampm}`;

        const dur = stop.duration_minutes || 90;
        const endTotal = h * 60 + m + dur;
        const endH = Math.floor(endTotal / 60) % 24;
        const endM = endTotal % 60;
        const endAmpm = endH >= 12 ? 'PM' : 'AM';
        const endH12 = endH % 12 || 12;
        const endMm = endM < 10 ? `0${endM}` : `${endM}`;
        const endTime = `${endH12}:${endMm} ${endAmpm}`;

        return `${startTime} - ${endTime}`;
      }
      return raw;
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
