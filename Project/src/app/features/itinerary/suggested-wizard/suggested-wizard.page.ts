import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import {
  IonButton,
  IonContent,
  IonHeader,
  IonIcon,
  IonSpinner,
  IonTitle,
  IonToolbar,
  ToastController,
} from '@ionic/angular';
import { addIcons } from 'ionicons';
import {
  arrowBack,
  calendarOutline,
  cashOutline,
  checkmarkCircle,
  closeOutline,
  createOutline,
  informationCircleOutline,
  locationOutline,
  sparkles,
  timeOutline,
} from 'ionicons/icons';
import { Itinerary } from '../../../core/models/itinerary.models';
import { ItineraryBudgetSummary, ItineraryService } from '../../../core/services/itinerary.service';
import { PlaceService } from '../../../core/services/place.service';

export interface PreferenceOption {
  key: string;
  label: string;
  icon?: string;
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
    IonTitle,
    IonButton,
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

  public quickDestinations = [
    'Nueva Ecija',
    'Bongabon',
    'Pantabangan',
    'Cabanatuan City',
    'Gapan City',
    'General Tinio',
  ];

  public budgetPresets = [1500, 2500, 4000, 6000];

  public preferenceOptions: PreferenceOption[] = [
    { key: 'nature', label: 'Nature & Adventure' },
    { key: 'heritage', label: 'Heritage & Faith' },
    { key: 'food', label: 'Food & Dining' },
    { key: 'relaxation', label: 'Resorts & Swimming' },
    { key: 'culture', label: 'Culture & Museum' },
    { key: 'scenic', label: 'Scenic Viewpoints' },
  ];

  public selectedPreferences: Set<string> = new Set(['nature', 'food']);

  constructor(
    private fb: FormBuilder,
    private router: Router,
    private itineraryService: ItineraryService,
    public placeService: PlaceService,
    private toastController: ToastController
  ) {
    addIcons({
      arrowBack,
      sparkles,
      locationOutline,
      calendarOutline,
      cashOutline,
      timeOutline,
      checkmarkCircle,
      createOutline,
      informationCircleOutline,
      closeOutline,
    });

    const today = new Date();
    const tomorrow = new Date();
    tomorrow.setDate(today.getDate() + 1);

    this.form = this.fb.group({
      destination: ['Nueva Ecija', [Validators.required]],
      start_date: [today.toISOString().split('T')[0], [Validators.required]],
      end_date: [tomorrow.toISOString().split('T')[0], [Validators.required]],
      daily_budget: [2500, [Validators.required, Validators.min(0)]],
    });
  }

  public ngOnInit(): void {}

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

  public get computedTripDays(): number {
    const startStr = this.form.get('start_date')?.value;
    const endStr = this.form.get('end_date')?.value;
    if (!startStr || !endStr) return 1;

    const start = new Date(startStr);
    const end = new Date(endStr);
    const diff = Math.max(0, end.getTime() - start.getTime());
    return Math.max(1, Math.ceil(diff / (1000 * 60 * 60 * 24)) + 1);
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
        this.budgetSummary = this.itineraryService.calculateBudgetSummary(plan);
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
  }

  public async acceptAndSave(): Promise<void> {
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
          await this.router.navigate(['/tabs/home']);
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

    // Navigate to custom builder or history
    this.acceptAndSave().then(() => {
      // User can customize from saved list
    });
  }

  public backToForm(): void {
    this.generatedPlan = null;
  }

  public onBack(): void {
    if (this.generatedPlan) {
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
}
