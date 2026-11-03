import { Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormControl, FormsModule, ReactiveFormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import {
  IonButton,
  IonContent,
  IonIcon,
  IonModal,
  IonSpinner,
  ToastController,
} from '@ionic/angular';
import { addIcons } from 'ionicons';
import {
  arrowBackOutline,
  arrowForward,
  calendarOutline,
  cashOutline,
  closeCircle,
  closeOutline,
  compassOutline,
  informationCircle,
  locationOutline,
  mapOutline,
  navigateOutline,
  notifications,
  openOutline,
  personCircleOutline,
  searchOutline,
  sparkles,
  timeOutline,
} from 'ionicons/icons';
import { Subscription, catchError, debounceTime, distinctUntilChanged, finalize, of, switchMap, tap } from 'rxjs';
import { GuestItinerary, GuestStorageService } from '../../core/services/guest-storage.service';
import { PlaceService } from '../../core/services/place.service';
import { Place } from '../../core/models/place.models';
import { Itinerary } from '../../core/models/itinerary.models';
import { ItineraryService } from '../../core/services/itinerary.service';
import { getOfflineDestinationsForHome } from '../../core/data/offline-places.data';

export interface DestinationItem {
  id: string;
  name: string;
  municipality: string;
  category: string;
  categoryKey: string;
  image: string;
  description: string;
  tags: string[];
  searchQuery: string;
  directionsUrl: string;
  openingHours?: string | null;
  costDisplay: string;
}

@Component({
  selector: 'app-home',
  templateUrl: './home.page.html',
  styleUrls: ['./home.page.scss'],
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    RouterLink,
    IonContent,
    IonButton,
    IonIcon,
    IonModal,
    IonSpinner,
  ],
})
export class HomePage implements OnInit, OnDestroy {
  public isGuestMode = false;
  public searchControl = new FormControl('');
  public selectedDestination: DestinationItem | null = null;
  public isDetailModalOpen = false;

  public isPopularCatalogOpen = false;
  public selectedCatalogMunicipality = 'All';
  public catalogMunicipalities: string[] = [
    'All',
    'Bongabon',
    'Pantabangan',
    'Gapan City',
    'General Tinio',
    'Cabanatuan City',
    'Science City of Muñoz',
    'Gabaldon',
  ];

  public searchResults: DestinationItem[] = [];
  public isSearching = false;
  public searchLoading = false;

  public savedItineraries: Itinerary[] = [];

  private subscriptions = new Subscription();

  // Curated fallback destinations from canonical offline places dataset (DEF-05)
  public destinations: DestinationItem[] = getOfflineDestinationsForHome();

  constructor(
    private guestStorage: GuestStorageService,
    private itineraryService: ItineraryService,
    private placeService: PlaceService,
    private router: Router,
    private toastController: ToastController
  ) {
    addIcons({
      arrowBackOutline,
      notifications,
      personCircleOutline,
      informationCircle,
      sparkles,
      mapOutline,
      arrowForward,
      searchOutline,
      closeCircle,
      closeOutline,
      locationOutline,
      calendarOutline,
      compassOutline,
      navigateOutline,
      openOutline,
      timeOutline,
      cashOutline,
    });
  }

  public ngOnInit(): void {
    // 1. Subscribe to Guest Mode state
    this.subscriptions.add(
      this.guestStorage.isGuestMode$.subscribe((mode) => {
        this.isGuestMode = mode;
      })
    );

    // 2. Subscribe to Saved Itineraries (Dual-mode: Backend + Guest fallback)
    this.subscriptions.add(
      this.itineraryService.itineraries$.subscribe((items) => {
        this.savedItineraries = items || [];
      })
    );

    // 3. Fetch Curated Featured Places from Backend
    this.loadFeaturedPlaces();

    // 4. Setup 300ms Debounced Local Search via RxJS switchMap
    this.setupSearchPipeline();
  }

  public ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
  }

  private loadFeaturedPlaces(): void {
    this.placeService.getFeaturedPlaces(20).subscribe({
      next: (places) => {
        if (places && places.length > 0) {
          this.destinations = places.map((p) => this.mapPlaceToDestination(p));
        }
      },
      error: () => {
        // Retain verified fallback destinations if backend is not currently running
      },
    });
  }

  private setupSearchPipeline(): void {
    const searchSub = this.searchControl.valueChanges
      .pipe(
        debounceTime(300),
        distinctUntilChanged(),
        tap((term) => {
          const trimmed = (term || '').trim();
          this.isSearching = trimmed.length > 0;
          if (!this.isSearching) {
            this.searchResults = [];
            this.searchLoading = false;
          }
        }),
        switchMap((term) => {
          const trimmed = (term || '').trim();
          if (!trimmed) {
            return of(null);
          }
          this.searchLoading = true;
          return this.placeService.searchPlaces({ q: trimmed, limit: 20 }).pipe(
            catchError(() => {
              // Graceful local search fallback for offline resilience
              const localMatches = this.destinations.filter(
                (d) =>
                  d.name.toLowerCase().includes(trimmed.toLowerCase()) ||
                  d.municipality.toLowerCase().includes(trimmed.toLowerCase()) ||
                  d.category.toLowerCase().includes(trimmed.toLowerCase()) ||
                  d.tags.some((tag) => tag.toLowerCase().includes(trimmed.toLowerCase()))
              );
              return of({
                total: localMatches.length,
                limit: 20,
                offset: 0,
                items: localMatches.map((item) => ({
                  id: item.id,
                  name: item.name,
                  category: item.categoryKey,
                  latitude: 15.48,
                  longitude: 120.97,
                  municipality_name: item.municipality,
                  address_text: `${item.municipality}, Nueva Ecija`,
                  description: item.description,
                  cost_currency: 'PHP',
                  source_name: 'Fallback',
                  source_record_id: item.id,
                  imported_at: new Date().toISOString(),
                  is_featured: true,
                  tags: item.tags,
                  directions_url: item.directionsUrl,
                } as Place)),
              });
            }),
            finalize(() => {
              this.searchLoading = false;
            })
          );
        })
      )
      .subscribe((response) => {
        if (response) {
          this.searchResults = response.items.map((p) => this.mapPlaceToDestination(p));
        }
      });

    this.subscriptions.add(searchSub);
  }

  public mapPlaceToDestination(place: Place): DestinationItem {
    let costDisplay = 'Cost not provided';
    if (place.estimated_cost_min !== null && place.estimated_cost_min !== undefined) {
      if (
        place.estimated_cost_max !== null &&
        place.estimated_cost_max !== undefined &&
        place.estimated_cost_max > place.estimated_cost_min
      ) {
        costDisplay = `₱${Math.round(place.estimated_cost_min)} - ₱${Math.round(place.estimated_cost_max)}`;
      } else {
        costDisplay = `₱${Math.round(place.estimated_cost_min)}`;
      }
    }

    return {
      id: String(place.id),
      name: place.name,
      municipality: place.municipality_name || 'Nueva Ecija',
      category: this.placeService.formatCategoryName(place.category),
      categoryKey: place.category,
      image: this.placeService.getPlaceImage(place.name, place.image_url),
      description: place.description || 'Verified destination in Nueva Ecija, Central Luzon.',
      tags:
        place.tags && place.tags.length > 0
          ? place.tags
          : [this.placeService.formatCategoryName(place.category)],
      searchQuery: `${place.name} ${place.municipality_name || ''} Nueva Ecija`.trim(),
      directionsUrl:
        place.directions_url ||
        `https://www.google.com/maps/dir/?api=1&destination=${place.latitude},${place.longitude}`,
      openingHours: place.opening_hours,
      costDisplay,
    };
  }

  public async onNotificationClick(): Promise<void> {
    const toast = await this.toastController.create({
      message: "You're all caught up! No active travel alerts in Nueva Ecija.",
      duration: 2500,
      position: 'top',
      color: 'dark',
    });
    await toast.present();
  }

  public get filteredCatalogDestinations(): DestinationItem[] {
    if (this.selectedCatalogMunicipality === 'All') {
      return this.destinations;
    }
    const filter = this.selectedCatalogMunicipality.toLowerCase();
    return this.destinations.filter(
      (d) =>
        d.municipality.toLowerCase().includes(filter) ||
        filter.includes(d.municipality.toLowerCase())
    );
  }

  public filterCatalogByMunicipality(muni: string): void {
    this.selectedCatalogMunicipality = muni;
  }

  public onSeeAll(): void {
    this.isPopularCatalogOpen = true;
  }

  public closePopularCatalog(): void {
    this.isPopularCatalogOpen = false;
  }

  public clearSearch(): void {
    this.searchControl.setValue('');
  }

  public openDestinationDetail(destination: DestinationItem): void {
    this.selectedDestination = destination;
    this.isDetailModalOpen = true;
  }

  public closeDestinationDetail(): void {
    this.isDetailModalOpen = false;
    this.selectedDestination = null;
  }

  public openInGoogleMaps(destination: DestinationItem): void {
    window.open(destination.directionsUrl, '_blank');
  }

  public startPlanningWithDestination(destination: DestinationItem): void {
    this.closeDestinationDetail();
    this.closePopularCatalog();
    this.router.navigate(['/suggested-wizard'], {
      queryParams: {
        destination: destination.municipality,
        placeId: destination.id,
      },
    });
  }

  public viewDestinationOnMap(destination: DestinationItem): void {
    this.closeDestinationDetail();
    this.closePopularCatalog();
    const queryParams: Record<string, string> = {
      destination: destination.name,
      municipality: destination.municipality,
    };
    if (destination.directionsUrl) {
      const match = destination.directionsUrl.match(/destination=(-?\d+\.?\d*),(-?\d+\.?\d*)/);
      if (match) {
        queryParams['lat'] = match[1];
        queryParams['lng'] = match[2];
      }
    }
    this.router.navigate(['/tabs/map'], { queryParams });
  }

  public onSuggestedClick(): void {
    this.router.navigate(['/suggested-wizard']);
  }

  public onCustomClick(): void {
    this.router.navigate(['/custom-builder']);
  }

  public openItinerary(itinerary: Itinerary): void {
    if (itinerary.id) {
      this.router.navigate(['/itinerary', itinerary.id]);
    }
  }

  public get displayedSavedItineraries(): Itinerary[] {
    return this.savedItineraries.slice(0, 2);
  }

  public onSeeAllItineraries(): void {
    this.router.navigate(['/tabs/history']);
  }
}
