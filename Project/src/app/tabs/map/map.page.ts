import {
  AfterViewInit,
  ChangeDetectorRef,
  Component,
  Inject,
  OnDestroy,
  OnInit,
  PLATFORM_ID,
} from '@angular/core';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import {
  IonContent,
  IonIcon,
  IonSpinner,
} from '@ionic/angular';
import { addIcons } from 'ionicons';
import {
  bandageOutline,
  basketOutline,
  bedOutline,
  busOutline,
  businessOutline,
  cafeOutline,
  cardOutline,
  carOutline,
  cashOutline,
  closeOutline,
  flagOutline,
  layersOutline,
  leafOutline,
  libraryOutline,
  locateOutline,
  locationOutline,
  mapOutline,
  medkitOutline,
  navigateOutline,
  restaurantOutline,
  sparklesOutline,
  timeOutline,
  waterOutline,
  cartOutline,
} from 'ionicons/icons';
import * as L from 'leaflet';
import 'leaflet.markercluster';

import { Place } from '../../core/models/place.models';
import { PlaceService } from '../../core/services/place.service';
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
    IonContent,
    IonIcon,
    IonSpinner,
  ],
})
export class MapPage implements OnInit, AfterViewInit, OnDestroy {
  public map: L.Map | null = null;
  public markerCluster: L.MarkerClusterGroup | null = null;
  public places: Place[] = [];
  public selectedPlace: Place | null = null;
  public selectedCategory: string | null = null;
  public isLoading = false;
  public categoryFilters: CategoryFilterItem[] = CATEGORY_FILTERS;

  private isBrowser = false;

  constructor(
    private placeService: PlaceService,
    private cdr: ChangeDetectorRef,
    @Inject(PLATFORM_ID) private platformId: object
  ) {
    this.isBrowser = isPlatformBrowser(this.platformId);
    addIcons({
      bandageOutline,
      basketOutline,
      bedOutline,
      busOutline,
      businessOutline,
      cafeOutline,
      cardOutline,
      carOutline,
      cashOutline,
      closeOutline,
      flagOutline,
      layersOutline,
      leafOutline,
      libraryOutline,
      locateOutline,
      locationOutline,
      mapOutline,
      medkitOutline,
      navigateOutline,
      restaurantOutline,
      sparklesOutline,
      timeOutline,
      waterOutline,
      cartOutline,
    });
  }

  public ngOnInit(): void {
    this.loadPlaces();
  }

  public ngAfterViewInit(): void {
    if (this.isBrowser) {
      this.initMap();
    }
  }

  /**
   * Ionic page lifecycle hook: recalculates dimensions when navigating back to tab.
   */
  public ionViewDidEnter(): void {
    if (this.map) {
      setTimeout(() => {
        this.map?.invalidateSize();
      }, 150);
    }
  }

  public ngOnDestroy(): void {
    if (this.markerCluster) {
      this.markerCluster.clearLayers();
      this.markerCluster = null;
    }
    if (this.map) {
      this.map.remove();
      this.map = null;
    }
  }

  /**
   * Initializes the Leaflet map, OpenStreetMap tiles, and marker cluster group.
   */
  public initMap(): void {
    const mapElement = document.getElementById('leaflet-map');
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

    L.tileLayer(tileUrl, {
      attribution: attribution,
      maxZoom: 19,
    }).addTo(this.map);

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

    // Render any places already loaded
    if (this.places.length > 0) {
      this.updateMarkers();
    }
  }

  /**
   * Fetches places matching the active category filter with graceful offline fallback.
   */
  public loadPlaces(): void {
    this.isLoading = true;
    const searchParams = this.selectedCategory
      ? { categories: [this.selectedCategory], limit: 100 }
      : { limit: 100 };

    this.placeService.searchPlaces(searchParams).subscribe({
      next: (result) => {
        this.places = result.items || [];
        this.isLoading = false;
        this.updateMarkers();
        this.cdr.detectChanges();
      },
      error: () => {
        // Fallback to featured places if local server is unreachable
        this.placeService.getFeaturedPlaces(25).subscribe({
          next: (featured) => {
            this.places = this.selectedCategory
              ? featured.filter((p) => p.category === this.selectedCategory)
              : featured;
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
      const customPin = L.divIcon({
        className: 'custom-map-pin-container',
        html: `
          <div class="custom-map-pin ${isFeatured ? 'pin-featured' : ''}" title="${this.escapeHtml(place.name)}">
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

      this.markerCluster.addLayer(marker);
    }
  }

  /**
   * Toggles category filter pill selection.
   */
  public selectCategory(categoryKey: string | null): void {
    if (this.selectedCategory === categoryKey) {
      return;
    }
    this.selectedCategory = categoryKey;
    this.selectedPlace = null;
    this.loadPlaces();
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
      return `₱${min} - ₱${max}`;
    }
    if (min != null) {
      return `From ₱${min}`;
    }
    if (max != null) {
      return `Up to ₱${max}`;
    }
    return 'Cost not provided';
  }

  public formatCategory(categoryKey: string): string {
    return this.placeService.formatCategoryName(categoryKey);
  }

  public getPlaceImageUrl(place: Place): string {
    return this.placeService.getPlaceImage(place.name, place.image_url);
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
