import {
  AfterViewInit,
  Component,
  ElementRef,
  EventEmitter,
  Inject,
  Input,
  OnChanges,
  OnDestroy,
  Output,
  PLATFORM_ID,
  SimpleChanges,
  ViewChild,
} from '@angular/core';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { Router } from '@angular/router';
import * as L from 'leaflet';
import { IonIcon } from '@ionic/angular';
import { addIcons } from 'ionicons';
import {
  chevronDownOutline,
  chevronUpOutline,
  mapOutline,
  openOutline,
} from 'ionicons/icons';
import { ItineraryDay, ItineraryItem } from '../../../core/models/itinerary.models';
import { decodePolyline, generateGeodesicArc } from '../../../core/utils/polyline.util';

@Component({
  selector: 'app-itinerary-route-map',
  templateUrl: './itinerary-route-map.component.html',
  styleUrls: ['./itinerary-route-map.component.scss'],
  standalone: true,
  imports: [CommonModule, IonIcon],
})
export class ItineraryRouteMapComponent implements AfterViewInit, OnChanges, OnDestroy {
  @Input() public day: ItineraryDay | null = null;
  @Input() public itineraryId?: string | null = null;
  @Input() public isCollapsible = true;
  @Input() public mapHeight = '180px';
  @Input() public showFullRouteAction = true;

  @Output() public stopSelected = new EventEmitter<ItineraryItem>();

  @ViewChild('mapElement', { static: false }) private mapElementRef?: ElementRef<HTMLDivElement>;

  public isExpanded = true;
  public map: L.Map | null = null;
  public polylineLayer: L.Polyline | null = null;
  public stopsLayer: L.LayerGroup | null = null;
  private isBrowser = false;

  constructor(
    private router: Router,
    @Inject(PLATFORM_ID) private platformId: object
  ) {
    this.isBrowser = isPlatformBrowser(this.platformId);
    if (this.isBrowser && typeof window !== 'undefined') {
      (window as unknown as { L: unknown }).L = L;
    }
    addIcons({
      chevronDownOutline,
      chevronUpOutline,
      mapOutline,
      openOutline,
    });
  }

  public ngAfterViewInit(): void {
    if (this.isBrowser) {
      setTimeout(() => this.initOrUpdateMap(), 100);
    }
  }

  public ngOnChanges(changes: SimpleChanges): void {
    if (changes['day'] && !changes['day'].firstChange) {
      if (this.isBrowser) {
        setTimeout(() => this.initOrUpdateMap(), 50);
      }
    }
  }

  public ngOnDestroy(): void {
    if (this.map) {
      this.map.remove();
      this.map = null;
    }
  }

  public toggleExpand(): void {
    if (!this.isCollapsible) return;
    this.isExpanded = !this.isExpanded;
    if (this.isExpanded && this.isBrowser) {
      setTimeout(() => {
        this.map?.invalidateSize();
        this.fitRouteBounds();
      }, 150);
    }
  }

  public openFullRouteOnMap(): void {
    if (!this.day) return;
    this.router.navigate(['/tabs/map'], {
      queryParams: {
        followRoute: 'true',
        dayNumber: this.day.day_number,
        itineraryId: this.itineraryId || undefined,
      },
    });
  }

  public initOrUpdateMap(): void {
    if (!this.isBrowser) return;
    if (!this.map && !this.mapElementRef?.nativeElement) return;

    if (!this.map) {
      const el = this.mapElementRef!.nativeElement;
      this.map = L.map(el, {
        zoomControl: false,
        attributionControl: false,
        dragging: true,
        scrollWheelZoom: false,
        doubleClickZoom: false,
      }).setView([15.58, 121.0], 11);

      L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
        maxZoom: 19,
      }).addTo(this.map);
    }

    this.renderRoute();
  }

  private renderRoute(): void {
    if (!this.map || !this.day) return;

    // Reset layers
    if (this.polylineLayer) {
      this.map.removeLayer(this.polylineLayer);
      this.polylineLayer = null;
    }
    if (this.stopsLayer) {
      this.stopsLayer.clearLayers();
    } else {
      this.stopsLayer = L.layerGroup().addTo(this.map);
    }

    const items = this.day.items || [];
    const stopCoords: Array<[number, number]> = [];
    const fullRoutePoints: Array<[number, number]> = [];

    items.forEach((item, idx) => {
      const lat = item.place?.latitude ?? item.custom_lat;
      const lng = item.place?.longitude ?? item.custom_lng;
      if (lat != null && lng != null) {
        stopCoords.push([lat, lng]);

        // Place numbered circular pin
        const pinIcon = L.divIcon({
          className: 'preview-stop-marker-container',
          html: `<div class="preview-stop-pin" role="button" tabindex="0" aria-label="Stop ${idx + 1}: ${item.place?.name || item.custom_title || 'Stop'}">${idx + 1}</div>`,
          iconSize: [26, 26],
          iconAnchor: [13, 13],
        });

        const marker = L.marker([lat, lng], { icon: pinIcon });
        marker.on('click', () => {
          this.stopSelected.emit(item);
        });
        marker.addTo(this.stopsLayer!);

        // Polyline segments
        if (item.route_polyline_from_prev) {
          try {
            const decoded = decodePolyline(item.route_polyline_from_prev);
            if (decoded.length > 0) {
              fullRoutePoints.push(...decoded);
            }
          } catch {
            fullRoutePoints.push([lat, lng]);
          }
        } else if (stopCoords.length > 1) {
          const prevCoord = stopCoords[stopCoords.length - 2];
          const arc = generateGeodesicArc(prevCoord, [lat, lng]);
          fullRoutePoints.push(...arc);
        } else {
          fullRoutePoints.push([lat, lng]);
        }
      }
    });

    const routeToDraw = fullRoutePoints.length > 1 ? fullRoutePoints : stopCoords;
    if (routeToDraw.length > 1) {
      this.polylineLayer = L.polyline(routeToDraw, {
        color: '#2563eb',
        weight: 4,
        opacity: 0.85,
        lineJoin: 'round',
      }).addTo(this.map);
    }

    this.fitRouteBounds(stopCoords);
  }

  private fitRouteBounds(coords?: Array<[number, number]>): void {
    if (!this.map) return;
    const items = this.day?.items || [];
    const stopCoords =
      coords ||
      items
        .map((it) => {
          const lat = it.place?.latitude ?? it.custom_lat;
          const lng = it.place?.longitude ?? it.custom_lng;
          return lat != null && lng != null ? ([lat, lng] as [number, number]) : null;
        })
        .filter((c): c is [number, number] => c != null);

    if (stopCoords.length >= 2) {
      const bounds = L.latLngBounds(stopCoords);
      this.map.fitBounds(bounds, { padding: [24, 24] });
    } else if (stopCoords.length === 1) {
      this.map.setView(stopCoords[0], 14);
    }
  }
}
