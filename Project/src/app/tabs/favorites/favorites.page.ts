import { CommonModule } from '@angular/common';
import type { OnDestroy, OnInit } from '@angular/core';
import { ChangeDetectorRef, Component, inject } from '@angular/core';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import {
  IonContent,
  IonHeader,
  IonIcon,
  IonToolbar,
  ToastController,
} from '@ionic/angular';
import { addIcons } from 'ionicons';
import {
  closeOutline,
  compassOutline,
  heart,
  heartOutline,
  locationOutline,
  navigateOutline,
  openOutline,
  searchOutline,
  trashOutline,
} from 'ionicons/icons';
import { Subscription } from 'rxjs';

import type { Place } from '../../core/models/place.models';
import { FavoritesService } from '../../core/services/favorites.service';
import { PlaceService } from '../../core/services/place.service';
import { PlaceDetailSheetComponent } from '../../shared/components/place-detail-sheet/place-detail-sheet.component';

@Component({
  selector: 'app-favorites',
  templateUrl: './favorites.page.html',
  styleUrls: ['./favorites.page.scss'],
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    IonHeader,
    IonToolbar,
    IonContent,
    IonIcon,
    PlaceDetailSheetComponent,
  ],
})
export class FavoritesPage implements OnInit, OnDestroy {
  public allFavorites: Place[] = [];
  public filteredFavorites: Place[] = [];
  public selectedCategory = 'ALL';
  public categories: string[] = ['ALL', 'Nature & Parks', 'Culture & Heritage', 'Cafes & Dining', 'Resorts & Stays', 'Farm & Agri-Tourism'];
  public searchControl = new FormControl('');
  public selectedPlaceForDetail: Place | null = null;

  private favoritesService = inject(FavoritesService);
  private placeService = inject(PlaceService);
  private router = inject(Router);
  private toastController = inject(ToastController);
  private cdr = inject(ChangeDetectorRef);
  private subscriptions = new Subscription();

  constructor() {
    addIcons({
      heart,
      heartOutline,
      locationOutline,
      navigateOutline,
      openOutline,
      searchOutline,
      trashOutline,
      compassOutline,
      closeOutline,
    });
  }

  public ngOnInit(): void {
    this.subscriptions.add(
      this.favoritesService.favorites$.subscribe((places) => {
        this.allFavorites = places;
        this.applyFilters();
        this.cdr.markForCheck();
      })
    );

    this.subscriptions.add(
      this.searchControl.valueChanges.subscribe(() => {
        this.applyFilters();
        this.cdr.markForCheck();
      })
    );
  }

  public ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
  }

  public ionViewWillEnter(): void {
    this.allFavorites = this.favoritesService.getFavorites();
    this.applyFilters();
    this.cdr.markForCheck();
  }

  public selectCategory(cat: string): void {
    this.selectedCategory = cat;
    this.applyFilters();
  }

  public clearSearch(): void {
    this.searchControl.setValue('');
  }

  public applyFilters(): void {
    const q = (this.searchControl.value || '').trim().toLowerCase();
    this.filteredFavorites = this.allFavorites.filter((place) => {
      const matchesSearch =
        !q ||
        place.name.toLowerCase().includes(q) ||
        (place.municipality_name && place.municipality_name.toLowerCase().includes(q)) ||
        (place.category && place.category.toLowerCase().includes(q));

      const matchesCat =
        this.selectedCategory === 'ALL' ||
        (place.category && place.category.toLowerCase().includes(this.selectedCategory.toLowerCase()));

      return matchesSearch && matchesCat;
    });
  }

  public async removeFavorite(place: Place, event?: Event): Promise<void> {
    if (event) {
      event.stopPropagation();
    }
    this.favoritesService.removeFavorite(place.id);
    const toast = await this.toastController.create({
      message: `Removed ${place.name} from favorites.`,
      duration: 2000,
      color: 'dark',
      position: 'bottom',
    });
    await toast.present();
  }

  public openPlaceDetail(place: Place): void {
    this.selectedPlaceForDetail = place;
    this.cdr.markForCheck();
  }

  public closePlaceDetail(): void {
    this.selectedPlaceForDetail = null;
    this.cdr.markForCheck();
  }

  public getPlaceImage(place: Place): string {
    return this.placeService.getPlaceImage(place.name, place.image_url);
  }

  public formatCost(place: Place): string {
    if (place.estimated_cost_min != null && place.estimated_cost_max != null) {
      if (place.estimated_cost_min === 0 && place.estimated_cost_max === 0) return 'Free Admission';
      return `₱${place.estimated_cost_min.toLocaleString()} - ₱${place.estimated_cost_max.toLocaleString()}`;
    }
    if (place.estimated_cost_min != null) return `From ₱${place.estimated_cost_min.toLocaleString()}`;
    return 'Admission: Check on arrival';
  }

  public getDirectionsUrl(place: Place): string {
    return `https://www.google.com/maps/dir/?api=1&destination=${place.latitude},${place.longitude}`;
  }

  public goToMap(): void {
    this.router.navigate(['/tabs/map']);
  }
}
