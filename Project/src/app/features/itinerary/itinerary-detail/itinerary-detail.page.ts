import {
  AfterViewInit,
  Component,
  ElementRef,
  Inject,
  OnDestroy,
  OnInit,
  PLATFORM_ID,
  ViewChild,
} from '@angular/core';
import { CommonModule, isPlatformBrowser, Location } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import * as L from 'leaflet';
import {
  AlertController,
  IonContent,
  IonHeader,
  IonIcon,
  IonModal,
  IonSpinner,
  IonToolbar,
  ToastController,
} from '@ionic/angular';
import { addIcons } from 'ionicons';
import {
  addCircleOutline,
  addOutline,
  alertCircleOutline,
  arrowBack,
  arrowDown,
  arrowForward,
  arrowForwardOutline,
  arrowUp,
  busOutline,
  calendar,
  calendarOutline,
  carOutline,
  cashOutline,
  checkmarkCircle,
  chevronDownOutline,
  chevronUpOutline,
  close,
  closeOutline,
  compassOutline,
  copyOutline,
  createOutline,
  downloadOutline,
  informationCircle,
  informationCircleOutline,
  locationOutline,
  locationSharp,
  mapOutline,
  navigateCircleOutline,
  navigateOutline,
  openOutline,
  printOutline,
  shareSocialOutline,
  shieldCheckmarkOutline,
  sparkles,
  speedometerOutline,
  storefrontOutline,
  timeOutline,
  trash,
  trashOutline,
  walkOutline,
} from 'ionicons/icons';
import { of, Subscription, throwError } from 'rxjs';
import { catchError, timeout } from 'rxjs/operators';
import {
  Itinerary,
  ItineraryBudgetSummary,
  ItineraryDay,
  ItineraryItem,
} from '../../../core/models/itinerary.models';
import { Place } from '../../../core/models/place.models';
import { formatDateRange } from '../../../core/utils/date.utils';
import { ItineraryService } from '../../../core/services/itinerary.service';
import { NearbyPlaceItem, PlaceService } from '../../../core/services/place.service';
import { RouteTrackingService } from '../../../core/services/route-tracking.service';
import { decodePolyline } from '../../../core/utils/polyline.util';
import { environment } from '../../../../environments/environment';
import {
  CommuteInfo,
  LegCommuteInfo,
  getCommuteInfoForMunicipality,
  getLegCommuteInfo,
} from '../../../core/data/commute-guide.data';
import {
  buildGoogleMapsDayRouteUrl,
  copyTextSummary,
  downloadIcsFile,
  shareNativeItinerary,
  triggerPrintItinerary,
} from '../../../core/utils/itinerary-export.util';
import { PlaceDetailSheetComponent } from '../../../shared/components/place-detail-sheet/place-detail-sheet.component';
import { ItineraryRouteMapComponent } from '../../../shared/components/itinerary-route-map/itinerary-route-map.component';
import { ComponentCanDeactivate } from '../../../core/guards/pending-changes.guard';

export interface EditableActivityItem {
  id: string;
  custom_title: string;
  planned_time: string;
  duration_label: string;
  description: string;
  notes: string;
  estimated_cost: number | null;
  estimated_cost_min?: number | null;
  estimated_cost_max?: number | null;
  target_day_index: number;
  place_id?: string | null;
  place?: any;
}

export interface EditableDay {
  day_number: number;
  travel_date: string;
  items: EditableActivityItem[];
}

export interface EditableItineraryForm {
  title: string;
  destination: string;
  start_date: string;
  end_date: string;
  daily_budget: number;
  days: EditableDay[];
}

@Component({
  selector: 'app-itinerary-detail',
  templateUrl: './itinerary-detail.page.html',
  styleUrls: ['./itinerary-detail.page.scss'],
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    IonContent,
    IonHeader,
    IonToolbar,
    IonIcon,
    IonSpinner,
    IonModal,
    PlaceDetailSheetComponent,
    ItineraryRouteMapComponent,
  ],
})
export class ItineraryDetailPage implements OnInit, AfterViewInit, OnDestroy, ComponentCanDeactivate {
  public itineraryId: string | null = null;
  public itinerary: Itinerary | null = null;
  public isLoading = true;
  public activeDayIndex = 0;
  public budgetSummary: ItineraryBudgetSummary | null = null;

  // Embedded Day Route Preview Map (Phase 25.3)
  @ViewChild('previewMapElement', { static: false }) private previewMapElementRef?: ElementRef<HTMLDivElement>;
  public previewMap: L.Map | null = null;
  public previewPolylineLayer: L.Polyline | null = null;
  public previewStopsLayer: L.LayerGroup | null = null;
  public isPreviewMapExpanded = true;
  private isBrowser = false;

  // In-Place Edit Mode state (Image 2 View vs Image 3 Edit)
  public isEditMode = false;
  public editForm: EditableItineraryForm = {
    title: '',
    destination: '',
    start_date: '',
    end_date: '',
    daily_budget: 0,
    days: [],
  };

  // View state: 'itinerary' (Overview / Day Timeline) | 'nearby' (Nearby Places)
  public viewMode: 'itinerary' | 'nearby' = 'itinerary';
  public activeNearbyTab: 'restaurants' | 'hospitals' | 'stores' = 'restaurants';
  public nearbyPlacesList: NearbyPlaceItem[] = [];

  // Stop Details Modal state
  public selectedStop: ItineraryItem | null = null;
  public isStopModalOpen = false;
  public isAssumptionsExpanded = false;
  public isShareModalOpen = false;

  private subscriptions = new Subscription();

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private itineraryService: ItineraryService,
    public placeService: PlaceService,
    public routeTrackingService: RouteTrackingService,
    private alertController: AlertController,
    private toastController: ToastController,
    private location: Location,
    @Inject(PLATFORM_ID) private platformId: object
  ) {
    this.isBrowser = isPlatformBrowser(this.platformId);
    if (this.isBrowser && typeof window !== 'undefined' && !(window as any).L) {
      (window as unknown as { L: unknown }).L = (L as unknown as { default?: unknown }).default ?? L;
    }
    addIcons({
      arrowBack,
      arrowForward,
      arrowForwardOutline,
      arrowUp,
      arrowDown,
      close,
      closeOutline,
      createOutline,
      trash,
      trashOutline,
      alertCircleOutline,
      shieldCheckmarkOutline,
      informationCircleOutline,
      compassOutline,
      calendar,
      calendarOutline,
      carOutline,
      storefrontOutline,
      cashOutline,
      locationOutline,
      openOutline,
      addCircleOutline,
      addOutline,
      timeOutline,
      busOutline,
      informationCircle,
      checkmarkCircle,
      chevronDownOutline,
      chevronUpOutline,
      locationSharp,
      mapOutline,
      navigateCircleOutline,
      navigateOutline,
      sparkles,
      speedometerOutline,
      walkOutline,
      shareSocialOutline,
      copyOutline,
      printOutline,
      downloadOutline,
    });
  }

  public ngOnInit(): void {
    this.itineraryId = this.route.snapshot.paramMap.get('id');
    if (this.itineraryId) {
      this.loadItinerary(this.itineraryId);
    } else {
      this.isLoading = false;
    }
  }

  public ngAfterViewInit(): void {
    if (this.isBrowser) {
      setTimeout(() => {
        this.initPreviewMap();
      }, 300);
    }
  }

  public ionViewDidEnter(): void {
    if (this.isBrowser && this.previewMap) {
      setTimeout(() => {
        this.previewMap?.invalidateSize();
        this.updatePreviewMap();
      }, 150);
    }
  }

  public ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
    if (this.previewMap) {
      this.previewMap.remove();
      this.previewMap = null;
    }
  }

  /**
   * Prevents accidental navigation when travelers have unsaved itinerary edits in in-place edit mode (ROUTE-04).
   */
  public canDeactivate(): boolean | Promise<boolean> {
    if (!this.isEditMode) {
      return true;
    }
    return new Promise<boolean>((resolve) => {
      this.alertController
        .create({
          header: 'Discard Unsaved Edits?',
          message: 'You have unsaved edits in this itinerary. Leaving now will discard your current modifications.',
          buttons: [
            {
              text: 'Keep Editing',
              role: 'cancel',
              handler: () => resolve(false),
            },
            {
              text: 'Discard & Leave',
              role: 'destructive',
              handler: () => {
                this.isEditMode = false;
                resolve(true);
              },
            },
          ],
        })
        .then((alert) => alert.present());
    });
  }

  public loadItinerary(id: string): void {
    const cached = this.itineraryService.getCachedItineraryById?.(id);
    if (cached) {
      this.itinerary = cached;
      this.initEditForm();
      this.activeDayIndex = 0;
      this.budgetSummary = this.itineraryService.calculateBudgetSummary(cached);
      this.refreshNearbyPlaces();
      this.isLoading = false;
      setTimeout(() => this.updatePreviewMap(), 100);
    } else {
      this.isLoading = true;
    }

    this.subscriptions.add(
      this.itineraryService
        .getItineraryById(id)
        .pipe(
          timeout(4000),
          catchError((err) => {
            if (cached) {
              return of(cached);
            }
            return throwError(() => err);
          })
        )
        .subscribe({
          next: (itin) => {
            this.itinerary = itin;
            this.initEditForm();
            this.budgetSummary = this.itineraryService.calculateBudgetSummary(itin);
            this.refreshNearbyPlaces();
            this.isLoading = false;
            setTimeout(() => this.updatePreviewMap(), 100);
          },
          error: () => {
            this.isLoading = false;
          },
        })
    );
  }

  public initEditForm(): void {
    if (!this.itinerary) return;
    this.editForm = {
      title: this.itinerary.title || '',
      destination: this.itinerary.destination || '',
      start_date: this.itinerary.start_date || '',
      end_date: this.itinerary.end_date || '',
      daily_budget: this.itinerary.daily_budget || 0,
      days: (this.itinerary.days || []).map((day, dIdx) => ({
        day_number: day.day_number || dIdx + 1,
        travel_date: day.travel_date || '',
        items: (day.items || []).map((item) => ({
          id: item.id || `item-${Date.now()}-${Math.random()}`,
          custom_title: this.getStopTitle(item),
          planned_time: item.planned_time || '08:00 AM',
          duration_label: this.formatDurationHours(item),
          description: this.getStopDescription(item),
          notes: item.notes || '',
          estimated_cost: item.estimated_cost_min ?? item.estimated_cost_max ?? null,
          estimated_cost_min: item.estimated_cost_min ?? null,
          estimated_cost_max: item.estimated_cost_max ?? null,
          target_day_index: dIdx,
          place_id: item.place_id,
          place: item.place,
        })),
      })),
    };
  }

  public toggleEditMode(): void {
    this.initEditForm();
    this.isEditMode = true;
  }

  public cancelEdit(): void {
    this.isEditMode = false;
    this.initEditForm();
  }

  public addDay(): void {
    const nextDayNum = this.editForm.days.length + 1;
    let nextDate = '';
    if (this.editForm.days.length > 0) {
      const lastDate = this.editForm.days[this.editForm.days.length - 1].travel_date;
      if (lastDate) {
        const d = new Date(lastDate);
        d.setDate(d.getDate() + 1);
        nextDate = d.toISOString().split('T')[0];
      }
    } else {
      nextDate = this.editForm.start_date || new Date().toISOString().split('T')[0];
    }

    this.editForm.days.push({
      day_number: nextDayNum,
      travel_date: nextDate,
      items: [],
    });
  }

  public async removeDay(dIdx: number): Promise<void> {
    if (this.editForm.days.length <= 1) {
      const toast = await this.toastController.create({
        message: 'An itinerary must have at least one day.',
        duration: 2000,
        color: 'warning',
        position: 'top',
      });
      await toast.present();
      return;
    }

    this.editForm.days.splice(dIdx, 1);
    this.editForm.days.forEach((day, idx) => {
      day.day_number = idx + 1;
      day.items.forEach((item) => {
        item.target_day_index = idx;
      });
    });
  }

  public addActivity(dIdx: number): void {
    const day = this.editForm.days[dIdx];
    if (!day) return;
    const newAct: EditableActivityItem = {
      id: `act-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
      custom_title: '',
      planned_time: '08:00 AM',
      duration_label: '2 hours',
      description: '',
      notes: '',
      estimated_cost: 0,
      target_day_index: dIdx,
    };
    day.items.push(newAct);
  }

  public deleteActivity(dIdx: number, aIdx: number): void {
    const day = this.editForm.days[dIdx];
    if (day && day.items) {
      day.items.splice(aIdx, 1);
    }
  }

  public moveActivityUp(dIdx: number, aIdx: number): void {
    const day = this.editForm.days[dIdx];
    if (day && day.items && aIdx > 0) {
      const temp = day.items[aIdx];
      day.items[aIdx] = day.items[aIdx - 1];
      day.items[aIdx - 1] = temp;
    }
  }

  public moveActivityDown(dIdx: number, aIdx: number): void {
    const day = this.editForm.days[dIdx];
    if (day && day.items && aIdx < day.items.length - 1) {
      const temp = day.items[aIdx];
      day.items[aIdx] = day.items[aIdx + 1];
      day.items[aIdx + 1] = temp;
    }
  }

  public moveActivityToDifferentDay(currentDayIdx: number, aIdx: number, targetIdxRaw: number | string): void {
    const targetIdx = Number(targetIdxRaw);
    if (isNaN(targetIdx) || targetIdx === currentDayIdx) return;
    const curDay = this.editForm.days[currentDayIdx];
    const targetDay = this.editForm.days[targetIdx];
    if (!curDay || !targetDay) return;

    const [movedItem] = curDay.items.splice(aIdx, 1);
    if (movedItem) {
      movedItem.target_day_index = targetIdx;
      targetDay.items.push(movedItem);
    }
  }

  public parseDurationMinutes(label: string): number {
    if (!label) return 90;
    const match = label.match(/(\d+)/);
    if (match) {
      const num = parseInt(match[1], 10);
      if (label.toLowerCase().includes('hour') || label.toLowerCase().includes('hr')) {
        return num * 60;
      }
      return num;
    }
    return 90;
  }

  public async saveChanges(): Promise<void> {
    if (!this.itinerary) return;

    const payloadDays = this.editForm.days.map((day, dIdx) => ({
      day_number: day.day_number || dIdx + 1,
      travel_date: day.travel_date,
      title: `Day ${day.day_number || dIdx + 1}`,
      items: day.items.map((act, aIdx) => ({
        place_id: act.place_id || null,
        custom_title: act.custom_title,
        planned_time: act.planned_time,
        duration_minutes: this.parseDurationMinutes(act.duration_label),
        notes: act.notes,
        estimated_cost_min: act.estimated_cost_min != null ? act.estimated_cost_min : act.estimated_cost,
        estimated_cost_max: act.estimated_cost_max != null ? act.estimated_cost_max : act.estimated_cost,
        sort_order: aIdx + 1,
        place: act.place || {
          name: act.custom_title,
          description: act.description,
          municipality_name: this.editForm.destination,
        },
      })),
    }));

    const updatePayload = {
      title: this.editForm.title,
      destination: this.editForm.destination,
      start_date: this.editForm.start_date,
      end_date: this.editForm.end_date,
      daily_budget: Number(this.editForm.daily_budget) || 0,
      days: payloadDays,
    };

    this.subscriptions.add(
      this.itineraryService.updateItinerary(this.itinerary.id, updatePayload).subscribe({
        next: async (updated) => {
          this.itinerary = updated;
          this.budgetSummary = this.itineraryService.calculateBudgetSummary(updated);
          this.isEditMode = false;
          const toast = await this.toastController.create({
            message: 'Itinerary changes saved successfully!',
            duration: 2500,
            color: 'success',
            position: 'top',
          });
          await toast.present();
        },
        error: async () => {
          const toast = await this.toastController.create({
            message: 'Failed to save changes. Please try again.',
            duration: 2500,
            color: 'danger',
            position: 'top',
          });
          await toast.present();
        },
      })
    );
  }

  public getDaysNightsLabel(itin: Itinerary | null): string {
    const days = itin?.days?.length || 1;
    const nights = Math.max(0, days - 1);
    return nights > 0
      ? `${days} Days - ${nights} ${nights === 1 ? 'Night' : 'Nights'}`
      : `${days} Day`;
  }

  public formatDayTravelDate(dateStr?: string): string {
    if (!dateStr) return '';
    try {
      const parts = dateStr.split('-');
      if (parts.length === 3) {
        const d = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));
        if (!isNaN(d.getTime())) {
          return d.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric',
          });
        }
      }
    } catch {
      // fallback
    }
    return dateStr;
  }

  public formatTimingHour(item: ItineraryItem): string {
    if (item.planned_time) {
      const match = item.planned_time.match(/(\d{1,2}:\d{2})/);
      if (match) {
        return match[1];
      }
      return item.planned_time;
    }
    return '08:00';
  }

  public formatDurationHours(item: ItineraryItem): string {
    if (item.duration_minutes) {
      const hrs = Math.round(item.duration_minutes / 60);
      return hrs >= 1 ? `${hrs} ${hrs === 1 ? 'hour' : 'hours'}` : `${item.duration_minutes} mins`;
    }
    return '2 hours';
  }

  public getStopEstimatedCost(item: ItineraryItem): string {
    const cost = item.estimated_cost_min ?? item.estimated_cost_max;
    if (cost != null) {
      if (cost === 0) return 'Free Admission';
      return `₱${cost.toLocaleString()}`;
    }
    return 'Fee not listed';
  }

  public getStopDescription(item: ItineraryItem): string {
    if (item.place?.description) {
      return item.place.description;
    }
    if (item.notes) {
      return item.notes;
    }
    return 'Explore the destination and local culture. Enjoy sightseeing and take photos.';
  }

  public calculateTotalActivityExpenses(): number {
    if (!this.itinerary?.days) return 0;
    let sum = 0;
    for (const day of this.itinerary.days) {
      for (const item of day.items || []) {
        const cost = item.estimated_cost_min ?? item.estimated_cost_max;
        if (cost != null && !isNaN(Number(cost))) {
          sum += Number(cost);
        }
      }
    }
    return sum;
  }

  public selectDay(index: number): void {
    this.activeDayIndex = index;
    this.refreshNearbyPlaces();
    this.updatePreviewMap();
    if (this.isBrowser && typeof document !== 'undefined') {
      setTimeout(() => {
        const el = document.getElementById(`day-card-${index}`);
        if (el) {
          el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
      }, 50);
    }
  }

  public refreshNearbyPlaces(): void {
    const curDay = this.itinerary?.days[this.activeDayIndex];
    const muni = this.getDayLocation(curDay);
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

  public get currentDay(): ItineraryDay | undefined {
    return this.itinerary?.days[this.activeDayIndex];
  }

  public get computedTripDays(): number {
    return this.itinerary?.days.length || 1;
  }

  public get totalStopsCount(): number {
    if (!this.itinerary) return 0;
    return this.itinerary.days.reduce(
      (acc, d) => acc + (d.items ? d.items.length : 0),
      0
    );
  }

  public get formattedDateSpan(): string {
    if (!this.itinerary?.start_date || !this.itinerary?.end_date) {
      return '';
    }
    const days = this.computedTripDays;
    const nights = Math.max(0, days - 1);
    const rangeStr = formatDateRange(this.itinerary.start_date, this.itinerary.end_date);
    return `${rangeStr} (${days} ${days === 1 ? 'day' : 'days'}, ${nights} ${nights === 1 ? 'night' : 'nights'})`;
  }

  public formatDailyBudget(itinerary: Itinerary): string {
    if (itinerary.daily_budget && itinerary.daily_budget > 0) {
      return `₱ ${itinerary.daily_budget.toLocaleString()}/day`;
    }
    return 'Flexible Budget';
  }

  public getDayLocation(day: ItineraryDay | undefined): string {
    if (!day || !day.items || day.items.length === 0) {
      return this.itinerary?.destination || 'Nueva Ecija';
    }
    const stopWithMuni = day.items.find((it) => it.place?.municipality_name);
    return (
      stopWithMuni?.place?.municipality_name ||
      this.itinerary?.destination ||
      'Nueva Ecija'
    );
  }

  public getDaySubtitle(day: ItineraryDay | undefined): string {
    if (!day || !day.items || day.items.length === 0) {
      return 'Spontaneous discoveries and relaxed travel pace!';
    }
    const categories = new Set(
      day.items
        .map((it) => it.place?.category || 'destinations')
        .map((c) => this.placeService.formatCategoryName(c))
    );
    const catList = Array.from(categories).slice(0, 3);
    const catLabels = catList.join(', ');
    const muni = this.getDayLocation(day);
    return `${catLabels} in ${muni}!`;
  }

  public getStopTitle(item: ItineraryItem): string {
    return item.place?.name || item.custom_title || 'Destination Stop';
  }

  public getStopImage(item: ItineraryItem): string {
    const name = this.getStopTitle(item);
    return this.placeService.getPlaceImage(name);
  }

  public getStopCategory(item: ItineraryItem): string {
    if (item.place?.category) {
      return this.placeService.formatCategoryName(item.place.category);
    }
    return 'Destination';
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

  public getTimingTime(stop: ItineraryItem, index?: number): string {
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
    const day = this.currentDay;
    if (day && day.items && day.items.length > 0) {
      const idx = index !== undefined ? index : day.items.indexOf(stop);
      if (idx >= 0) {
        let totalMinutes = 510; // 08:30 AM
        for (let i = 0; i < idx; i++) {
          totalMinutes += (day.items[i].duration_minutes || 90) + 30;
        }
        const dur = stop.duration_minutes || 90;
        const startH = Math.floor(totalMinutes / 60) % 24;
        const startM = totalMinutes % 60;
        const endTotal = totalMinutes + dur;
        const endH = Math.floor(endTotal / 60) % 24;
        const endM = endTotal % 60;

        const formatHour = (h: number, m: number) => {
          const ampm = h >= 12 ? 'PM' : 'AM';
          const h12 = h % 12 || 12;
          const mm = m < 10 ? `0${m}` : `${m}`;
          return `${h12}:${mm} ${ampm}`;
        };

        return `${formatHour(startH, startM)} - ${formatHour(endH, endM)}`;
      }
    }
    return 'Flexible time';
  }

  public getTimingDuration(stop: ItineraryItem): string {
    if (stop.planned_time && stop.planned_time.includes('Night')) {
      return '22 hrs';
    }
    if (stop.duration_minutes) {
      const hrs = Math.round(stop.duration_minutes / 60);
      return hrs >= 1 ? `${hrs} hrs` : `${stop.duration_minutes} mins`;
    }
    return '2 hrs';
  }

  public getStopCost(item: ItineraryItem): string {
    if (item.estimated_cost_min != null || item.estimated_cost_max != null) {
      const min = item.estimated_cost_min ?? item.estimated_cost_max;
      const max = item.estimated_cost_max ?? item.estimated_cost_min;
      return min === max ? `₱${min}` : `₱${min} - ₱${max}`;
    }
    return 'Price not listed';
  }

  public openStopDetail(item: ItineraryItem): void {
    this.selectedStop = item;
    this.isStopModalOpen = true;
  }

  public closeStopDetail(): void {
    this.isStopModalOpen = false;
    this.selectedStop = null;
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
      name: this.getStopTitle(this.selectedStop),
      latitude: this.selectedStop.custom_lat ?? 15.58,
      longitude: this.selectedStop.custom_lng ?? 121.0,
      category: 'attraction',
      municipality_name: this.itinerary?.destination || 'Nueva Ecija',
      description: this.getStopDescription(this.selectedStop),
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

  public openInGoogleMaps(item: ItineraryItem): void {
    const lat = item.place?.latitude || item.custom_lat;
    const lng = item.place?.longitude || item.custom_lng;
    const title = this.getStopTitle(item);

    let url: string;
    if (lat && lng) {
      url = `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`;
    } else {
      url = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
        title + ' Nueva Ecija'
      )}`;
    }
    window.open(url, '_blank', 'noopener,noreferrer');
  }

  public getCommuteInfo(stop: ItineraryItem): LegCommuteInfo {
    const curDay = this.itinerary?.days[this.activeDayIndex];
    if (curDay && curDay.items) {
      const idx = curDay.items.findIndex((s) => s.id === stop.id);
      if (idx > 0) {
        const prev = curDay.items[idx - 1];
        return getLegCommuteInfo(prev, stop);
      }
    }
    return getLegCommuteInfo(null, stop);
  }

  public openNearbyInMaps(place: NearbyPlaceItem): void {
    const url = `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(
      place.name + ' ' + place.municipality + ' Nueva Ecija'
    )}`;
    window.open(url, '_blank', 'noopener,noreferrer');
  }

  public async addNearbyPlaceToActiveDay(place: NearbyPlaceItem): Promise<void> {
    const currentDay = this.currentDay;
    if (!currentDay) return;
    if (!currentDay.items) {
      currentDay.items = [];
    }

    const fallbackLat =
      currentDay.items.find((it) => it.place?.latitude || it.custom_lat)?.place?.latitude ??
      currentDay.items.find((it) => it.place?.latitude || it.custom_lat)?.custom_lat ??
      15.58;
    const fallbackLng =
      currentDay.items.find((it) => it.place?.longitude || it.custom_lng)?.place?.longitude ??
      currentDay.items.find((it) => it.place?.longitude || it.custom_lng)?.custom_lng ??
      121.0;

    const newStop: ItineraryItem = {
      id: `nearby-added-${Date.now()}`,
      day_id: currentDay.id || `day-${currentDay.day_number}`,
      sort_order: currentDay.items.length + 1,
      duration_minutes: 60,
      planned_time: '12:00 PM',
      custom_title: place.name,
      place: {
        id: place.id,
        name: place.name,
        category: place.category === 'restaurant' ? 'restaurant' : place.category === 'hospital' ? 'pharmacy' : 'convenience_store',
        latitude: place.latitude ?? fallbackLat,
        longitude: place.longitude ?? fallbackLng,
        municipality_name: place.municipality,
        opening_hours: place.openingHours,
        cost_currency: 'PHP',
        is_featured: false,
        source_name: 'NearbyEssential',
        source_record_id: place.id,
        imported_at: new Date().toISOString(),
      } as any,
    };

    currentDay.items.push(newStop);
    if (this.itinerary) {
      this.budgetSummary = this.itineraryService.calculateBudgetSummary(this.itinerary);
      this.itineraryService.updateItinerary(this.itinerary.id, {
        days: this.itinerary.days,
      }).subscribe();
      this.updatePreviewMap();
    }

    const toast = await this.toastController.create({
      message: `Added ${place.name} to Day ${currentDay.day_number}!`,
      duration: 2000,
      color: 'dark',
      position: 'bottom',
    });
    await toast.present();
  }

  public startDayRouteInGoogleMaps(day: ItineraryDay): void {
    const url = buildGoogleMapsDayRouteUrl(day.items || []);
    if (url) {
      window.open(url, '_blank', 'noopener,noreferrer');
    }
  }

  public openShareModal(): void {
    this.isShareModalOpen = true;
  }

  public closeShareModal(): void {
    this.isShareModalOpen = false;
  }

  public async exportIcs(): Promise<void> {
    if (!this.itinerary) return;
    const ok = downloadIcsFile(this.itinerary);
    const toast = await this.toastController.create({
      message: ok ? 'Calendar (.ics) downloaded successfully!' : 'Could not generate calendar file.',
      duration: 2500,
      position: 'top',
      color: ok ? 'success' : 'warning',
    });
    await toast.present();
    this.closeShareModal();
  }

  public async copySummary(): Promise<void> {
    if (!this.itinerary) return;
    const ok = await copyTextSummary(this.itinerary);
    const toast = await this.toastController.create({
      message: ok ? 'Itinerary text summary copied to clipboard!' : 'Unable to copy text summary.',
      duration: 2500,
      position: 'top',
      color: ok ? 'success' : 'warning',
    });
    await toast.present();
    this.closeShareModal();
  }

  public async shareNative(): Promise<void> {
    if (!this.itinerary) return;
    await shareNativeItinerary(this.itinerary);
    this.closeShareModal();
  }

  public printPdf(): void {
    this.closeShareModal();
    setTimeout(() => {
      triggerPrintItinerary();
    }, 250);
  }

  public get printDateFormatted(): string {
    return new Date().toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  }

  public onEdit(): void {
    if (this.itinerary) {
      this.router.navigate(['/custom-builder', this.itinerary.id]);
    }
  }

  public async onDelete(): Promise<void> {
    if (!this.itinerary) return;

    const alert = await this.alertController.create({
      header: 'Delete Itinerary',
      message: `Are you sure you want to delete "${this.itinerary.title}"? This cannot be undone.`,
      buttons: [
        { text: 'Cancel', role: 'cancel' },
        {
          text: 'Delete',
          role: 'destructive',
          handler: () => {
            this.itineraryService.deleteItinerary(this.itinerary!.id).subscribe({
              next: async () => {
                const toast = await this.toastController.create({
                  message: 'Itinerary deleted.',
                  duration: 2000,
                  color: 'dark',
                  position: 'top',
                });
                await toast.present();
                this.router.navigate(['/tabs/history']);
              },
            });
          },
        },
      ],
    });
    await alert.present();
  }

  // --- Embedded Leaflet Day Route Preview & Turn Tracking (Phase 25.3) ---

  public initPreviewMap(): void {
    const el =
      this.previewMapElementRef?.nativeElement ||
      document.getElementById('route-preview-map');
    if (!el || this.previewMap || !this.isBrowser) return;

    this.previewMap = L.map(el, {
      center: [15.58, 121.0],
      zoom: 11,
      zoomControl: false,
      attributionControl: false,
    });

    const tileUrl =
      environment.tileUrlTemplate ||
      'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
    L.tileLayer(tileUrl, { maxZoom: 19 }).addTo(this.previewMap);

    this.previewStopsLayer = L.layerGroup().addTo(this.previewMap);
    this.updatePreviewMap();
  }

  public updatePreviewMap(): void {
    if (!this.previewMap || !this.isBrowser) return;

    if (this.previewPolylineLayer) {
      this.previewMap.removeLayer(this.previewPolylineLayer);
      this.previewPolylineLayer = null;
    }
    if (this.previewStopsLayer) {
      this.previewStopsLayer.clearLayers();
    } else {
      this.previewStopsLayer = L.layerGroup().addTo(this.previewMap);
    }

    const day = this.currentDay;
    if (!day) return;

    const items = day.items || [];
    const stopCoords: Array<[number, number]> = [];

    items.forEach((item, idx) => {
      const lat = item.place?.latitude ?? item.custom_lat;
      const lng = item.place?.longitude ?? item.custom_lng;
      if (lat != null && lng != null) {
        stopCoords.push([lat, lng]);
        const pinIcon = L.divIcon({
          className: 'preview-stop-marker-container',
          html: `<div class="preview-stop-pin"><div class="pin-badge">${idx + 1}</div></div>`,
          iconSize: [26, 26],
          iconAnchor: [13, 13],
        });
        const marker = L.marker([lat, lng], { icon: pinIcon });
        marker.on('click', () => {
          this.openStopDetail(item);
        });
        this.previewStopsLayer?.addLayer(marker);
      }
    });

    if (day.day_overview_polyline) {
      const latlngs = decodePolyline(day.day_overview_polyline);
      this.previewPolylineLayer = L.polyline(latlngs, {
        color: '#2563eb',
        weight: 4,
        opacity: 0.88,
        lineJoin: 'round',
      }).addTo(this.previewMap);
      this.previewMap.fitBounds(this.previewPolylineLayer.getBounds(), {
        padding: [25, 25],
      });
    } else if (stopCoords.length > 1) {
      this.previewPolylineLayer = L.polyline(stopCoords, {
        color: '#94a3b8',
        weight: 3,
        dashArray: '6, 6',
      }).addTo(this.previewMap);
      this.previewMap.fitBounds(this.previewPolylineLayer.getBounds(), {
        padding: [25, 25],
      });
    } else if (stopCoords.length === 1) {
      this.previewMap.setView(stopCoords[0], 13);
    }

    setTimeout(() => {
      this.previewMap?.invalidateSize();
    }, 100);
  }

  public togglePreviewMap(): void {
    this.isPreviewMapExpanded = !this.isPreviewMapExpanded;
    if (this.isPreviewMapExpanded) {
      setTimeout(() => {
        this.previewMap?.invalidateSize();
        this.updatePreviewMap();
      }, 150);
    }
  }

  public startNavigationForActiveDay(): void {
    const day = this.currentDay;
    if (!day) return;
    this.routeTrackingService.startTracking(day);
    this.router.navigate(['/tabs/map'], {
      queryParams: {
        followRoute: 'true',
        dayNumber: day.day_number,
      },
    });
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

  private escapeHtml(text: string): string {
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  public onBack(): void {
    if (this.viewMode === 'nearby') {
      this.closeNearbyPlaces();
    } else if (typeof window !== 'undefined' && window.history.length > 1) {
      this.location.back();
    } else {
      this.router.navigate(['/tabs/history']);
    }
  }
}
