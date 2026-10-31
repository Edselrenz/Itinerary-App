import { Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
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
  arrowUpOutline,
  businessOutline,
  calendarOutline,
  cashOutline,
  checkmarkCircle,
  closeOutline,
  locationOutline,
  saveOutline,
  searchOutline,
  sparkles,
  timeOutline,
  trashOutline,
} from 'ionicons/icons';
import { Subscription, debounceTime, distinctUntilChanged } from 'rxjs';
import { Itinerary } from '../../../core/models/itinerary.models';
import { Place } from '../../../core/models/place.models';
import { ItineraryBudgetSummary, ItineraryService } from '../../../core/services/itinerary.service';
import { PlaceService } from '../../../core/services/place.service';

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
  ],
})
export class CustomBuilderPage implements OnInit, OnDestroy {
  public form: FormGroup;
  public days: BuilderDay[] = [];
  public activeDayIndex = 0;
  public itineraryId: string | null = null;
  public isEditMode = false;
  public isSaving = false;
  public hasUnsavedChanges = false;

  // Budget summary
  public budgetSummary: ItineraryBudgetSummary = {
    verifiedMin: 0,
    verifiedMax: 0,
    unverifiedCount: 0,
    displayText: 'No stops added',
  };

  // Place Picker Modal state
  public isPlacePickerOpen = false;
  public pickerSearchTerm = '';
  public pickerSearchResults: Place[] = [];
  public pickerSearching = false;
  public pickerTab: 'browse' | 'custom' = 'browse';

  // Custom venue form fields
  public customVenueTitle = '';
  public customVenueAddress = '';
  public customVenueCostMin: number | null = null;
  public customVenueCostMax: number | null = null;
  public customVenueDuration = 90;
  public customVenueNotes = '';

  private subscriptions = new Subscription();

  constructor(
    private fb: FormBuilder,
    private route: ActivatedRoute,
    private router: Router,
    private itineraryService: ItineraryService,
    public placeService: PlaceService,
    private alertController: AlertController,
    private toastController: ToastController
  ) {
    addIcons({
      arrowBack,
      addOutline,
      trashOutline,
      arrowUpOutline,
      arrowDownOutline,
      timeOutline,
      cashOutline,
      locationOutline,
      calendarOutline,
      saveOutline,
      checkmarkCircle,
      alertCircleOutline,
      closeOutline,
      searchOutline,
      sparkles,
      businessOutline,
    });

    const today = new Date();
    const tomorrow = new Date();
    tomorrow.setDate(today.getDate() + 1);

    this.form = this.fb.group({
      title: ['Nueva Ecija Getaway', [Validators.required, Validators.minLength(3)]],
      destination: ['Nueva Ecija', [Validators.required]],
      start_date: [today.toISOString().split('T')[0], [Validators.required]],
      end_date: [tomorrow.toISOString().split('T')[0], [Validators.required]],
      daily_budget: [2500, [Validators.required, Validators.min(0)]],
    });
  }

  public ngOnInit(): void {
    this.itineraryId = this.route.snapshot.paramMap.get('id');

    if (this.itineraryId) {
      this.isEditMode = true;
      this.loadItinerary(this.itineraryId);
    } else {
      this.initDefaultDays();
    }

    this.subscriptions.add(
      this.form.valueChanges.subscribe(() => {
        this.hasUnsavedChanges = true;
        this.updateBudgetSummary();
      })
    );
  }

  public ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
  }

  private initDefaultDays(): void {
    const startDate = this.form.get('start_date')?.value || new Date().toISOString().split('T')[0];
    const endDate = this.form.get('end_date')?.value || startDate;

    const start = new Date(startDate);
    const end = new Date(endDate);
    const diffTime = Math.max(0, end.getTime() - start.getTime());
    const diffDays = Math.max(1, Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1);

    this.days = [];
    for (let i = 0; i < diffDays; i++) {
      const dayDate = new Date(start);
      dayDate.setDate(start.getDate() + i);
      this.days.push({
        id: this.generateTempId(),
        day_number: i + 1,
        travel_date: dayDate.toISOString().split('T')[0],
        title: `Day ${i + 1}`,
        items: [],
      });
    }

    this.activeDayIndex = 0;
    this.updateBudgetSummary();
  }

  private loadItinerary(id: string): void {
    this.itineraryService.getItineraryById(id).subscribe({
      next: (itin) => {
        this.form.patchValue({
          title: itin.title,
          destination: itin.destination,
          start_date: itin.start_date,
          end_date: itin.end_date,
          daily_budget: itin.daily_budget,
        });

        this.days = (itin.days || []).map((d) => ({
          id: d.id,
          day_number: d.day_number,
          travel_date: d.travel_date,
          title: d.title || `Day ${d.day_number}`,
          items: (d.items || []).map((item) => ({
            id: item.id,
            place_id: item.place_id,
            custom_title: item.custom_title,
            custom_lat: item.custom_lat,
            custom_lng: item.custom_lng,
            sort_order: item.sort_order,
            planned_time: item.planned_time,
            duration_minutes: item.duration_minutes || 90,
            notes: item.notes,
            estimated_cost_min: item.estimated_cost_min,
            estimated_cost_max: item.estimated_cost_max,
            name: item.custom_title || item.place?.name || 'Destination Stop',
            category: item.place?.category
              ? this.placeService.formatCategoryName(item.place.category)
              : 'Custom Stop',
            municipality: item.place?.municipality_name || 'Nueva Ecija',
            image: this.placeService.getPlaceImage(
              item.custom_title || item.place?.name || '',
              item.place?.image_url
            ),
            isCustomVenue: !item.place_id,
          })),
        }));

        this.activeDayIndex = 0;
        this.updateBudgetSummary();
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

  public selectDay(index: number): void {
    if (index >= 0 && index < this.days.length) {
      this.activeDayIndex = index;
    }
  }

  public addDay(): void {
    const lastDay = this.days[this.days.length - 1];
    let nextDateStr = new Date().toISOString().split('T')[0];

    if (lastDay && lastDay.travel_date) {
      const nextDate = new Date(lastDay.travel_date);
      nextDate.setDate(nextDate.getDate() + 1);
      nextDateStr = nextDate.toISOString().split('T')[0];
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
    this.hasUnsavedChanges = true;
  }

  public moveStopDown(itemIndex: number): void {
    const cur = this.currentDay;
    if (!cur || itemIndex >= cur.items.length - 1) return;

    const temp = cur.items[itemIndex];
    cur.items[itemIndex] = cur.items[itemIndex + 1];
    cur.items[itemIndex + 1] = temp;

    this.reindexSortOrder(cur);
    this.hasUnsavedChanges = true;
  }

  public removeStop(itemIndex: number): void {
    const cur = this.currentDay;
    if (!cur) return;

    cur.items.splice(itemIndex, 1);
    this.reindexSortOrder(cur);
    this.hasUnsavedChanges = true;
    this.updateBudgetSummary();
  }

  private reindexSortOrder(day: BuilderDay): void {
    day.items.forEach((item, idx) => {
      item.sort_order = idx + 1;
    });
  }

  // --- Place Picker & Duplicate Guard ---

  public openPlacePicker(): void {
    this.isPlacePickerOpen = true;
    this.pickerSearchTerm = '';
    this.pickerTab = 'browse';
    this.loadFeaturedPlacesForPicker();
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

  private addPlaceStop(place: Place): void {
    const cur = this.currentDay;
    if (!cur) return;

    const stop: BuilderStop = {
      id: this.generateTempId(),
      place_id: place.id,
      name: place.name,
      category: this.placeService.formatCategoryName(place.category),
      municipality: place.municipality_name || 'Nueva Ecija',
      image: this.placeService.getPlaceImage(place.name, place.image_url),
      sort_order: cur.items.length + 1,
      duration_minutes: 90,
      estimated_cost_min: place.estimated_cost_min,
      estimated_cost_max: place.estimated_cost_max,
      isCustomVenue: false,
    };

    cur.items.push(stop);
    this.hasUnsavedChanges = true;
    this.updateBudgetSummary();
  }

  public addCustomVenueStop(): void {
    const cur = this.currentDay;
    if (!cur) return;

    const trimmedTitle = this.customVenueTitle.trim();
    if (!trimmedTitle) return;

    const stop: BuilderStop = {
      id: this.generateTempId(),
      place_id: null,
      custom_title: trimmedTitle,
      name: trimmedTitle,
      category: 'Custom Venue',
      municipality: this.customVenueAddress.trim() || 'Nueva Ecija',
      image: 'assets/images/casa_batik.png',
      sort_order: cur.items.length + 1,
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
    this.customVenueNotes = '';
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
    const formVals = this.form.value;

    const payload = {
      title: formVals.title,
      destination: formVals.destination,
      start_date: formVals.start_date,
      end_date: formVals.end_date,
      daily_budget: Number(formVals.daily_budget),
      preferences: [],
      type: 'custom' as const,
      assumptions: ['Budget estimates reflect entrance and primary activity fees.'],
      days: this.days.map((d) => ({
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
        })
      : this.itineraryService.createItinerary(payload);

    action$.subscribe({
      next: async (saved) => {
        this.isSaving = false;
        this.hasUnsavedChanges = false;
        this.router.navigate(['/tabs/home']);
        const toast = await this.toastController.create({
          message: `Itinerary "${saved.title}" saved successfully!`,
          duration: 2500,
          color: 'success',
          position: 'top',
        });
        await toast.present();
      },
      error: async (err) => {
        this.isSaving = false;
        const toast = await this.toastController.create({
          message: err?.error?.detail || 'Failed to save itinerary. Please try again.',
          duration: 3500,
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
