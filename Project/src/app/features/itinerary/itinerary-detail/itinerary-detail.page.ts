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
  alertCircleOutline,
  arrowBack,
  arrowForwardOutline,
  calendarOutline,
  cashOutline,
  checkmarkCircle,
  closeOutline,
  createOutline,
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
      arrowBack,
      createOutline,
      trashOutline,
      locationOutline,
      locationSharp,
      calendarOutline,
      cashOutline,
      timeOutline,
      checkmarkCircle,
      closeOutline,
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
    return '₱ 3,000 - ₱ 5,000/day';
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
    const muni = this.getDayLocation(day);
    if (muni === 'Bongabon') {
      return 'Food spots, local culture, and historic sites!';
    }
    return `Food spots, local culture, and historic sites in ${muni}!`;
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

  public getTimingTime(stop: ItineraryItem): string {
    if (stop.planned_time) {
      return stop.planned_time;
    }
    return '12:00 PM - 2:00 PM';
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
