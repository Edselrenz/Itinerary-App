import { CommonModule } from '@angular/common';
import type { OnDestroy, OnInit } from '@angular/core';
import { ApplicationRef, ChangeDetectorRef, Component, inject } from '@angular/core';
import type { FormGroup } from '@angular/forms';
import { FormBuilder, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import {
  AlertController,
  IonButton,
  IonContent,
  IonHeader,
  IonIcon,
  IonModal,
  IonSpinner,
  IonTitle,
  IonToolbar,
  ToastController,
} from '@ionic/angular';
import { addIcons } from 'ionicons';
import {
  addOutline,
  alertCircleOutline,
  arrowBack,
  arrowDownOutline,
  arrowForwardOutline,
  arrowUpOutline,
  businessOutline,
  calendarOutline,
  cashOutline,
  checkmark,
  checkmarkCircle,
  closeOutline,
  createOutline,
  locationOutline,
      locationSharp,
  saveOutline,
  searchOutline,
  sparkles,
  timeOutline,
  trashOutline, checkmarkOutline, mapOutline } from 'ionicons/icons';
import type { Observable} from 'rxjs';
import { Subject, Subscription, debounceTime, distinctUntilChanged, map, merge } from 'rxjs';

import type { ComponentCanDeactivate } from '../../../core/guards/pending-changes.guard';
import type { Itinerary, ItineraryDay, ItineraryItem } from '../../../core/models/itinerary.models';
import type { Place } from '../../../core/models/place.models';
import type { ItineraryBudgetSummary } from '../../../core/services/itinerary.service';
import { ItineraryService } from '../../../core/services/itinerary.service';
import { PlaceService } from '../../../core/services/place.service';
import { addDaysLocal, diffDaysLocal, formatDateRange, parseLocalIsoDate, toLocalIsoDate } from '../../../core/utils/date.utils';
import { haversineDistanceMeters } from '../../../core/utils/polyline.util';
import { DestinationAutocompleteComponent } from '../../../shared/components/destination-autocomplete/destination-autocomplete.component';
import { ItineraryRouteMapComponent } from '../../../shared/components/itinerary-route-map/itinerary-route-map.component';
import { PlaceDetailSheetComponent } from '../../../shared/components/place-detail-sheet/place-detail-sheet.component';

export interface BuilderStop {
  id: string;
  place_id?: string | null;
  custom_title?: string | null;
  custom_lat?: number | null;
  custom_lng?: number | null;
  sort_order: number;
  planned_time?: string | null;
  duration_minutes: number;
  notes?: string | null;
  estimated_cost_min?: number | null;
  estimated_cost_max?: number | null;
  name: string;
  category: string;
  municipality: string;
  image: string;
  isCustomVenue: boolean;
  place?: Place | null;
}

export interface BuilderDay {
  id: string;
  day_number: number;
  travel_date: string;
  title: string;
  items: BuilderStop[];
}

@Component({
  selector: 'app-custom-builder',
  templateUrl: './custom-builder.page.html',
  styleUrls: ['./custom-builder.page.scss'],
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    IonContent,
    IonHeader,
    IonToolbar,
    IonTitle,
    IonButton,
    IonIcon,
    IonModal,
    IonSpinner,
    ItineraryRouteMapComponent,
    PlaceDetailSheetComponent,
    DestinationAutocompleteComponent,
  ],
})
export class CustomBuilderPage implements OnInit, OnDestroy, ComponentCanDeactivate {
  public form: FormGroup;
  public days: BuilderDay[] = [];
  public activeDayIndex = 0;
  public itineraryId: string | null = null;
  public isEditMode = false;
  public isSaving = false;
  public hasUnsavedChanges = false;
  public preAddedPlaceName: string | null = null;

  // View Mode: 'form' ("Tell us your travel details") vs 'browse' ("Add the places you want to visit") vs 'timeline' ("Your Custom Itinerary")
  public activeView: 'form' | 'browse' | 'timeline' = 'form';

  // Preference options matching Figma
  public preferenceOptions = [
    { key: 'nature', label: 'Nature & Parks' },
    { key: 'food', label: 'Food Trip' },
    { key: 'culture', label: 'Culture & History' },
    { key: 'shopping', label: 'Shopping' },
    { key: 'resort', label: 'Resort' },
  ];
  public selectedPreferences = new Set<string>();

  // Date Picker Pop-Up Window State ("From" and "To")
  public isDatePickerOpen = false;
  public popupStartDate = '';
  public popupEndDate = '';
  public minDate = toLocalIsoDate();

  // Quick suggestions for Step 1
  public quickDestinations = [
    'Bongabon',
    'Pantabangan',
    'Cabanatuan City',
    'Gapan City',
    'General Tinio',
    'Nueva Ecija',
  ];
  public budgetPresets = [1500, 2500, 4000, 6000];

  // Category Filter Pills (16 Canonical POI categories mapped)
  public browseCategories = [
    'All',
    'Tourist Spots',
    'Food',
    'Resorts & Stays',
    'Culture & Heritage',
    'Shopping',
    'Transit & Essentials',
    'Other',
  ];

  public get activeBrowseCategories(): string[] {
    if (this.selectedPreferences.size > 0) {
      return ['All', '✨ Recommended for You', ...this.browseCategories.filter((c) => c !== 'All')];
    }
    return this.browseCategories;
  }

  public selectedCategory = 'All';
  public browseSearchTerm = '';
  public allCuratedPlaces: Place[] = [];
  public displayedPlaces: Place[] = [];
  public isBrowseLoading = false;
  public browseSearchSubject = new Subject<string>();

  // Budget summary
  public budgetSummary: ItineraryBudgetSummary = {
    verifiedMin: 0,
    verifiedMax: 0,
    unverifiedCount: 0,
    displayText: 'No stops added',
  };

  // Place Picker Modal state (for adding custom off-grid venue or modal search)
  public isPlacePickerOpen = false;
  public selectedPlaceForDetail: Place | null = null;
  public pickerSearchTerm = '';
  public pickerSearchResults: Place[] = [];
  public pickerSearching = false;
  public pickerTab: 'browse' | 'custom' = 'browse';

  // Custom venue form fields (UI-08)
  public customVenueTitle = '';
  public customVenueAddress = '';
  public customVenueCostMin: number | null = null;
  public customVenueCostMax: number | null = null;
  public customVenueDuration = 90;
  public customVenueNotes = '';
  public customPlannedTime = '';
  public customVenueLat: number | null = null;
  public customVenueLng: number | null = null;
  public isCustomCoordsExpanded = false;

  // Edit Scheduled Stop Modal state (UI-06, UI-07)
  public isEditStopModalOpen = false;
  public editingStop: BuilderStop | null = null;
  public editingStopIndex = -1;
  public editStopTargetDayIndex = 0;
  public editStopTime = '';
  public editStopDuration = 90;
  public editStopCostMin: number | null = null;
  public editStopCostMax: number | null = null;
  public editStopNotes = '';

  private subscriptions = new Subscription();

  private fb = inject(FormBuilder);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private itineraryService = inject(ItineraryService);
  public placeService = inject(PlaceService);
  private alertController = inject(AlertController);
  private toastController = inject(ToastController);
  private cdr = inject(ChangeDetectorRef);
  private appRef = inject(ApplicationRef);

  private updateUI(): void {
    try {
      this.cdr.detectChanges();
    } catch {
      this.cdr.markForCheck();
    }
    try {
      this.appRef.tick();
    } catch {
      // Best-effort full application tick
    }
  }

  constructor() {
    addIcons({arrowBack,checkmarkCircle,addOutline,calendarOutline,sparkles,closeOutline,createOutline,locationOutline,mapOutline,cashOutline,searchOutline,checkmark,arrowForwardOutline,timeOutline,trashOutline,arrowUpOutline,arrowDownOutline,businessOutline,saveOutline,checkmarkOutline,locationSharp,alertCircleOutline,});

    const today = new Date();
    const tomorrow = addDaysLocal(today, 1);
    const savedBudget = typeof localStorage !== 'undefined' ? Number(localStorage.getItem('ne_default_budget')) : 0;
    const defaultBudget = savedBudget > 0 ? savedBudget : 3000;

    this.form = this.fb.group({
      title: ['Nueva Ecija Getaway', [Validators.required, Validators.minLength(3)]],
      destination: ['Nueva Ecija', [Validators.required]],
      start_date: [toLocalIsoDate(today), [Validators.required]],
      end_date: [toLocalIsoDate(tomorrow), [Validators.required]],
      daily_budget: [defaultBudget, [Validators.required, Validators.min(0)]],
    });
  }

  public ngOnInit(): void {
    this.itineraryId = this.route.snapshot.paramMap.get('id');

    const nav = this.router.getCurrentNavigation();
    const draft =
      nav?.extras?.state?.['draftItinerary'] ||
      (typeof history !== 'undefined' && history?.state ? history.state['draftItinerary'] : null);

    if (draft) {
      this.isEditMode = false;
      this.activeView = 'timeline';
      this.populateFromItinerary(draft);
      this.hasUnsavedChanges = true;
    } else if (this.itineraryId) {
      this.isEditMode = true;
      this.activeView = 'timeline';
      this.loadItinerary(this.itineraryId);
    } else {
      this.activeView = 'form';
      this.initDefaultDays();
    }

    this.loadBrowsePlaces();

    this.subscriptions.add(
      this.browseSearchSubject
        .pipe(debounceTime(300), distinctUntilChanged())
        .subscribe((q) => {
          this.executeBrowseServerSearch(q);
        })
    );

    this.subscriptions.add(
      this.form.valueChanges.subscribe(() => {
        this.hasUnsavedChanges = true;
        this.updateBudgetSummary();
      })
    );

    this.subscriptions.add(
      merge(
        this.form.get('start_date')!.valueChanges,
        this.form.get('end_date')!.valueChanges
      )
        .pipe(distinctUntilChanged())
        .subscribe(() => {
          this.syncDaysWithDateRange();
        })
    );

    // Support destination & addPlaceId from Map and Home discovery (UI-17)
    this.subscriptions.add(
      this.route.queryParams.subscribe((params) => {
        const dest = params['destination'];
        const addPlaceId = params['addPlaceId'];
        if (dest) {
          this.form.patchValue({ destination: dest });
        }
        if (addPlaceId) {
          this.placeService.getPlaceById(addPlaceId).subscribe({
            next: (place) => {
              if (place && this.days.length > 0) {
                const targetDay = this.days[0];
                const exists = targetDay.items.some((it) => it.place_id === place.id);
                if (!exists) {
                  this.addPlaceStop(place);
                  this.activeView = 'timeline';
                  this.hasUnsavedChanges = true;
                  this.updateBudgetSummary();
                }
                const currentTitle = this.form.get('title')?.value;
                if (!currentTitle || currentTitle.trim() === '' || currentTitle === 'Nueva Ecija Getaway') {
                  const suggestedTitle = `Trip to ${place.municipality_name || place.name}`;
                  this.form.patchValue({ title: suggestedTitle });
                }
                this.preAddedPlaceName = place.name;
                this.updateUI();
              }
            },
          });
        }
      })
    );
  }

  public ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
  }

  /**
   * Prevents accidental navigation when travelers have unsaved itinerary edits (UI-10).
   */
  public canDeactivate(): boolean | Promise<boolean> {
    if (!this.hasUnsavedChanges) {
      return true;
    }
    return new Promise<boolean>((resolve) => {
      this.alertController
        .create({
          header: 'Unsaved Itinerary Changes',
          message: 'You have unsaved changes in your custom itinerary. Leaving now will discard your current edits.',
          buttons: [
            {
              text: 'Stay & Edit',
              role: 'cancel',
              handler: () => resolve(false),
            },
            {
              text: 'Discard & Leave',
              role: 'destructive',
              handler: () => resolve(true),
            },
          ],
        })
        .then((alert) => alert.present());
    });
  }

  private initDefaultDays(): void {
    const startDate = this.form.get('start_date')?.value || toLocalIsoDate();
    const endDate = this.form.get('end_date')?.value || startDate;

    const start = parseLocalIsoDate(startDate);
    const diffDays = Math.max(1, diffDaysLocal(startDate, endDate));

    this.days = [];
    for (let i = 0; i < diffDays; i++) {
      const dayDate = addDaysLocal(start, i);
      this.days.push({
        id: this.generateTempId(),
        day_number: i + 1,
        travel_date: toLocalIsoDate(dayDate),
        title: `Day ${i + 1}`,
        items: [],
      });
    }

    this.activeDayIndex = 0;
    this.updateBudgetSummary();
  }

  public setDestination(dest: string): void {
    this.form.patchValue({ destination: dest });
  }

  public onDestinationSelected(event: {
    destination: string;
    placeId?: string;
    type: 'province' | 'municipality' | 'landmark';
  }): void {
    this.setDestination(event.destination);
  }

  public setBudgetPreset(budget: number): void {
    this.form.patchValue({ daily_budget: budget });
  }

  public syncDaysWithDateRange(): void {
    const startDateStr = this.form.get('start_date')?.value;
    const endDateStr = this.form.get('end_date')?.value;
    if (!startDateStr || !endDateStr) return;

    const start = parseLocalIsoDate(startDateStr);
    const end = parseLocalIsoDate(endDateStr);
    if (end < start) return;

    const targetDayCount = Math.max(1, diffDaysLocal(startDateStr, endDateStr));
    const currentDays = [...this.days];

    // Update travel dates for existing days
    for (let i = 0; i < currentDays.length; i++) {
      const dayDate = addDaysLocal(start, i);
      currentDays[i].travel_date = toLocalIsoDate(dayDate);
      currentDays[i].day_number = i + 1;
      currentDays[i].title = currentDays[i].title || `Day ${i + 1}`;
    }

    // Append new days if targetDayCount > currentDays.length
    if (targetDayCount > currentDays.length) {
      for (let i = currentDays.length; i < targetDayCount; i++) {
        const dayDate = addDaysLocal(start, i);
        currentDays.push({
          id: this.generateTempId(),
          day_number: i + 1,
          travel_date: toLocalIsoDate(dayDate),
          title: `Day ${i + 1}`,
          items: [],
        });
      }
    } else if (targetDayCount < currentDays.length && currentDays.length > 0) {
      // If shrinking: move stops from trimmed days to the last retained day so data is preserved
      const trailingDays = currentDays.slice(targetDayCount);
      for (const remDay of trailingDays) {
        for (const item of remDay.items) {
          currentDays[targetDayCount - 1].items.push(item);
        }
      }
      currentDays.splice(targetDayCount);
    }

    this.days = currentDays;
    this.activeDayIndex = Math.min(this.activeDayIndex, Math.max(0, this.days.length - 1));
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
      const end = addDaysLocal(parseLocalIsoDate(this.popupStartDate), 1);
      this.popupEndDate = toLocalIsoDate(end);
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

  public async applyDatePicker(): Promise<void> {
    if (!this.tempTripSummary.isValid) return;
    const newDaysCount = diffDaysLocal(this.popupStartDate, this.popupEndDate);

    // Check if shortening discards days with existing items
    if (newDaysCount < this.days.length) {
      const discardedDays = this.days.slice(newDaysCount);
      const hasStops = discardedDays.some((d) => d.items.length > 0);
      if (hasStops) {
        const alert = await this.alertController.create({
          header: 'Shorten Trip Duration?',
          message: `Reducing to ${newDaysCount} ${newDaysCount === 1 ? 'day' : 'days'} will discard scheduled stops on Day ${newDaysCount + 1}${this.days.length > newDaysCount + 1 ? ' to ' + this.days.length : ''}. Are you sure you want to proceed?`,
          buttons: [
            { text: 'Cancel', role: 'cancel' },
            {
              text: 'Discard & Shorten',
              role: 'destructive',
              handler: () => {
                this.commitDatePickerChanges();
              },
            },
          ],
        });
        await alert.present();
        return;
      }
    }
    this.commitDatePickerChanges();
  }

  public commitDatePickerChanges(): void {
    this.form.patchValue({
      start_date: this.popupStartDate,
      end_date: this.popupEndDate,
    });
    this.syncDaysWithDateRange();
    this.isDatePickerOpen = false;
    this.updateUI();
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

  public proceedToBuilder(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    // Sync days array with selected dates
    const targetDays = this.computedTripDays;
    const startDateStr = this.form.get('start_date')?.value;
    this.syncDaysWithDateRange();

    if (this.days.length !== targetDays) {
      const newDays: BuilderDay[] = [];
      const baseDate = startDateStr ? parseLocalIsoDate(startDateStr) : new Date();
      for (let i = 0; i < targetDays; i++) {
        const d = addDaysLocal(baseDate, i);
        const existing = this.days[i];
        newDays.push({
          id: existing?.id || this.generateTempId(),
          day_number: i + 1,
          travel_date: toLocalIsoDate(d),
          title: existing?.title || `Day ${i + 1}`,
          items: existing?.items || [],
        });
      }
      this.days = newDays;
      this.activeDayIndex = Math.min(this.activeDayIndex, this.days.length - 1);
    }

    // Keep browse view balanced across all categories (Finding 5)
    // Selected preferences remain accessible via '✨ Recommended for You' pill
    this.selectedCategory = 'All';

    this.loadBrowsePlaces();
    this.applyBrowseFilter();

    this.activeView = 'browse';
  }

  public backToForm(): void {
    this.activeView = 'form';
    this.updateUI();
  }

  public async onHeaderBack(): Promise<void> {
    if (this.activeView === 'form') {
      await this.onCancel();
    } else if (!this.isEditMode) {
      this.activeView = 'form';
      this.updateUI();
    } else {
      await this.onCancel();
    }
  }

  public populateFromItinerary(itin: Itinerary): void {
    this.form.patchValue({
      title: itin.title || 'Nueva Ecija Getaway',
      destination: itin.destination || 'Nueva Ecija',
      start_date: itin.start_date || toLocalIsoDate(),
      end_date: itin.end_date || toLocalIsoDate(addDaysLocal(new Date(), 1)),
      daily_budget: itin.daily_budget || 3000,
    });

    if (itin.preferences && Array.isArray(itin.preferences)) {
      this.selectedPreferences = new Set(itin.preferences);
    }

    this.days = (itin.days || []).map((d, dIdx) => ({
      id: d.id || this.generateTempId(),
      day_number: d.day_number || dIdx + 1,
      travel_date: d.travel_date || '',
      title: d.title || `Day ${d.day_number || dIdx + 1}`,
      items: (d.items || []).map((item, iIdx) => {
        const itemPlace =
          item.place || (item.place_id ? this.placeService.findPlaceById(item.place_id) : null);
        const name = item.custom_title || (item as any).name || itemPlace?.name || 'Destination Stop';
        return {
          id: item.id || this.generateTempId(),
          place_id: item.place_id || itemPlace?.id || null,
          custom_title: item.custom_title || name,
          custom_lat: item.custom_lat ?? itemPlace?.latitude ?? null,
          custom_lng: item.custom_lng ?? itemPlace?.longitude ?? null,
          sort_order: item.sort_order || iIdx + 1,
          planned_time: item.planned_time || null,
          duration_minutes: item.duration_minutes || 90,
          notes: item.notes || null,
          estimated_cost_min: item.estimated_cost_min ?? itemPlace?.estimated_cost_min ?? null,
          estimated_cost_max: item.estimated_cost_max ?? itemPlace?.estimated_cost_max ?? null,
          name: name,
          category: itemPlace?.category
            ? this.placeService.formatCategoryName(itemPlace.category)
            : 'Custom Stop',
          municipality: itemPlace?.municipality_name || itin.destination || 'Nueva Ecija',
          image: this.placeService.getPlaceImage(name, itemPlace?.image_url),
          isCustomVenue: !item.place_id && !itemPlace?.id,
          place: itemPlace,
        };
      }),
    }));

    // Auto-calculate times for any stops missing planned_time
    for (const day of this.days) {
      const chainedItems: BuilderStop[] = [];
      for (const item of day.items) {
        if (!item.planned_time) {
          item.planned_time = this.calculateNextStopTime(chainedItems);
        }
        chainedItems.push(item);
      }
    }

    this.activeDayIndex = 0;
    this.updateBudgetSummary();
  }

  private loadItinerary(id: string): void {
    this.itineraryService.getItineraryById(id).subscribe({
      next: (itin) => {
        this.populateFromItinerary(itin);
        this.hasUnsavedChanges = false;
      },
      error: async () => {
        const toast = await this.toastController.create({
          message: 'Failed to load itinerary. Initializing blank planner.',
          duration: 3000,
          color: 'danger',
          position: 'top',
        });
        await toast.present();
        this.initDefaultDays();
      },
    });
  }

  public get currentDay(): BuilderDay | undefined {
    return this.days[this.activeDayIndex];
  }

  public get activeDayNumber(): number {
    return this.activeDayIndex + 1;
  }

  public selectDay(index: number): void {
    if (index >= 0 && index < this.days.length) {
      this.activeDayIndex = index;
    }
  }

  public addDay(): void {
    const lastDay = this.days[this.days.length - 1];
    let nextDateStr = toLocalIsoDate();

    if (lastDay && lastDay.travel_date) {
      const nextDate = addDaysLocal(parseLocalIsoDate(lastDay.travel_date), 1);
      nextDateStr = toLocalIsoDate(nextDate);
    }

    const newDayNum = this.days.length + 1;
    this.days.push({
      id: this.generateTempId(),
      day_number: newDayNum,
      travel_date: nextDateStr,
      title: `Day ${newDayNum}`,
      items: [],
    });

    this.activeDayIndex = this.days.length - 1;
    this.form.patchValue({ end_date: nextDateStr });
    this.hasUnsavedChanges = true;
    this.updateBudgetSummary();
  }

  public async removeDay(index: number): Promise<void> {
    if (this.days.length <= 1) {
      const toast = await this.toastController.create({
        message: 'An itinerary must contain at least one day.',
        duration: 2500,
        color: 'warning',
        position: 'top',
      });
      await toast.present();
      return;
    }

    const alert = await this.alertController.create({
      header: `Delete Day ${index + 1}?`,
      message: 'All stops scheduled for this day will be removed.',
      buttons: [
        { text: 'Cancel', role: 'cancel' },
        {
          text: 'Delete',
          role: 'destructive',
          handler: () => {
            this.days.splice(index, 1);
            this.days.forEach((d, idx) => {
              d.day_number = idx + 1;
              d.title = `Day ${idx + 1}`;
            });
            this.activeDayIndex = Math.min(this.activeDayIndex, this.days.length - 1);
            this.hasUnsavedChanges = true;
            this.updateBudgetSummary();
          },
        },
      ],
    });
    await alert.present();
  }

  // --- Stop Management ---

  public moveStopUp(itemIndex: number): void {
    const cur = this.currentDay;
    if (!cur || itemIndex <= 0) return;

    const temp = cur.items[itemIndex];
    cur.items[itemIndex] = cur.items[itemIndex - 1];
    cur.items[itemIndex - 1] = temp;

    this.reindexSortOrder(cur);
    this.autoOptimizeDaySchedule(this.activeDayIndex);
    this.hasUnsavedChanges = true;
    this.updateUI();
  }

  public moveStopDown(itemIndex: number): void {
    const cur = this.currentDay;
    if (!cur || itemIndex >= cur.items.length - 1) return;

    const temp = cur.items[itemIndex];
    cur.items[itemIndex] = cur.items[itemIndex + 1];
    cur.items[itemIndex + 1] = temp;

    this.reindexSortOrder(cur);
    this.autoOptimizeDaySchedule(this.activeDayIndex);
    this.hasUnsavedChanges = true;
    this.updateUI();
  }

  public async removeStop(itemIndex: number): Promise<void> {
    const cur = this.currentDay;
    if (!cur) return;
    const stop = cur.items[itemIndex];
    const stopName = stop?.name || 'this stop';

    const alert = await this.alertController.create({
      header: 'Remove Stop?',
      message: `Are you sure you want to remove "${stopName}" from Day ${cur.day_number}?`,
      buttons: [
        {
          text: 'Cancel',
          role: 'cancel',
        },
        {
          text: 'Remove',
          role: 'destructive',
          handler: () => {
            this.executeRemoveStop(cur, itemIndex);
          },
        },
      ],
    });
    await alert.present();
  }

  public executeRemoveStop(day: BuilderDay, itemIndex: number): void {
    day.items.splice(itemIndex, 1);
    this.reindexSortOrder(day);
    this.hasUnsavedChanges = true;
    this.updateBudgetSummary();
  }

  // --- Edit Scheduled Stop Modal Workflow (UI-06, UI-07) ---

  public openEditStopModal(stop: BuilderStop, index: number): void {
    this.editingStop = stop;
    this.editingStopIndex = index;
    this.editStopTargetDayIndex = this.activeDayIndex;
    this.editStopTime = stop.planned_time || '';
    this.editStopDuration = stop.duration_minutes || 90;
    this.editStopCostMin = stop.estimated_cost_min ?? null;
    this.editStopCostMax = stop.estimated_cost_max ?? null;
    this.editStopNotes = stop.notes || '';
    this.isEditStopModalOpen = true;
  }

  public closeEditStopModal(): void {
    this.isEditStopModalOpen = false;
    this.editingStop = null;
    this.editingStopIndex = -1;
  }

  public async saveStopEdits(): Promise<void> {
    if (!this.editingStop || this.editingStopIndex < 0) return;

    if (
      this.editStopCostMin != null &&
      this.editStopCostMax != null &&
      Number(this.editStopCostMin) > Number(this.editStopCostMax)
    ) {
      const toast = await this.toastController.create({
        message: 'Estimated minimum cost cannot be greater than maximum cost.',
        duration: 3000,
        color: 'warning',
        position: 'top',
      });
      await toast.present();
      return;
    }

    const sourceDay = this.days[this.activeDayIndex];
    const targetIdx = Number(this.editStopTargetDayIndex);
    const targetDay = this.days[targetIdx] || sourceDay;

    this.editingStop.planned_time = this.editStopTime.trim() || null;
    this.editingStop.duration_minutes = Number(this.editStopDuration) || 90;
    this.editingStop.estimated_cost_min = this.editStopCostMin != null ? Number(this.editStopCostMin) : null;
    this.editingStop.estimated_cost_max = this.editStopCostMax != null ? Number(this.editStopCostMax) : null;
    this.editingStop.notes = this.editStopNotes.trim() || null;

    // Check if moving to another day (UI-07)
    if (targetIdx !== this.activeDayIndex && sourceDay && targetDay) {
      sourceDay.items.splice(this.editingStopIndex, 1);
      this.reindexSortOrder(sourceDay);

      targetDay.items.push(this.editingStop);
      this.reindexSortOrder(targetDay);
      this.activeDayIndex = targetIdx;
    }

    this.hasUnsavedChanges = true;
    this.updateBudgetSummary();
    this.closeEditStopModal();
  }

  private reindexSortOrder(day: BuilderDay): void {
    day.items.forEach((item, idx) => {
      item.sort_order = idx + 1;
    });
  }

  // --- Figma Custom Itinerary Browse & Add Places View ---

  public get totalStopsCount(): number {
    return this.days.reduce((acc, d) => acc + d.items.length, 0);
  }

  public switchToTimeline(): void {
    this.activeView = 'timeline';
  }

  public switchToBrowse(): void {
    this.activeView = 'browse';
  }

  public dismissPreArrivalBanner(): void {
    this.preAddedPlaceName = null;
    this.updateUI();
  }

  public loadBrowsePlaces(): void {
    this.isBrowseLoading = true;
    const dest = this.form?.get('destination')?.value?.trim();
    const isSpecificMuni =
      dest &&
      dest !== 'Nueva Ecija' &&
      dest !== 'All of Nueva Ecija' &&
      !dest.startsWith('🌏');

    const searchObs: Observable<Place[]> = isSpecificMuni
      ? this.placeService
          .searchPlaces({ municipality_name: dest, limit: 100 })
          .pipe(map((res) => res?.items || []))
      : this.placeService.getFeaturedPlaces(50);

    searchObs.subscribe({
      next: (places: Place[]) => {
        this.allCuratedPlaces = places;
        this.applyBrowseFilter();
        this.isBrowseLoading = false;
        this.updateUI();
      },
      error: () => {
        this.placeService.getFeaturedPlaces(50).subscribe({
          next: (places) => {
            this.allCuratedPlaces = places;
            this.applyBrowseFilter();
            this.isBrowseLoading = false;
            this.updateUI();
          },
          error: () => {
            this.allCuratedPlaces = [];
            this.displayedPlaces = [];
            this.isBrowseLoading = false;
            this.updateUI();
          },
        });
      },
    });
  }

  public setBrowseCategory(cat: string): void {
    this.selectedCategory = cat;
    this.applyBrowseFilter();
  }

  public onBrowseSearch(event: Event): void {
    const val = (event.target as HTMLInputElement).value || '';
    this.browseSearchTerm = val;
    this.browseSearchSubject.next(val);
    this.applyBrowseFilter();
  }

  public executeBrowseServerSearch(query: string): void {
    const q = query.trim();
    if (q.length >= 2) {
      this.placeService.searchPlaces({ q, limit: 50 }).subscribe({
        next: (res) => {
          if (res && res.items) {
            const existingIds = new Set(this.allCuratedPlaces.map((p) => p.id));
            const newPlaces = res.items.filter((p) => !existingIds.has(p.id));
            this.allCuratedPlaces = [...this.allCuratedPlaces, ...newPlaces];
            this.applyBrowseFilter();
          }
        },
      });
    }
  }

  public clearBrowseSearch(): void {
    this.browseSearchTerm = '';
    this.browseSearchSubject.next('');
    this.applyBrowseFilter();
  }

  public applyBrowseFilter(): void {
    let list = [...this.allCuratedPlaces];

    if (this.browseSearchTerm.trim()) {
      const q = this.browseSearchTerm.trim().toLowerCase();
      list = list.filter(
        (p) =>
          p.name.toLowerCase().includes(q) ||
          (p.municipality_name && p.municipality_name.toLowerCase().includes(q)) ||
          (p.description && p.description.toLowerCase().includes(q))
      );
    }

    if (this.selectedCategory !== 'All') {
      if (this.selectedCategory === '✨ Recommended for You') {
        const prefMap: Record<string, string[]> = {
          food: ['restaurant', 'cafe', 'fast_food', 'bar'],
          nature: ['tourist_attraction', 'nature_park', 'attraction'],
          culture: ['church_religious', 'museum_cultural', 'place_of_worship'],
          resort: ['hotel_accommodation', 'resort_swimming', 'motel', 'guest_house'],
          shopping: ['shopping_market', 'supermarket', 'convenience_store'],
        };
        const allowed = Array.from(this.selectedPreferences).flatMap(
          (p) => prefMap[p] || []
        );
        if (allowed.length > 0) {
          list = list.filter((p) => allowed.includes(p.category));
        }
      } else {
        const catMap: Record<string, string[]> = {
          'Tourist Spots': ['tourist_attraction', 'nature_park', 'attraction'],
          Food: ['restaurant', 'cafe', 'fast_food', 'bar'],
          'Resorts & Stays': ['hotel_accommodation', 'resort_swimming', 'motel', 'guest_house'],
          'Culture & Heritage': ['church_religious', 'museum_cultural', 'place_of_worship'],
          Shopping: ['shopping_market', 'supermarket', 'convenience_store'],
          'Transit & Essentials': [
            'bus_station',
            'transport_terminal',
            'hospital_clinic',
            'pharmacy',
            'gas_station',
            'bank_atm',
          ],
          Other: [
            'hotel_accommodation',
            'resort_swimming',
            'church_religious',
            'museum_cultural',
            'bus_station',
            'transport_terminal',
            'hospital_clinic',
            'pharmacy',
            'gas_station',
            'bank_atm',
            'convenience_store',
            'supermarket',
          ],
        };
        const allowed = catMap[this.selectedCategory] || [];
        list = list.filter((p) => allowed.includes(p.category));
      }
    }

    // Prioritize places matching chosen destination from Step 1 (C-BUG-03)
    const dest = (this.form.get('destination')?.value || '').toLowerCase().trim();
    if (dest && !dest.includes('nueva ecija')) {
      list.sort((a, b) => {
        const aMatch = (a.municipality_name || '').toLowerCase().includes(dest) ? 1 : 0;
        const bMatch = (b.municipality_name || '').toLowerCase().includes(dest) ? 1 : 0;
        return bMatch - aMatch;
      });
    }

    this.displayedPlaces = list;
  }

  public isPlaceInActiveDay(placeId?: string | null): boolean {
    if (!placeId) return false;
    const cur = this.currentDay;
    if (!cur) return false;
    return cur.items.some((it) => it.place_id === placeId);
  }

  public togglePlaceInActiveDay(place: Place): void {
    const cur = this.currentDay;
    if (!cur) return;

    const existingIdx = cur.items.findIndex((it) => it.place_id === place.id);
    if (existingIdx >= 0) {
      this.removeStop(existingIdx);
    } else {
      this.addPlaceStop(place);
    }
  }

  public getDayLocation(day: BuilderDay | undefined): string {
    if (!day || !day.items || day.items.length === 0) {
      return this.form.get('destination')?.value || 'Nueva Ecija';
    }
    const itemWithMuni = day.items.find((it) => it.municipality && it.municipality !== 'Nueva Ecija');
    return itemWithMuni?.municipality || day.items[0]?.municipality || this.form.get('destination')?.value || 'Nueva Ecija';
  }

  public getAsItineraryDay(day: BuilderDay): ItineraryDay {
    return {
      id: day.id,
      itinerary_id: this.itineraryId || 'draft',
      day_number: day.day_number,
      travel_date: day.travel_date,
      title: day.title,
      items: (day.items || []).map((it, idx) => ({
        id: it.id,
        day_id: day.id,
        order: it.sort_order ?? idx,
        custom_title: it.custom_title || it.name,
        custom_lat: it.custom_lat,
        custom_lng: it.custom_lng,
        estimated_cost_min: it.estimated_cost_min,
        estimated_cost_max: it.estimated_cost_max,
        place: it.place_id
          ? ({
              id: it.place_id,
              name: it.name,
              municipality: it.municipality,
              latitude: it.custom_lat ?? 0,
              longitude: it.custom_lng ?? 0,
              category: it.category,
            } as unknown as Place)
          : null,
      } as unknown as ItineraryItem)),
    };
  }

  public formatStopTiming(stop: BuilderStop): string {
    const durHours = Math.round(stop.duration_minutes / 60);
    const durText = durHours >= 1 ? `${durHours} hrs` : `${stop.duration_minutes} mins`;
    if (stop.planned_time) {
      return `${stop.planned_time} (${durText})`;
    }
    return `(${durText})`;
  }

  // --- Place Picker & Duplicate Guard ---

  public openPlacePicker(defaultTab: 'browse' | 'custom' = 'browse'): void {
    this.isPlacePickerOpen = true;
    this.pickerSearchTerm = '';
    this.pickerTab = defaultTab;
    if (defaultTab === 'browse') {
      this.loadFeaturedPlacesForPicker();
    }
  }

  public closePlacePicker(): void {
    this.isPlacePickerOpen = false;
  }

  public setPickerTab(tab: 'browse' | 'custom'): void {
    this.pickerTab = tab;
  }

  private loadFeaturedPlacesForPicker(): void {
    this.pickerSearching = true;
    this.placeService.getFeaturedPlaces(25).subscribe({
      next: (places) => {
        this.pickerSearchResults = places;
        this.pickerSearching = false;
      },
      error: () => {
        this.pickerSearchResults = [];
        this.pickerSearching = false;
      },
    });
  }

  public onPickerSearchChange(event: Event): void {
    const query = (event.target as HTMLInputElement).value || '';
    this.pickerSearchTerm = query;

    if (!query.trim()) {
      this.loadFeaturedPlacesForPicker();
      return;
    }

    this.pickerSearching = true;
    this.placeService.searchPlaces({ q: query.trim(), limit: 20 }).subscribe({
      next: (res) => {
        this.pickerSearchResults = res.items;
        this.pickerSearching = false;
      },
      error: () => {
        this.pickerSearchResults = [];
        this.pickerSearching = false;
      },
    });
  }

  public async selectPlaceFromPicker(place: Place): Promise<void> {
    const cur = this.currentDay;
    if (!cur) return;

    // Check duplicate stop guard for current day
    const isDuplicate = cur.items.some((it) => it.place_id === place.id);
    if (isDuplicate) {
      const alert = await this.alertController.create({
        header: 'Duplicate Destination',
        message: `"${place.name}" is already scheduled for Day ${cur.day_number}. Would you still like to add another stop here?`,
        buttons: [
          { text: 'Cancel', role: 'cancel' },
          {
            text: 'Add Anyway',
            handler: () => {
              this.addPlaceStop(place);
              this.closePlacePicker();
            },
          },
        ],
      });
      await alert.present();
      return;
    }

    this.addPlaceStop(place);
    this.closePlacePicker();
  }

  public calculateNextStopTime(items: BuilderStop[], nextStop?: BuilderStop): string {
    if (!items || items.length === 0) {
      return '09:00 AM';
    }
    const lastItem = items[items.length - 1];
    if (!lastItem.planned_time) {
      return '09:00 AM';
    }
    const match = lastItem.planned_time.match(/(\d{1,2}):(\d{2})\s*(AM|PM)?/i);
    if (!match) {
      return '09:00 AM';
    }
    let hours = parseInt(match[1], 10);
    const minutes = parseInt(match[2], 10);
    const meridiem = match[3]?.toUpperCase();

    if (meridiem === 'PM' && hours < 12) hours += 12;
    if (meridiem === 'AM' && hours === 12) hours = 0;

    const duration = lastItem.duration_minutes || 90;

    // Dynamic inter-stop transit calculation (CUST-03)
    let transitBuffer = 30; // default 30 min buffer
    if (
      lastItem.custom_lat &&
      lastItem.custom_lng &&
      nextStop?.custom_lat &&
      nextStop?.custom_lng
    ) {
      const distMeters = haversineDistanceMeters(
        lastItem.custom_lat,
        lastItem.custom_lng,
        nextStop.custom_lat,
        nextStop.custom_lng
      );
      // Assume average driving speed of 40 km/h (11.1 m/s) with 10 min parking/staging buffer
      const drivingMinutes = Math.round((distMeters / 1000 / 40) * 60);
      transitBuffer = Math.max(15, Math.min(120, drivingMinutes + 10));
    }

    const totalMinutes = hours * 60 + minutes + duration + transitBuffer;

    const newHours24 = Math.floor(totalMinutes / 60) % 24;
    const newMinutes = totalMinutes % 60;
    const newMeridiem = newHours24 >= 12 ? 'PM' : 'AM';
    let newHours12 = newHours24 % 12;
    if (newHours12 === 0) newHours12 = 12;

    const padM = newMinutes < 10 ? `0${newMinutes}` : `${newMinutes}`;
    const padH = newHours12 < 10 ? `0${newHours12}` : `${newHours12}`;
    return `${padH}:${padM} ${newMeridiem}`;
  }

  public autoOptimizeDaySchedule(dayIndex = this.activeDayIndex): void {
    const day = this.days[dayIndex];
    if (!day || !day.items || day.items.length === 0) return;

    const chainedItems: BuilderStop[] = [];
    for (let i = 0; i < day.items.length; i++) {
      const item = day.items[i];
      item.planned_time = this.calculateNextStopTime(chainedItems, item);
      item.sort_order = i + 1;
      chainedItems.push(item);
    }
    this.hasUnsavedChanges = true;
  }

  public inspectPlace(place: Place): void {
    this.selectedPlaceForDetail = place;
  }

  public closePlaceDetailSheet(): void {
    this.selectedPlaceForDetail = null;
  }

  public addPlaceFromDetailSheet(place: Place): void {
    if (!this.isPlaceInActiveDay(place.id)) {
      this.addPlaceStop(place);
    }
    this.selectedPlaceForDetail = null;
  }

  private addPlaceStop(place: Place): void {
    const cur = this.currentDay;
    if (!cur) return;

    const plannedTime = this.calculateNextStopTime(cur.items, {
      custom_lat: place.latitude,
      custom_lng: place.longitude,
    } as BuilderStop);
    const stop: BuilderStop = {
      id: this.generateTempId(),
      place_id: place.id,
      custom_title: place.name,
      custom_lat: place.latitude,
      custom_lng: place.longitude,
      name: place.name,
      category: this.placeService.formatCategoryName(place.category),
      municipality: place.municipality_name || 'Nueva Ecija',
      image: this.placeService.getPlaceImage(place.name, place.image_url),
      sort_order: cur.items.length + 1,
      planned_time: plannedTime,
      duration_minutes: 90,
      estimated_cost_min: place.estimated_cost_min,
      estimated_cost_max: place.estimated_cost_max,
      isCustomVenue: false,
      place: place,
    };

    cur.items.push(stop);
    this.hasUnsavedChanges = true;
    this.updateBudgetSummary();
  }

  public toggleCustomCoords(): void {
    this.isCustomCoordsExpanded = !this.isCustomCoordsExpanded;
  }

  public async addCustomVenueStop(): Promise<void> {
    const cur = this.currentDay;
    if (!cur) return;

    const trimmedTitle = this.customVenueTitle.trim();
    if (!trimmedTitle) return;

    // Validate coordinates if entered (UI-08 & Phase 45)
    const hasLat = this.customVenueLat != null && String(this.customVenueLat).trim() !== '';
    const hasLng = this.customVenueLng != null && String(this.customVenueLng).trim() !== '';
    if ((hasLat && !hasLng) || (!hasLat && hasLng)) {
      const toast = await this.toastController.create({
        message: 'Please provide both Latitude and Longitude coordinates, or leave both blank.',
        duration: 3000,
        color: 'warning',
        position: 'top',
      });
      await toast.present();
      return;
    }

    if (hasLat && hasLng) {
      const lat = Number(this.customVenueLat);
      const lng = Number(this.customVenueLng);
      const isWithinNuevaEcija = lat >= 15.15 && lat <= 16.15 && lng >= 120.70 && lng <= 121.40;
      if (!isWithinNuevaEcija) {
        const toast = await this.toastController.create({
          message: 'Coordinates fall outside Nueva Ecija (Lat 15.15–16.15, Lng 120.70–121.40). Please check your coordinates.',
          duration: 3500,
          color: 'warning',
          position: 'top',
        });
        await toast.present();
        return;
      }
    }

    // Validate cost bounds
    if (
      this.customVenueCostMin != null &&
      this.customVenueCostMax != null &&
      Number(this.customVenueCostMin) > Number(this.customVenueCostMax)
    ) {
      const toast = await this.toastController.create({
        message: 'Custom venue minimum cost cannot exceed maximum cost.',
        duration: 3000,
        color: 'warning',
        position: 'top',
      });
      await toast.present();
      return;
    }

    const stop: BuilderStop = {
      id: this.generateTempId(),
      place_id: null,
      custom_title: trimmedTitle,
      name: trimmedTitle,
      category: 'Custom Venue',
      municipality: this.customVenueAddress.trim() || 'Nueva Ecija',
      image: 'assets/images/casa_batik.png',
      sort_order: cur.items.length + 1,
      planned_time: this.customPlannedTime.trim() || this.calculateNextStopTime(cur.items),
      custom_lat: this.customVenueLat != null ? Number(this.customVenueLat) : null,
      custom_lng: this.customVenueLng != null ? Number(this.customVenueLng) : null,
      duration_minutes: Number(this.customVenueDuration) || 90,
      notes: this.customVenueNotes.trim() || null,
      estimated_cost_min: this.customVenueCostMin != null ? Number(this.customVenueCostMin) : null,
      estimated_cost_max: this.customVenueCostMax != null ? Number(this.customVenueCostMax) : null,
      isCustomVenue: true,
    };

    cur.items.push(stop);
    this.hasUnsavedChanges = true;
    this.updateBudgetSummary();

    // Reset custom venue inputs
    this.customVenueTitle = '';
    this.customVenueAddress = '';
    this.customVenueCostMin = null;
    this.customVenueCostMax = null;
    this.customVenueDuration = 90;
    this.customVenueNotes = '';
    this.customPlannedTime = '';
    this.customVenueLat = null;
    this.customVenueLng = null;
    this.isCustomCoordsExpanded = false;
    this.closePlacePicker();
  }

  // --- Honest Budget Calculation ---

  private updateBudgetSummary(): void {
    const tempItinerary: Itinerary = {
      id: this.itineraryId || 'temp',
      title: this.form.get('title')?.value || 'Untitled',
      destination: this.form.get('destination')?.value || 'Nueva Ecija',
      start_date: this.form.get('start_date')?.value || '',
      end_date: this.form.get('end_date')?.value || '',
      daily_budget: this.form.get('daily_budget')?.value || 0,
      preferences: [],
      type: 'custom',
      assumptions: [],
      created_at: new Date().toISOString(),
      days: this.days.map((d) => ({
        id: d.id,
        itinerary_id: this.itineraryId || 'temp',
        day_number: d.day_number,
        travel_date: d.travel_date,
        title: d.title,
        items: d.items.map((it) => ({
          id: it.id,
          day_id: d.id,
          place_id: it.place_id,
          custom_title: it.custom_title,
          sort_order: it.sort_order,
          duration_minutes: it.duration_minutes,
          estimated_cost_min: it.estimated_cost_min,
          estimated_cost_max: it.estimated_cost_max,
        })),
      })),
    };

    this.budgetSummary = this.itineraryService.calculateBudgetSummary(tempItinerary);
  }

  // --- Save Itinerary ---

  public async saveItinerary(): Promise<void> {
    if (this.totalStopsCount === 0) {
      const toast = await this.toastController.create({
        message: 'Please add at least one destination before saving your itinerary.',
        duration: 3000,
        color: 'warning',
        position: 'top',
      });
      await toast.present();
      return;
    }

    if (this.form.invalid) {
      this.form.markAllAsTouched();
      const toast = await this.toastController.create({
        message: 'Please complete all required fields.',
        duration: 2500,
        color: 'danger',
        position: 'top',
      });
      await toast.present();
      return;
    }

    this.isSaving = true;
    this.updateUI();
    const formVals = this.form.value;

    const payload = {
      title: formVals.title,
      destination: formVals.destination,
      start_date: formVals.start_date,
      end_date: formVals.end_date,
      daily_budget: Number(formVals.daily_budget),
      preferences: Array.from(this.selectedPreferences),
      type: 'custom' as const,
      assumptions: ['Budget estimates reflect entrance and primary activity fees.'],
      days: this.days.map((d) => ({
        day_number: d.day_number,
        travel_date: d.travel_date,
        title: d.title,
        items: d.items.map((it) => ({
          place_id: it.place_id,
          custom_title: it.custom_title || it.name,
          custom_lat: it.custom_lat ?? it.place?.latitude ?? null,
          custom_lng: it.custom_lng ?? it.place?.longitude ?? null,
          sort_order: it.sort_order,
          planned_time: it.planned_time,
          duration_minutes: it.duration_minutes,
          notes: it.notes,
          estimated_cost_min: it.estimated_cost_min,
          estimated_cost_max: it.estimated_cost_max,
          place: it.place || null,
        })),
      })),
    };

    const action$ = this.isEditMode && this.itineraryId
      ? this.itineraryService.updateItinerary(this.itineraryId, {
          title: payload.title,
          destination: payload.destination,
          start_date: payload.start_date,
          end_date: payload.end_date,
          daily_budget: payload.daily_budget,
          preferences: payload.preferences,
          assumptions: payload.assumptions,
          days: payload.days,
        })
      : this.itineraryService.createItinerary(payload);

    action$.subscribe({
      next: async (saved) => {
        this.isSaving = false;
        this.hasUnsavedChanges = false;
        this.updateUI();
        if (saved && saved.id) {
          this.router.navigate(['/itinerary', saved.id]);
        } else {
          this.router.navigate(['/tabs/home']);
        }
        const toast = await this.toastController.create({
          message: `Itinerary "${saved?.title || 'Trip'}" saved successfully!`,
          duration: 2500,
          color: 'success',
          position: 'top',
        });
        await toast.present();
      },
      error: async (err) => {
        this.isSaving = false;
        this.updateUI();
        let errorMsg = 'Failed to save itinerary. Please try again.';
        if (Array.isArray(err?.error?.detail)) {
          errorMsg = err.error.detail.map((d: any) => d.msg || d.message || JSON.stringify(d)).join('; ');
        } else if (typeof err?.error?.detail === 'string') {
          errorMsg = err.error.detail;
        } else if (err?.error?.detail && typeof err.error.detail === 'object') {
          errorMsg = err.error.detail.message || err.error.detail.msg || 'Failed to save itinerary. Please try again.';
        }
        const toast = await this.toastController.create({
          message: errorMsg,
          duration: 4000,
          color: 'danger',
          position: 'top',
        });
        await toast.present();
      },
    });
  }

  // --- Unsaved Changes Exit Guard ---

  public async onCancel(): Promise<void> {
    if (this.hasUnsavedChanges) {
      const alert = await this.alertController.create({
        header: 'Discard Changes?',
        message: 'You have unsaved changes in your itinerary. Leaving will discard them.',
        buttons: [
          { text: 'Keep Editing', role: 'cancel' },
          {
            text: 'Discard',
            role: 'destructive',
            handler: () => {
              this.router.navigate(['/tabs/home']);
            },
          },
        ],
      });
      await alert.present();
    } else {
      this.router.navigate(['/tabs/home']);
    }
  }

  public formatPlaceCost(place: Place): string {
    if (place.estimated_cost_min != null || place.estimated_cost_max != null) {
      const min = place.estimated_cost_min ?? place.estimated_cost_max;
      const max = place.estimated_cost_max ?? place.estimated_cost_min;
      return min === max ? `₱${min}` : `₱${min} - ₱${max}`;
    }
    return 'Cost not provided';
  }

  private generateTempId(): string {
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
      return crypto.randomUUID();
    }
    return 'tmp-' + Math.random().toString(36).substring(2, 9);
  }
}
