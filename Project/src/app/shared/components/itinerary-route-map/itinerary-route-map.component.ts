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
import { environment } from '../../../../environments/environment';

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

  @Input() public activeStopIndex: number | null = null;

  @Output() public stopSelected = new EventEmitter<ItineraryItem>();
  @Output() public stopIndexSelected = new EventEmitter<number>();

  @ViewChild('mapElement', { static: false }) private mapElementRef?: ElementRef<HTMLDivElement>;

  public isExpanded = true;
  public map: L.Map | null = null;
  public polylineLayer: L.Polyline | null = null;
  public stopsLayer: L.LayerGroup | null = null;
  private stopMarkers: L.Marker[] = [];
  private isBrowser = false;

  constructor(
    private router: Router,
    @Inject(PLATFORM_ID) private platformId: object
  ) {
    this.isBrowser = isPlatformBrowser(this.platformId);
    if (this.isBrowser && typeof window !== 'undefined' && !(window as any).L) {
      (window as unknown as { L: unknown }).L = (L as unknown as { default?: unknown }).default ?? L;
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
    } else if (changes['activeStopIndex'] && !changes['activeStopIndex'].firstChange) {
      if (this.isBrowser) {
        this.updateActiveStopMarker();
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

      const tileUrl =
        environment.tileUrlTemplate ||
        'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
      const attribution =
        environment.tileAttribution ||
        '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors';

      L.tileLayer(tileUrl, {
        attribution,
        maxZoom: 19,
      }).addTo(this.map);
    }

    this.renderRoute();
  }

  private async fetchOsrmRoute(coords: Array<[number, number]>): Promise<Array<[number, number]> | null> {
    if (coords.length < 2) return null;
    const waypoints = coords.map(([lat, lng]) => `${lng},${lat}`).join(';');
    const url = `https://router.project-osrm.org/route/v1/driving/${waypoints}?overview=full&geometries=polyline`;
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2500);
      const res = await fetch(url, { signal: controller.signal });
      clearTimeout(timeoutId);
      if (!res.ok) return null;
      const data = await res.json();
      if (data.code === 'Ok' && data.routes && data.routes.length > 0) {
        return decodePolyline(data.routes[0].geometry);
      }
    } catch {
      // Graceful fallback to already rendered geodesic spline
    }
    return null;
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
    this.stopMarkers = [];

    const items = this.day.items || [];
    const stopCoords: Array<[number, number]> = [];
    const fullRoutePoints: Array<[number, number]> = [];
    let hasMissingPolyline = false;

    items.forEach((item, idx) => {
      const lat = item.place?.latitude ?? item.custom_lat;
      const lng = item.place?.longitude ?? item.custom_lng;
      if (lat != null && lng != null) {
        stopCoords.push([lat, lng]);

        // Place numbered circular pin with active pulse highlight support (GAP-05)
        const isActive = this.activeStopIndex === idx;
        const pinIcon = L.divIcon({
          className: 'preview-stop-marker-container',
          html: `<div class="preview-stop-pin${isActive ? ' is-active-stop' : ''}" role="button" tabindex="0" aria-label="Stop ${idx + 1}: ${item.place?.name || item.custom_title || 'Stop'}">${idx + 1}</div>`,
          iconSize: isActive ? [32, 32] : [26, 26],
          iconAnchor: isActive ? [16, 16] : [13, 13],
        });

        const marker = L.marker([lat, lng], { icon: pinIcon });
        marker.on('click', () => {
          this.stopIndexSelected.emit(idx);
          this.stopSelected.emit(item);
        });
        marker.addTo(this.stopsLayer!);
        this.stopMarkers.push(marker);

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
          hasMissingPolyline = true;
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

    // If online and missing polylines, query public OSRM router for real road geometry
    if (hasMissingPolyline && stopCoords.length > 1 && this.isBrowser) {
      this.fetchOsrmRoute(stopCoords).then((roadPoints) => {
        if (roadPoints && roadPoints.length > 1 && this.polylineLayer) {
          this.polylineLayer.setLatLngs(roadPoints);
        }
      });
    }
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

  private updateActiveStopMarker(): void {
    if (!this.map || !this.day?.items) return;
    const items = this.day.items;
    items.forEach((item, idx) => {
      const marker = this.stopMarkers[idx];
      if (!marker) return;
      const isActive = this.activeStopIndex === idx;
      const pinIcon = L.divIcon({
        className: 'preview-stop-marker-container',
        html: `<div class="preview-stop-pin${isActive ? ' is-active-stop' : ''}" role="button" tabindex="0" aria-label="Stop ${idx + 1}: ${item.place?.name || item.custom_title || 'Stop'}">${idx + 1}</div>`,
        iconSize: isActive ? [32, 32] : [26, 26],
        iconAnchor: isActive ? [16, 16] : [13, 13],
      });
      marker.setIcon(pinIcon);
      if (isActive) {
        const lat = item.place?.latitude ?? item.custom_lat;
        const lng = item.place?.longitude ?? item.custom_lng;
        if (lat != null && lng != null) {
          this.map?.panTo([lat, lng], { animate: true, duration: 0.5 });
        }
      }
    });
  }
}
