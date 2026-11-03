import { Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
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
  alertCircleOutline,
  arrowBack,
  arrowForwardOutline,
  busOutline,
  calendarOutline,
  cashOutline,
  checkmarkCircle,
  closeOutline,
  createOutline,
  informationCircle,
  informationCircleOutline,
  locationOutline,
  locationSharp,
  navigateOutline,
  openOutline,
  sparkles,
  storefrontOutline,
  timeOutline,
  trashOutline,
} from 'ionicons/icons';
import { Subscription } from 'rxjs';
import {
  Itinerary,
  ItineraryBudgetSummary,
  ItineraryDay,
  ItineraryItem,
} from '../../../core/models/itinerary.models';
import { formatDateRange } from '../../../core/utils/date.utils';
import { ItineraryService } from '../../../core/services/itinerary.service';
import { NearbyPlaceItem, PlaceService } from '../../../core/services/place.service';
import { CommuteInfo, getCommuteInfoForMunicipality } from '../../../core/data/commute-guide.data';

@Component({
  selector: 'app-itinerary-detail',
  templateUrl: './itinerary-detail.page.html',
  styleUrls: ['./itinerary-detail.page.scss'],
  standalone: true,
  imports: [
    CommonModule,
    IonContent,
    IonHeader,
    IonToolbar,
    IonIcon,
    IonSpinner,
    IonModal,
  ],
})
export class ItineraryDetailPage implements OnInit, OnDestroy {
  public itineraryId: string | null = null;
  public itinerary: Itinerary | null = null;
  public isLoading = true;
  public activeDayIndex = 0;
  public budgetSummary: ItineraryBudgetSummary | null = null;

  // View state: 'itinerary' (Overview / Day Timeline) | 'nearby' (Nearby Places)
  public viewMode: 'itinerary' | 'nearby' = 'itinerary';
  public activeNearbyTab: 'restaurants' | 'hospitals' | 'stores' = 'restaurants';
  public nearbyPlacesList: NearbyPlaceItem[] = [];

  // Stop Details Modal state
  public selectedStop: ItineraryItem | null = null;
  public isStopModalOpen = false;

  private subscriptions = new Subscription();

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private itineraryService: ItineraryService,
    public placeService: PlaceService,
    private alertController: AlertController,
    private toastController: ToastController
  ) {
    addIcons({
      addCircleOutline,
      arrowBack,
      busOutline,
      createOutline,
      trashOutline,
      locationOutline,
      locationSharp,
      calendarOutline,
      cashOutline,
      timeOutline,
      checkmarkCircle,
      closeOutline,
      informationCircle,
      informationCircleOutline,
      openOutline,
      navigateOutline,
      alertCircleOutline,
      sparkles,
      storefrontOutline,
      arrowForwardOutline,
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

  public ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
  }

  public loadItinerary(id: string): void {
    this.isLoading = true;
    this.subscriptions.add(
      this.itineraryService.getItineraryById(id).subscribe({
        next: (itin) => {
          this.itinerary = itin;
          this.activeDayIndex = 0;
          this.budgetSummary = this.itineraryService.calculateBudgetSummary(itin);
          this.refreshNearbyPlaces();
          this.isLoading = false;
        },
        error: () => {
          this.isLoading = false;
        },
      })
    );
  }

  public selectDay(index: number): void {
    this.activeDayIndex = index;
    this.refreshNearbyPlaces();
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

  public getTimingTime(stop: ItineraryItem, index?: number): string {
    if (stop.planned_time) {
      return stop.planned_time;
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

  public getCommuteInfo(stop: ItineraryItem): CommuteInfo {
    return getCommuteInfoForMunicipality(
      stop.place?.municipality_name || this.itinerary?.destination || 'Nueva Ecija',
      this.getStopTitle(stop)
    );
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
        latitude: 15.63,
        longitude: 121.14,
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
    }

    const toast = await this.toastController.create({
      message: `Added ${place.name} to Day ${currentDay.day_number}!`,
      duration: 2000,
      color: 'dark',
      position: 'bottom',
    });
    await toast.present();
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

  public onBack(): void {
    if (this.viewMode === 'nearby') {
      this.closeNearbyPlaces();
    } else {
      this.router.navigate(['/tabs/history']);
    }
  }
}
