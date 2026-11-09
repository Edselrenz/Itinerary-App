import { CommonModule } from '@angular/common';
import {
  Component,
  EventEmitter,
  Input,
  Output,
  ChangeDetectionStrategy,
  inject,
} from '@angular/core';
import { IonIcon } from '@ionic/angular';
import { addIcons } from 'ionicons';
import {
  addOutline,
  busOutline,
  callOutline,
  cashOutline,
  checkmarkCircle,
  chevronDownOutline,
  chevronUpOutline,
  closeOutline,
  globeOutline,
  informationCircleOutline,
  locationOutline,
  navigateOutline,
  shieldCheckmarkOutline,
  sparklesOutline,
  star,
  starHalf,
  starOutline,
  timeOutline,
} from 'ionicons/icons';

import { environment } from '../../../../environments/environment';
import type { CommuteInfo } from '../../../core/data/commute-guide.data';
import type { Place, PlacePhoto } from '../../../core/models/place.models';
import { ConnectivityService } from '../../../core/services/connectivity.service';
import { PlaceService } from '../../../core/services/place.service';

@Component({
  selector: 'app-place-detail-sheet',
  templateUrl: './place-detail-sheet.component.html',
  styleUrls: ['./place-detail-sheet.component.scss'],
  standalone: true,
  imports: [CommonModule, IonIcon],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PlaceDetailSheetComponent {
  private connectivityService = inject(ConnectivityService, { optional: true });

  @Input() public place: Place | null = null;
  @Input() public showAddToTripActions = true;
  @Input() public showNavigationAction = true;
  @Input() public dayNumber?: number;
  @Input() public stopNotes?: string | null;
  @Input() public commuteInfo?: CommuteInfo;

  @Output() public closeSheet = new EventEmitter<void>();
  @Output() public startTripHere = new EventEmitter<Place>();
  @Output() public addToCustomTrip = new EventEmitter<Place>();
  @Output() public addToDay = new EventEmitter<Place>();

  public isHoursExpanded = false;
  public activePhotoIndex = 0;
  public placeService = inject(PlaceService);

  constructor() {
    addIcons({
      addOutline,
      busOutline,
      callOutline,
      cashOutline,
      checkmarkCircle,
      chevronDownOutline,
      chevronUpOutline,
      closeOutline,
      globeOutline,
      informationCircleOutline,
      locationOutline,
      navigateOutline,
      shieldCheckmarkOutline,
      sparklesOutline,
      star,
      starHalf,
      starOutline,
      timeOutline,
    });
  }

  public onClose(): void {
    this.closeSheet.emit();
  }

  public onStartTripHere(): void {
    if (this.place) {
      this.startTripHere.emit(this.place);
    }
  }

  public onAddToCustomTrip(): void {
    if (this.place) {
      this.addToCustomTrip.emit(this.place);
    }
  }

  public onAddToDay(): void {
    if (this.place) {
      this.addToDay.emit(this.place);
    }
  }

  public toggleHours(): void {
    this.isHoursExpanded = !this.isHoursExpanded;
  }

  public setActivePhoto(idx: number): void {
    this.activePhotoIndex = idx;
  }

  public getHeroPhotoUrl(): string {
    if (!this.place) return '';

    // If Google Places photos exist, use photo proxy
    if (this.place.photos && this.place.photos.length > 0) {
      const active = this.place.photos[this.activePhotoIndex] || this.place.photos[0];
      if (active?.name) {
        const apiBase = this.connectivityService?.activeApiBaseUrl || environment.apiBaseUrl;
        return `${apiBase}/places/photos/${encodeURIComponent(active.name)}?max_width_px=800`;
      }
    }

    return this.placeService.getPlaceImage(this.place.name, this.place.image_url);
  }

  public getPhotoThumbnailUrl(photo: PlacePhoto): string {
    if (photo.name) {
      const apiBase = this.connectivityService?.activeApiBaseUrl || environment.apiBaseUrl;
      return `${apiBase}/places/photos/${encodeURIComponent(photo.name)}?max_width_px=200`;
    }
    return '';
  }

  public formatCost(place: Place): string {
    const min = place.estimated_cost_min;
    const max = place.estimated_cost_max;
    if (min != null && max != null) {
      if (min === 0 && max === 0) return 'Free Admission (₱0)';
      return `₱${min} - ₱${max}`;
    }
    if (min != null) return min === 0 ? 'Free Admission (₱0)' : `From ₱${min}`;
    if (max != null) return `Up to ₱${max}`;
    return 'Admission: Check on arrival';
  }

  public formatCategory(categoryKey: string): string {
    return this.placeService.formatCategoryName(categoryKey);
  }

  public getDirectionsUrl(place: Place): string {
    if (place.directions_url && place.directions_url.trim().length > 0) {
      return place.directions_url;
    }
    return `https://www.google.com/maps/dir/?api=1&destination=${place.latitude},${place.longitude}`;
  }

  public get isOpenNow(): boolean | null {
    if (this.place?.regular_opening_hours?.open_now !== undefined) {
      return this.place.regular_opening_hours.open_now;
    }
    return null;
  }

  public get weekdayDescriptions(): string[] {
    return this.place?.regular_opening_hours?.weekday_descriptions || [];
  }
}
