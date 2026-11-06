import {
  AfterViewInit,
  ChangeDetectorRef,
  Component,
  ElementRef,
  Inject,
  OnDestroy,
  OnInit,
  PLATFORM_ID,
  ViewChild,
} from '@angular/core';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { Subject, Subscription, debounceTime, distinctUntilChanged } from 'rxjs';
import {
  IonContent,
  IonIcon,
  IonModal,
  IonSpinner,
} from '@ionic/angular';
import { addIcons } from 'ionicons';
import {
  addOutline,
  bandageOutline,
  basketOutline,
  bedOutline,
  busOutline,
  businessOutline,
  cafeOutline,
  cardOutline,
  carOutline,
  cashOutline,
  checkmarkOutline,
  closeCircleOutline,
  closeOutline,
  cloudOfflineOutline,
  filterOutline,
  flagOutline,
  funnelOutline,
  layersOutline,
  leafOutline,
  libraryOutline,
  listOutline,
  locateOutline,
  locationOutline,
  mapOutline,
  medkitOutline,
  navigateOutline,
  optionsOutline,
  reloadOutline,
  restaurantOutline,
  searchOutline,
  shieldCheckmarkOutline,
  sparklesOutline,
  speedometerOutline,
  stopCircleOutline,
  timeOutline,
  warningOutline,
  waterOutline,
  cartOutline,
} from 'ionicons/icons';
import * as L from 'leaflet';
import 'leaflet.markercluster';

import { Municipality, Place } from '../../core/models/place.models';
import { PlaceService } from '../../core/services/place.service';
import {
  RouteTrackingService,
  RouteTrackingState,
} from '../../core/services/route-tracking.service';
import { PlaceDetailSheetComponent } from '../../shared/components/place-detail-sheet/place-detail-sheet.component';
import { ItineraryDay, ItineraryItem } from '../../core/models/itinerary.models';
import { decodePolyline } from '../../core/utils/polyline.util';
import { environment } from '../../../environments/environment';

export interface CategoryFilterItem {
  key: string | null;
  label: string;
  icon: string;
}

export const CATEGORY_FILTERS: CategoryFilterItem[] = [
  { key: null, label: 'All Places', icon: 'layers-outline' },
  { key: 'tourist_attraction', label: 'Attractions', icon: 'sparkles-outline' },
  { key: 'nature_park', label: 'Nature & Parks', icon: 'leaf-outline' },
  { key: 'resort_swimming', label: 'Resorts & Pools', icon: 'water-outline' },
  { key: 'hotel_accommodation', label: 'Hotels & Stays', icon: 'bed-outline' },
  { key: 'restaurant', label: 'Restaurants', icon: 'restaurant-outline' },
  { key: 'cafe', label: 'Cafes & Coffee', icon: 'cafe-outline' },
  { key: 'church_religious', label: 'Churches & Faith', icon: 'business-outline' },
  { key: 'museum_cultural', label: 'Museums & Culture', icon: 'library-outline' },
  { key: 'shopping_market', label: 'Markets & Shops', icon: 'cart-outline' },
  { key: 'transport_terminal', label: 'Transit & Terminals', icon: 'bus-outline' },
  { key: 'convenience_store', label: 'Convenience', icon: 'basket-outline' },
  { key: 'hospital_clinic', label: 'Hospitals & Clinics', icon: 'medkit-outline' },
  { key: 'pharmacy', label: 'Pharmacies', icon: 'bandage-outline' },
  { key: 'bank_atm', label: 'Banks & ATMs', icon: 'card-outline' },
  { key: 'fuel_station', label: 'Fuel Stations', icon: 'car-outline' },
  { key: 'public_facility', label: 'Public Facilities', icon: 'flag-outline' },
];

export const NUEVA_ECIJA_MUNICIPALITIES: string[] = [
  'Aliaga', 'Bongabon', 'Cabanatuan City', 'Cabiao', 'Carranglan', 'Cuyapo',
  'Gabaldon', 'Gapan City', 'General Mamerto Natividad', 'General Tinio', 'Guimba',
  'Jaen', 'Laur', 'Licab', 'Llanera', 'Lupao', 'Nampicuan', 'Palayan City',
  'Pantabangan', 'Peñaranda', 'Quezon', 'Rizal', 'San Antonio', 'San Isidro',
  'San Jose City', 'San Leonardo', 'Santa Rosa', 'Santo Domingo', 'Science City of Muñoz',
  'Talavera', 'Talugtug', 'Zaragoza'
];

export const NUEVA_ECIJA_CENTER: [number, number] = [15.58, 121.0];
export const NUEVA_ECIJA_DEFAULT_ZOOM = 10;
export const NUEVA_ECIJA_BOUNDS: [[number, number], [number, number]] = [
  [15.05, 120.55],
  [16.25, 121.55],
];

@Component({
  selector: 'app-map',
  templateUrl: './map.page.html',
  styleUrls: ['./map.page.scss'],
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    IonContent,
    IonIcon,
    IonModal,
    IonSpinner,
    PlaceDetailSheetComponent,
  ],
})
export class MapPage implements OnInit, AfterViewInit, OnDestroy {
  public map: L.Map | null = null;
  public markerCluster: L.MarkerClusterGroup | null = null;
  public places: Place[] = [];
  public selectedPlace: Place | null = null;
  public selectedCategory: string | null = null;
  public isLoading = false;
  public hasTileError = false;
  public categoryFilters: CategoryFilterItem[] = CATEGORY_FILTERS;

  // Search & Deep Multi-Select Filter Sheet State (UI-16)
  public searchQuery = '';
  public selectedCategories: Set<string> = new Set<string>();
  public selectedMunicipality: string | null = null;
  public selectedPriceTier: 'all' | 'free' | 'budget' | 'mid' = 'all';
  public isFilterSheetOpen = false;
  public activeFilterCount = 0;
  public municipalities: string[] = NUEVA_ECIJA_MUNICIPALITIES;

  // Accessible Collapsible POI List Drawer (UI-16)
  public isPoiDrawerOpen = false;

  // Route Navigation & Turn-by-Turn Tracking Layer State (Phase 25.3)
  public routePolylineLayer: L.Polyline | null = null;
  public itineraryStopsLayer: L.LayerGroup | null = null;
  public userLocationMarker: L.Marker | null = null;
  public activeTrackingState: RouteTrackingState | null = null;
  public activeRouteMode: 'browse' | 'follow' = 'browse';

  private searchSubject = new Subject<string>();
  private viewportDebounceTimer: ReturnType<typeof setTimeout> | null = null;
  private subscriptions = new Subscription();
  private pendingTarget: { lat?: number; lng?: number; destination?: string; municipality?: string } | null = null;

  @ViewChild('mapElement', { static: false }) private mapElementRef?: ElementRef<HTMLDivElement>;

  private isBrowser = false;

  constructor(
    private placeService: PlaceService,
    public routeTrackingService: RouteTrackingService,
    private route: ActivatedRoute,
    private router: Router,
    private cdr: ChangeDetectorRef,
    @Inject(PLATFORM_ID) private platformId: object
  ) {
    this.isBrowser = isPlatformBrowser(this.platformId);
    if (this.isBrowser && typeof window !== 'undefined') {
      (window as unknown as { L: unknown }).L = L;
    }
    addIcons({
      addOutline,
      bandageOutline,
      basketOutline,
      bedOutline,
      busOutline,
      businessOutline,
      cafeOutline,
      cardOutline,
      carOutline,
      cashOutline,
      checkmarkOutline,
      closeCircleOutline,
      closeOutline,
      cloudOfflineOutline,
      filterOutline,
      flagOutline,
      funnelOutline,
      layersOutline,
      leafOutline,
      libraryOutline,
      listOutline,
      locateOutline,
      locationOutline,
      mapOutline,
      medkitOutline,
      navigateOutline,
      optionsOutline,
      reloadOutline,
      restaurantOutline,
      searchOutline,
      shieldCheckmarkOutline,
      sparklesOutline,
      speedometerOutline,
      stopCircleOutline,
      timeOutline,
      warningOutline,
      waterOutline,
      cartOutline,
    });
  }

  public ngOnInit(): void {
    this.loadPlaces();
    this.loadMunicipalities();

    this.subscriptions.add(
      this.routeTrackingService.state$.subscribe((state) => {
        this.activeTrackingState = state;
        if (this.map && state.isTracking && state.activeDay) {
          if (!this.routePolylineLayer) {
            this.renderRouteOnMap(state.activeDay);
          }
          if (state.currentPosition) {
            this.updateUserLocationMarker(state.currentPosition, state.heading);
            if (this.activeRouteMode === 'follow') {
              const target = state.snappedPosition || state.currentPosition;
              this.map.panTo(target, { animate: true, duration: 0.5 });
            }
          }
        } else if (!state.isTracking && this.routePolylineLayer) {
          this.clearRouteFromMap();
        }
        this.cdr.detectChanges();
      })
    );

    this.subscriptions.add(
      this.routeTrackingService.recenter$.subscribe((pos) => {
        if (this.map) {
          this.map.flyTo(pos, 16, { duration: 0.8 });
        }
      })
    );

    this.subscriptions.add(
      this.searchSubject
        .pipe(debounceTime(300), distinctUntilChanged())
        .subscribe((q) => {
          this.searchQuery = q;
          this.loadPlaces();
        })
    );

    this.subscriptions.add(
      this.route.queryParams.subscribe((params) => {
        const lat = params['lat'] ? parseFloat(params['lat']) : undefined;
        const lng = params['lng'] ? parseFloat(params['lng']) : undefined;
        const destination = params['destination'] || undefined;
        const municipality = params['municipality'] || undefined;
        const follow = params['followRoute'] === 'true';

        if (follow) {
          this.activeRouteMode = 'follow';
          const day = this.routeTrackingService.currentState.activeDay;
          if (day && this.map) {
            this.renderRouteOnMap(day);
          }
        }

        if (lat !== undefined && lng !== undefined) {
          this.pendingTarget = { lat, lng, destination, municipality };
          this.flyToTarget(lat, lng);
        } else if (destination || municipality) {
          this.pendingTarget = { destination, municipality };
          this.flyToDestinationOrMunicipality(destination, municipality);
        }
      })
    );
  }

  public ngAfterViewInit(): void {
    if (this.isBrowser) {
      setTimeout(() => {
        this.initMap();
      }, 100);
    }
  }

  public ionViewDidEnter(): void {
    if (this.isBrowser) {
      if (!this.map) {
        this.initMap();
      } else {
        setTimeout(() => {
          this.map?.invalidateSize();
          if (this.pendingTarget?.lat !== undefined && this.pendingTarget?.lng !== undefined) {
            this.flyToTarget(this.pendingTarget.lat, this.pendingTarget.lng);
          } else if (this.pendingTarget?.destination || this.pendingTarget?.municipality) {
            this.flyToDestinationOrMunicipality(this.pendingTarget.destination, this.pendingTarget.municipality);
          }
        }, 150);
      }
    }
  }

  public ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
    this.clearRouteFromMap();
    if (this.viewportDebounceTimer) {
      clearTimeout(this.viewportDebounceTimer);
      this.viewportDebounceTimer = null;
    }
    if (this.markerCluster) {
      this.markerCluster.clearLayers();
      this.markerCluster = null;
    }
    if (this.map) {
      if (typeof this.map.remove === 'function') {
        this.map.remove();
      }
      this.map = null;
    }
  }

  /**
   * Initializes the Leaflet map, OpenStreetMap tiles, and marker cluster group.
   */
  public initMap(): void {
    const mapElement =
      this.mapElementRef?.nativeElement || document.getElementById('leaflet-map');
    if (!mapElement || this.map) {
      return;
    }

    const maxBounds = L.latLngBounds(
      NUEVA_ECIJA_BOUNDS[0],
      NUEVA_ECIJA_BOUNDS[1]
    );

    this.map = L.map(mapElement, {
      center: NUEVA_ECIJA_CENTER,
      zoom: NUEVA_ECIJA_DEFAULT_ZOOM,
      minZoom: 9,
      maxZoom: 18,
      maxBounds: maxBounds,
      maxBoundsViscosity: 0.8,
      zoomControl: false,
    });

    // Add zoom controls positioned bottom-right
    L.control
      .zoom({
        position: 'bottomright',
      })
      .addTo(this.map);

    // OpenStreetMap Raster Tile Layer with attribution
    const tileUrl =
      environment.tileUrlTemplate ||
      'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
    const attribution =
      environment.tileAttribution ||
      '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors';

    const tileLayer = L.tileLayer(tileUrl, {
      attribution: attribution,
      maxZoom: 19,
    });
    tileLayer.on('tileerror', () => {
      if (!this.hasTileError) {
        this.hasTileError = true;
        this.cdr.detectChanges();
      }
    });
    tileLayer.addTo(this.map);

    // MarkerClusterGroup
    this.markerCluster = (L as unknown as { markerClusterGroup: (opts?: unknown) => L.MarkerClusterGroup }).markerClusterGroup({
      showCoverageOnHover: false,
      maxClusterRadius: 40,
      spiderfyOnMaxZoom: true,
      chunkedLoading: true,
    });

    this.map.addLayer(this.markerCluster);

    // Clicking map background dismisses bottom sheet
    this.map.on('click', () => {
      if (this.selectedPlace) {
        this.selectedPlace = null;
        this.cdr.detectChanges();
      }
    });

    // Viewport-bounded POI querying on map pan/zoom (UI-17)
    this.map.on('moveend', () => {
      this.onMapMoveEnd();
    });

    // Render any places already loaded
    if (this.places.length > 0) {
      this.updateMarkers();
    }

    if (this.activeTrackingState?.isTracking && this.activeTrackingState.activeDay) {
      this.renderRouteOnMap(this.activeTrackingState.activeDay);
    }
  }

  /**
   * Listen to Leaflet moveend (debounced 350ms) to dynamically query viewport bounds (UI-17).
   */
  public onMapMoveEnd(): void {
    if (this.viewportDebounceTimer) {
      clearTimeout(this.viewportDebounceTimer);
    }
    this.viewportDebounceTimer = setTimeout(() => {
      if (this.map && this.map.getZoom() >= 10) {
        const bounds = this.map.getBounds();
        this.loadPlaces(bounds);
      }
    }, 350);
  }

  private loadMunicipalities(): void {
    this.placeService.getMunicipalities().subscribe({
      next: (munis: Municipality[]) => {
        if (munis && munis.length > 0) {
          const names = munis.map((m) => m.name).sort();
          this.municipalities = Array.from(new Set(names));
          this.cdr.detectChanges();
        }
      },
      error: () => {
        // Fall back to statically curated NUEVA_ECIJA_MUNICIPALITIES
        this.municipalities = NUEVA_ECIJA_MUNICIPALITIES;
      },
    });
  }

  /**
   * Fetches places matching the active filters & optional viewport bounds with graceful offline fallback.
   */
  public loadPlaces(bounds?: L.LatLngBounds): void {
    this.isLoading = true;

    const searchParams: {
      q?: string;
      categories?: string[];
      min_lat?: number;
      max_lat?: number;
      min_lng?: number;
      max_lng?: number;
      limit?: number;
    } = {};

    if (this.searchQuery && this.searchQuery.trim().length > 0) {
      searchParams.q = this.searchQuery.trim();
    }

    if (this.selectedCategories.size > 0) {
      searchParams.categories = Array.from(this.selectedCategories);
    } else if (this.selectedCategory) {
      searchParams.categories = [this.selectedCategory];
    }

    if (bounds) {
      searchParams.min_lat = bounds.getSouth();
      searchParams.max_lat = bounds.getNorth();
      searchParams.min_lng = bounds.getWest();
      searchParams.max_lng = bounds.getEast();
      searchParams.limit = 150;
    } else {
      searchParams.limit = 100;
    }

    this.placeService.searchPlaces(searchParams).subscribe({
      next: (result) => {
        const items = result.items || [];
        this.places = this.applyLocalFilters(items);
        this.isLoading = false;
        this.updateMarkers();
        if (this.pendingTarget?.lat !== undefined && this.pendingTarget?.lng !== undefined) {
          this.flyToTarget(this.pendingTarget.lat, this.pendingTarget.lng);
        } else if (this.pendingTarget?.destination || this.pendingTarget?.municipality) {
          this.flyToDestinationOrMunicipality(this.pendingTarget.destination, this.pendingTarget.municipality);
        }
        this.cdr.detectChanges();
      },
      error: () => {
        // Fallback to featured places if local server is unreachable
        this.placeService.getFeaturedPlaces(50).subscribe({
          next: (featured) => {
            let items = featured;
            if (this.selectedCategories.size > 0) {
              items = items.filter((p) => this.selectedCategories.has(p.category));
            } else if (this.selectedCategory) {
              items = items.filter((p) => p.category === this.selectedCategory);
            }
            if (this.searchQuery && this.searchQuery.trim()) {
              const q = this.searchQuery.trim().toLowerCase();
              items = items.filter(
                (p) =>
                  p.name.toLowerCase().includes(q) ||
                  (p.municipality_name && p.municipality_name.toLowerCase().includes(q))
              );
            }
            this.places = this.applyLocalFilters(items);
            this.isLoading = false;
            this.updateMarkers();
            this.cdr.detectChanges();
          },
          error: () => {
            this.isLoading = false;
            this.cdr.detectChanges();
          },
        });
      },
    });
  }

  private applyLocalFilters(items: Place[]): Place[] {
    let result = items;

    if (this.selectedMunicipality) {
      const muniLower = this.selectedMunicipality.toLowerCase();
      result = result.filter(
        (p) => p.municipality_name && p.municipality_name.toLowerCase().includes(muniLower)
      );
    }

    if (this.selectedPriceTier !== 'all') {
      if (this.selectedPriceTier === 'free') {
        result = result.filter(
          (p) => p.estimated_cost_min === 0 && p.estimated_cost_max === 0
        );
      } else if (this.selectedPriceTier === 'budget') {
        result = result.filter(
          (p) =>
            (p.estimated_cost_max != null && p.estimated_cost_max <= 500) ||
            (p.estimated_cost_min === 0 && p.estimated_cost_max == null)
        );
      } else if (this.selectedPriceTier === 'mid') {
        result = result.filter(
          (p) =>
            (p.estimated_cost_max != null && p.estimated_cost_max > 500) ||
            (p.estimated_cost_min != null && p.estimated_cost_min > 500)
        );
      }
    }

    return result;
  }

  /**
   * Replaces cluster pins with current places list using custom vector pins.
   */
  public updateMarkers(): void {
    if (!this.markerCluster) {
      return;
    }

    this.markerCluster.clearLayers();

    for (const place of this.places) {
      if (typeof place.latitude !== 'number' || typeof place.longitude !== 'number') {
        continue;
      }

      const isFeatured = place.is_featured;
      const safeName = this.escapeHtml(place.name);
      const safeMuni = this.escapeHtml(place.municipality_name || 'Nueva Ecija');
      const customPin = L.divIcon({
        className: 'custom-map-pin-container',
        html: `
          <div
            class="custom-map-pin ${isFeatured ? 'pin-featured' : ''}"
            tabindex="0"
            role="button"
            aria-label="${safeName}, ${safeMuni}"
            title="${safeName}"
          >
            <div class="pin-marker">
              <div class="pin-inner"></div>
            </div>
          </div>
        `,
        iconSize: [30, 30],
        iconAnchor: [15, 30],
        popupAnchor: [0, -30],
      });

      const marker = L.marker([place.latitude, place.longitude], {
        icon: customPin,
      });

      marker.on('click', (e: L.LeafletMouseEvent) => {
        L.DomEvent.stopPropagation(e);
        this.selectedPlace = place;
        this.cdr.detectChanges();

        // Smoothly pan towards marker allowing bottom sheet room
        if (this.map) {
          this.map.panTo([place.latitude, place.longitude], {
            animate: true,
            duration: 0.5,
          });
        }
      });

      marker.on('keypress', (e: any) => {
        if (e.originalEvent?.key === 'Enter' || e.originalEvent?.key === ' ') {
          this.selectedPlace = place;
          this.cdr.detectChanges();
        }
      });

      this.markerCluster.addLayer(marker);
    }
  }

  // --- Search Input Handlers (UI-16) ---

  public onSearchInput(event: Event): void {
    const val = (event.target as HTMLInputElement).value || '';
    this.searchQuery = val;
    this.searchSubject.next(val);
  }

  public clearSearch(): void {
    this.searchQuery = '';
    this.searchSubject.next('');
  }

  // --- Quick Pill Filter Selection ---

  public selectCategory(categoryKey: string | null): void {
    if (categoryKey === null) {
      this.selectedCategory = null;
      this.selectedCategories.clear();
    } else {
      if (this.selectedCategory === categoryKey) {
        this.selectedCategory = null;
        this.selectedCategories.delete(categoryKey);
      } else {
        this.selectedCategory = categoryKey;
        this.selectedCategories = new Set([categoryKey]);
      }
    }
    this.updateActiveFilterCount();
    this.selectedPlace = null;
    this.loadPlaces();
  }

  // --- Multi-Select Filter Modal Actions (UI-16) ---

  public openFilterSheet(): void {
    this.isFilterSheetOpen = true;
  }

  public closeFilterSheet(): void {
    this.isFilterSheetOpen = false;
  }

  public toggleCategoryFilter(categoryKey: string): void {
    if (this.selectedCategories.has(categoryKey)) {
      this.selectedCategories.delete(categoryKey);
    } else {
      this.selectedCategories.add(categoryKey);
    }
    this.selectedCategory =
      this.selectedCategories.size === 1
        ? Array.from(this.selectedCategories)[0]
        : null;
    this.updateActiveFilterCount();
  }

  public isCategorySelected(categoryKey: string): boolean {
    return this.selectedCategories.has(categoryKey);
  }

  public selectMunicipality(name: string | null): void {
    this.selectedMunicipality = this.selectedMunicipality === name ? null : name;
    this.updateActiveFilterCount();
  }

  public selectPriceTier(tier: 'all' | 'free' | 'budget' | 'mid'): void {
    this.selectedPriceTier = tier;
    this.updateActiveFilterCount();
  }

  public applyFilters(): void {
    this.updateActiveFilterCount();
    this.closeFilterSheet();
    this.loadPlaces();
  }

  public resetFilters(): void {
    this.selectedCategories.clear();
    this.selectedCategory = null;
    this.selectedMunicipality = null;
    this.selectedPriceTier = 'all';
    this.updateActiveFilterCount();
    this.loadPlaces();
  }

  public updateActiveFilterCount(): void {
    let count = 0;
    if (this.selectedCategories.size > 0) {
      count += this.selectedCategories.size;
    }
    if (this.selectedMunicipality) {
      count += 1;
    }
    if (this.selectedPriceTier !== 'all') {
      count += 1;
    }
    this.activeFilterCount = count;
  }

  // --- Accessible Collapsible POI List Drawer (UI-16) ---

  public togglePoiDrawer(): void {
    this.isPoiDrawerOpen = !this.isPoiDrawerOpen;
    this.cdr.detectChanges();
  }

  public openPoiDrawer(): void {
    this.isPoiDrawerOpen = true;
    this.cdr.detectChanges();
  }

  public closePoiDrawer(): void {
    this.isPoiDrawerOpen = false;
    this.cdr.detectChanges();
  }

  public selectPlaceFromDrawer(place: Place): void {
    this.selectedPlace = place;
    this.isPoiDrawerOpen = false;
    if (typeof place.latitude === 'number' && typeof place.longitude === 'number') {
      this.flyToTarget(place.latitude, place.longitude);
    }
    this.cdr.detectChanges();
  }

  // --- Bottom Sheet Itinerary Integration Actions (UI-17) ---

  public startTripHere(place: Place): void {
    this.router.navigate(['/suggested-wizard'], {
      queryParams: {
        destination: place.municipality_name || place.name,
        placeId: place.id,
      },
    });
  }

  public addToCustomTrip(place: Place): void {
    this.router.navigate(['/custom-builder'], {
      queryParams: {
        destination: place.municipality_name || place.name,
        addPlaceId: place.id,
      },
    });
  }

  /**
   * Smoothly pans back to Nueva Ecija overview.
   */
  public recenterMap(): void {
    if (this.map) {
      this.map.flyTo(NUEVA_ECIJA_CENTER, NUEVA_ECIJA_DEFAULT_ZOOM, {
        duration: 0.8,
      });
    }
  }

  /**
   * Closes the active bottom sheet.
   */
  public closeBottomSheet(): void {
    this.selectedPlace = null;
    this.cdr.detectChanges();
  }

  /**
   * Generates keyless Google Maps directions handoff URL.
   */
  public getDirectionsUrl(place: Place): string {
    if (place.directions_url && place.directions_url.trim().length > 0) {
      return place.directions_url;
    }
    return `https://www.google.com/maps/dir/?api=1&destination=${place.latitude},${place.longitude}`;
  }

  /**
   * Formats cost range honestly without treating null as zero.
   */
  public formatCost(place: Place): string {
    const min = place.estimated_cost_min;
    const max = place.estimated_cost_max;
    if (min != null && max != null) {
      if (min === 0 && max === 0) {
        return 'Free Admission (₱0)';
      }
      return `₱${min} - ₱${max}`;
    }
    if (min != null) {
      return min === 0 ? 'Free Admission (₱0)' : `From ₱${min}`;
    }
    if (max != null) {
      return `Up to ₱${max}`;
    }
    return 'Fee: Not verified / Not provided';
  }

  private flyToTarget(lat: number, lng: number): void {
    if (this.map && !isNaN(lat) && !isNaN(lng)) {
      this.map.flyTo([lat, lng], 14, { duration: 1.0 });
    }
  }

  private flyToDestinationOrMunicipality(destination?: string, municipality?: string): void {
    if (!this.places || this.places.length === 0) {
      return;
    }
    let matchedPlace: Place | undefined;
    if (destination) {
      const lower = destination.toLowerCase();
      matchedPlace = this.places.find((p) => p.name.toLowerCase().includes(lower));
    }
    if (!matchedPlace && municipality) {
      const lowerMuni = municipality.toLowerCase();
      matchedPlace = this.places.find((p) =>
        p.municipality_name?.toLowerCase().includes(lowerMuni)
      );
    }
    if (matchedPlace && typeof matchedPlace.latitude === 'number' && typeof matchedPlace.longitude === 'number') {
      this.selectedPlace = matchedPlace;
      this.flyToTarget(matchedPlace.latitude, matchedPlace.longitude);
      this.cdr.detectChanges();
    }
  }

  public formatCategory(categoryKey: string): string {
    return this.placeService.formatCategoryName(categoryKey);
  }

  public getPlaceImageUrl(place: Place): string {
    return this.placeService.getPlaceImage(place.name, place.image_url);
  }

  // --- Active Route & Turn Tracking Actions (Phase 25.3) ---

  public toggleRouteMode(): void {
    this.activeRouteMode = this.activeRouteMode === 'follow' ? 'browse' : 'follow';
    if (this.activeRouteMode === 'follow') {
      const pos =
        this.activeTrackingState?.snappedPosition ||
        this.activeTrackingState?.currentPosition;
      if (pos && this.map) {
        this.map.flyTo(pos, 16, { duration: 0.6 });
      } else if (this.routePolylineLayer && this.map) {
        this.map.fitBounds(this.routePolylineLayer.getBounds(), { padding: [40, 40] });
      }
    }
    this.cdr.detectChanges();
  }

  public recenterUserLocation(): void {
    const pos = this.activeTrackingState?.currentPosition;
    if (pos && this.map) {
      this.map.flyTo(pos, 16, { duration: 0.8 });
    }
  }

  public stopRouteTracking(): void {
    this.routeTrackingService.stopTracking();
    this.clearRouteFromMap();
    this.activeRouteMode = 'browse';
    this.cdr.detectChanges();
  }

  public renderRouteOnMap(day: ItineraryDay): void {
    if (!this.map) return;

    this.clearRouteFromMap();
    this.itineraryStopsLayer = L.layerGroup().addTo(this.map);

    if (day.day_overview_polyline) {
      const latlngs = decodePolyline(day.day_overview_polyline);
      this.routePolylineLayer = L.polyline(latlngs, {
        color: '#2563eb',
        weight: 5,
        opacity: 0.88,
        lineJoin: 'round',
      }).addTo(this.map);

      this.map.fitBounds(this.routePolylineLayer.getBounds(), {
        padding: [50, 50],
      });
    }

    const items = day.items || [];
    items.forEach((item, idx) => {
      const lat = item.place?.latitude ?? item.custom_lat;
      const lng = item.place?.longitude ?? item.custom_lng;
      if (lat == null || lng == null) return;

      const stopTitle = this.escapeHtml(item.place?.name || item.custom_title || `Stop ${idx + 1}`);
      const stopIcon = L.divIcon({
        className: 'route-stop-marker-container',
        html: `
          <div class="route-stop-pin" role="button" aria-label="Stop ${idx + 1}: ${stopTitle}">
            <div class="route-stop-badge">${idx + 1}</div>
            <div class="route-stop-tooltip">${stopTitle}</div>
          </div>
        `,
        iconSize: [32, 32],
        iconAnchor: [16, 16],
      });

      const marker = L.marker([lat, lng], { icon: stopIcon });
      marker.on('click', (e: L.LeafletMouseEvent) => {
        L.DomEvent.stopPropagation(e);
        if (item.place) {
          this.selectedPlace = item.place;
          this.cdr.detectChanges();
        }
      });

      this.itineraryStopsLayer?.addLayer(marker);
    });

    if (this.activeTrackingState?.currentPosition) {
      this.updateUserLocationMarker(
        this.activeTrackingState.currentPosition,
        this.activeTrackingState.heading
      );
    }
  }

  public clearRouteFromMap(): void {
    if (this.routePolylineLayer && this.map) {
      this.map.removeLayer(this.routePolylineLayer);
      this.routePolylineLayer = null;
    }
    if (this.itineraryStopsLayer && this.map) {
      this.itineraryStopsLayer.clearLayers();
      this.map.removeLayer(this.itineraryStopsLayer);
      this.itineraryStopsLayer = null;
    }
    if (this.userLocationMarker && this.map) {
      this.map.removeLayer(this.userLocationMarker);
      this.userLocationMarker = null;
    }
  }

  public updateUserLocationMarker(pos: [number, number], heading: number | null): void {
    if (!this.map) return;

    const headingHtml =
      heading != null
        ? `<div class="user-heading-pointer" style="transform: rotate(${heading}deg);"></div>`
        : '';

    const userIcon = L.divIcon({
      className: 'user-location-marker-container',
      html: `
        <div class="user-pulse-marker">
          <div class="pulse-beacon"></div>
          <div class="pulse-core"></div>
          ${headingHtml}
        </div>
      `,
      iconSize: [28, 28],
      iconAnchor: [14, 14],
    });

    if (!this.userLocationMarker) {
      this.userLocationMarker = L.marker(pos, { icon: userIcon, zIndexOffset: 1000 }).addTo(this.map);
    } else {
      this.userLocationMarker.setLatLng(pos);
      this.userLocationMarker.setIcon(userIcon);
    }
  }

  public formatMetersToKm(meters: number | null | undefined): string {
    if (meters == null) return '0 m';
    if (meters < 1000) return `${Math.round(meters)} m`;
    return `${(meters / 1000).toFixed(1)} km`;
  }

  public formatEtaSeconds(seconds: number | null | undefined): string {
    if (seconds == null) return '--';
    if (seconds < 60) return `${seconds}s`;
    const mins = Math.round(seconds / 60);
    if (mins < 60) return `${mins} min`;
    const hrs = Math.floor(mins / 60);
    const remMins = mins % 60;
    return `${hrs}h ${remMins}m`;
  }

  public getStopDisplayName(item: ItineraryItem | null | undefined): string {
    if (!item) return 'Route Destination';
    return item.place?.name || item.custom_title || 'Next Waypoint';
  }

  private escapeHtml(text: string): string {
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
}
