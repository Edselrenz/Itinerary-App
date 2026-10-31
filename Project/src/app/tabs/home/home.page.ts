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

  public searchResults: DestinationItem[] = [];
  public isSearching = false;
  public searchLoading = false;

  public savedItineraries: Itinerary[] = [];

  private subscriptions = new Subscription();

  // Curated fallback destinations to guarantee rich visual experience if backend is offline
  public destinations: DestinationItem[] = [
    {
      id: 'minalungao',
      name: 'Minalungao National Park',
      municipality: 'General Tinio',
      category: 'Nature & Adventure',
      categoryKey: 'nature_park',
      image: 'assets/images/minalungao.png',
      description: 'Towering 16-meter limestone cliffs, emerald-green Peñaranda River bamboo rafting, and subterranean caves.',
      tags: ['Balsa Rafting', 'Cliff Diving', 'Caving'],
      searchQuery: 'Minalungao National Park General Tinio Nueva Ecija',
      directionsUrl: 'https://www.google.com/maps/dir/?api=1&destination=15.2981,121.1223',
      openingHours: '07:00-17:00',
      costDisplay: '₱100 - ₱500',
    },
    {
      id: 'tagpuan_gapan',
      name: 'Tagpuan sa Lumang Gapan',
      municipality: 'Gapan City',
      category: 'Heritage & Faith',
      categoryKey: 'church_religious',
      image: 'assets/images/tagpuan_gapan.png',
      description: 'The "Little Vigan" of Nueva Ecija featuring restored Spanish colonial street lamps, historic brick facades, and night food stalls.',
      tags: ['Colonial Walk', 'Night Market', 'Historic Street'],
      searchQuery: 'Tagpuan sa Lumang Gapan Gapan City Nueva Ecija',
      directionsUrl: 'https://www.google.com/maps/dir/?api=1&destination=15.3065,120.9461',
      openingHours: '06:00-20:00',
      costDisplay: 'Cost not provided',
    },
    {
      id: 'pantabangan_lake',
      name: 'Pantabangan Dam and Lake Viewpoint',
      municipality: 'Pantabangan',
      category: 'Tourist Attraction',
      categoryKey: 'tourist_attraction',
      image: 'assets/images/pantabangan_lake.png',
      description: 'One of Southeast Asia\'s largest clean water reservoirs, framed by scenic Sierra Madre mountain ridges and bass fishing spots.',
      tags: ['Bass Fishing', 'Scenic View', 'Dam Site'],
      searchQuery: 'Pantabangan Lake Dam Pantabangan Nueva Ecija',
      directionsUrl: 'https://www.google.com/maps/dir/?api=1&destination=15.8126,121.1098',
      openingHours: '06:00-18:00',
      costDisplay: 'Cost not provided',
    },
    {
      id: 'george_point',
      name: 'George Point',
      municipality: 'Pantabangan',
      category: 'Cafe & Dining',
      categoryKey: 'cafe',
      image: 'assets/images/george_point.png',
      description: 'Scenic panoramic hilltop overlooking Pantabangan Lake, ideal for sunset views, relaxing lakeside dining, and coffee.',
      tags: ['Sunset View', 'Lakeside Coffee', 'Photography'],
      searchQuery: 'George Point Pantabangan Nueva Ecija',
      directionsUrl: 'https://www.google.com/maps/dir/?api=1&destination=15.8200,121.1150',
      openingHours: '08:00-20:00',
      costDisplay: '₱150 - ₱450',
    },
    {
      id: 'highland_bali',
      name: 'Highland Bali Villas Resort and Spa',
      municipality: 'Pantabangan',
      category: 'Resort & Stay',
      categoryKey: 'hotel_accommodation',
      image: 'assets/images/highland_bali.png',
      description: 'Balinese-inspired lakefront retreat with water sports, exotic villas, and breathtaking vistas across the water.',
      tags: ['Water Sports', 'Resort Villas', 'Spa'],
      searchQuery: 'Highland Bali Villa Resort Pantabangan Nueva Ecija',
      directionsUrl: 'https://www.google.com/maps/dir/?api=1&destination=15.8180,121.1210',
      openingHours: '24 Hours',
      costDisplay: '₱3500 - ₱8000',
    },
    {
      id: 'farm_villaronte',
      name: 'Farm Villaronte',
      municipality: 'San Jose City',
      category: 'Tourist Attraction',
      categoryKey: 'tourist_attraction',
      image: 'assets/images/farm_villaronte.png',
      description: 'Vibrant flower farm, organic produce picking, rustic pavilions, and family-friendly agro-tourism trails.',
      tags: ['Sunflower Fields', 'Organic Produce', 'Agri-Tour'],
      searchQuery: 'Farm Villaronte San Jose City Nueva Ecija',
      directionsUrl: 'https://www.google.com/maps/dir/?api=1&destination=15.7850,120.9980',
      openingHours: '08:00-17:00',
      costDisplay: '₱50 - ₱200',
    },
    {
      id: 'casa_batik',
      name: 'Casa Batik',
      municipality: 'Cabanatuan City',
      category: 'Culture & Museum',
      categoryKey: 'museum_cultural',
      image: 'assets/images/casa_batik.png',
      description: 'Artisan craft space celebrating Philippine textile traditions, local handcrafted coffee, and homegrown culinary heritage.',
      tags: ['Handcrafted Goods', 'Art Cafe', 'Local Heritage'],
      searchQuery: 'Casa Batik Cabanatuan City Nueva Ecija',
      directionsUrl: 'https://www.google.com/maps/dir/?api=1&destination=15.4850,120.9650',
      openingHours: '09:00-18:00',
      costDisplay: '₱100 - ₱300',
    },
    {
      id: 'pavillion_farm',
      name: "D' Pavilion Farm and Resort",
      municipality: 'Bongabon',
      category: 'Resort & Swimming',
      categoryKey: 'resort_swimming',
      image: 'assets/images/pavillion_farm.png',
      description: 'Sprawling eco-tourism estate in the Onion Capital with open lawns, fresh mountain breezes, and native dining.',
      tags: ['Mountain View', 'Onion Capital', 'Eco Camp'],
      searchQuery: 'Pavillion Farm Bongabon Nueva Ecija',
      directionsUrl: 'https://www.google.com/maps/dir/?api=1&destination=15.6322,121.1447',
      openingHours: '08:00-18:00',
      costDisplay: '₱150 - ₱400',
    },
    {
      id: 'lake_farm_marre',
      name: 'Lake Farm de La Marre',
      municipality: 'San Jose City',
      category: 'Resort & Stay',
      categoryKey: 'hotel_accommodation',
      image: 'assets/images/lake_farm_marre.png',
      description: 'Tranquil countryside lakefront farm estate with boating, peaceful nature retreats, and farm-to-table culinary dining.',
      tags: ['Lakeside Retreat', 'Nature Farm', 'Boating'],
      searchQuery: 'Lake Farm de La Marre San Jose City Nueva Ecija',
      directionsUrl: 'https://www.google.com/maps/dir/?api=1&destination=15.7720,120.9850',
      openingHours: '08:00-20:00',
      costDisplay: '₱500 - ₱2500',
    },
    {
      id: 'la_casa_prime',
      name: 'La Casa Prime Cabins',
      municipality: 'Bongabon',
      category: 'Resort & Stay',
      categoryKey: 'hotel_accommodation',
      image: 'assets/images/la_casa_prime.png',
      description: 'Serene mountain cabin sanctuary with overlooking views of Pantabangan Lake and modern glamping amenities.',
      tags: ['Mountain Cabins', 'Lake View', 'Glamping'],
      searchQuery: 'La Casa Prime Cabins Pantabangan Nueva Ecija',
      directionsUrl: 'https://www.google.com/maps/dir/?api=1&destination=15.6280,121.1520',
      openingHours: '24 Hours',
      costDisplay: '₱2500 - ₱6000',
    },
  ];

  constructor(
    private guestStorage: GuestStorageService,
    private itineraryService: ItineraryService,
    private placeService: PlaceService,
    private router: Router,
    private toastController: ToastController
  ) {
    addIcons({
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

  public onSeeAll(): void {
    this.router.navigate(['/tabs/map']);
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
    this.router.navigate(['/tabs/map'], {
      queryParams: { destination: destination.name, municipality: destination.municipality },
    });
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
