import { Injectable } from '@angular/core';
import { ToastController } from '@ionic/angular';
import { AuthService } from './auth.service';
import { GuestStorageService } from './guest-storage.service';
import { ItineraryService } from './itinerary.service';
import { ItineraryCreatePayload } from '../models/itinerary.models';

@Injectable({
  providedIn: 'root',
})
export class GuestMigrationService {
  constructor(
    private authService: AuthService,
    private guestStorage: GuestStorageService,
    private itineraryService: ItineraryService,
    private toastController: ToastController
  ) {}

  /**
   * Returns the count of local guest itineraries currently stored on this device.
   */
  public async getUnsyncedCount(): Promise<number> {
    const items = await this.guestStorage.getItineraries();
    return items ? items.length : 0;
  }

  /**
   * Migrates local guest itineraries to the authenticated traveler's backend account.
   * Resolves with the number of successfully migrated itineraries.
   */
  public async migrateGuestData(showToast: boolean = true): Promise<number> {
    if (!this.authService.isAuthenticated()) {
      return 0;
    }

    const guestItems = await this.guestStorage.getItineraries();
    if (!guestItems || guestItems.length === 0) {
      return 0;
    }

    let successCount = 0;

    for (const item of guestItems) {
      const payload: ItineraryCreatePayload = {
        title: item.title || 'Untitled Trip',
        destination: item.destination || 'Nueva Ecija',
        start_date: item.start_date,
        end_date: item.end_date,
        daily_budget: item.daily_budget || 0,
        preferences: item.preferences || [],
        type: item.type || 'custom',
        assumptions: item.assumptions || [],
        days: (item.days || []).map((d: any) => ({
          day_number: d.day_number,
          travel_date: d.travel_date,
          title: d.title,
          items: (d.items || []).map((it: any) => ({
            place_id: it.place_id,
            custom_title: it.custom_title,
            custom_lat: it.custom_lat,
            custom_lng: it.custom_lng,
            sort_order: it.sort_order,
            planned_time: it.planned_time,
            duration_minutes: it.duration_minutes || 60,
            notes: it.notes,
            estimated_cost_min: it.estimated_cost_min,
            estimated_cost_max: it.estimated_cost_max,
            place: it.place,
          })),
        })),
      };

      try {
        await new Promise<void>((resolve, reject) => {
          this.itineraryService.createItinerary(payload).subscribe({
            next: () => {
              successCount++;
              resolve();
            },
            error: (err) => {
              // Non-blocking: continue with next itinerary
              reject(err);
            },
          });
        });
      } catch {
        // Continue migration for remaining itineraries
      }
    }

    if (successCount > 0) {
      await this.guestStorage.clearGuestData();
      this.itineraryService.refreshItineraries().subscribe({ error: () => {} });

      if (showToast) {
        const toast = await this.toastController.create({
          message: `Synced ${successCount} ${successCount === 1 ? 'trip' : 'trips'} to your account!`,
          duration: 3000,
          color: 'success',
          position: 'top',
        });
        await toast.present();
      }
    }

    return successCount;
  }
}

