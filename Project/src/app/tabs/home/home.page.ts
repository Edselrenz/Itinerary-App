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
  checkmarkDoneOutline,
  closeCircle,
  closeOutline,
  compassOutline,
  informationCircle,
  leafOutline,
  locationOutline,
  mapOutline,
  navigateOutline,
  notifications,
  openOutline,
  personCircleOutline,
  searchOutline,
  shieldCheckmarkOutline,
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
import { toLocalIsoDate } from '../../core/utils/date.utils';

export interface TravelNotification {
  id: string;
  type: 'trip' | 'advisory' | 'sync';
  title: string;
  message: string;
  timestamp: string;
  icon: string;
  colorClass: 'blue' | 'amber' | 'green' | 'teal';
  itineraryId?: string;
  isRead: boolean;
}

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
  public isNotificationsDrawerOpen = false;
  public notificationsList: TravelNotification[] = [];
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
      leafOutline,
      shieldCheckmarkOutline,
      checkmarkDoneOutline,
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
        this.buildNotifications(this.savedItineraries);
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
                items: localMatches.map((item) => {
                  let lat = 15.48;
                  let lng = 120.97;
                  if (item.directionsUrl) {
                    const match = item.directionsUrl.match(/destination=(-?\d+\.?\d*),(-?\d+\.?\d*)/);
                    if (match) {
                      lat = parseFloat(match[1]);
                      lng = parseFloat(match[2]);
                    }
                  }
                  return {
                    id: item.id,
                    name: item.name,
                    category: item.categoryKey,
                    latitude: lat,
                    longitude: lng,
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
                  } as Place;
                }),
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

  public get unreadNotificationCount(): number {
    return this.notificationsList.filter((n) => !n.isRead).length;
  }

  public onNotificationClick(): void {
    this.isNotificationsDrawerOpen = true;
  }

  public closeNotificationsDrawer(): void {
    this.isNotificationsDrawerOpen = false;
  }

  public markAllNotificationsAsRead(): void {
    this.notificationsList.forEach((n) => (n.isRead = true));
  }

  public openNotificationTrip(notif: TravelNotification): void {
    if (notif.itineraryId) {
      notif.isRead = true;
      this.closeNotificationsDrawer();
      this.router.navigate(['/itinerary', notif.itineraryId]);
    }
  }

  public buildNotifications(itineraries: Itinerary[]): void {
    const list: TravelNotification[] = [];
    const today = toLocalIsoDate();

    // 1. Upcoming Trips Alerts
    const upcomingTrips = (itineraries || []).filter((itin) => {
      const endOrStart = (itin.end_date || itin.start_date || '').split('T')[0];
      return endOrStart >= today;
    });

    for (const trip of upcomingTrips) {
      list.push({
        id: `trip-${trip.id}`,
        type: 'trip',
        title: `Upcoming: ${trip.title}`,
        message: `Your trip to ${trip.destination} is coming up on ${trip.start_date}. Review your stops and commute notes.`,
        timestamp: trip.start_date,
        icon: 'calendar-outline',
        colorClass: 'blue',
        itineraryId: trip.id,
        isRead: false,
      });
    }

    // 2. Provincial Travel Advisories
    list.push({
      id: 'adv-minalungao',
      type: 'advisory',
      title: 'Minalungao River Rafting Active',
      message: 'Optimal conditions for limestone river cruising and bamboo rafting are now active in General Tinio.',
      timestamp: 'Season Tip',
      icon: 'leaf-outline',
      colorClass: 'teal',
      isRead: false,
    });

    list.push({
      id: 'adv-transit',
      type: 'advisory',
      title: 'Provincial UV Express Notice',
      message: 'UV Express vans depart hourly from Cabanatuan Central Terminal to Bongabon and Gapan City.',
      timestamp: 'Transit Advisory',
      icon: 'information-circle',
      colorClass: 'amber',
      isRead: false,
    });

    list.push({
      id: 'adv-sync',
      type: 'sync',
      title: 'Cloudflare Worker Sync Active',
      message: 'Permanent cloud API proxy is connected. Offline places and itineraries remain accessible.',
      timestamp: 'System',
      icon: 'shield-checkmark-outline',
      colorClass: 'green',
      isRead: true,
    });

    this.notificationsList = list;
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
      placeId: destination.id,
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
