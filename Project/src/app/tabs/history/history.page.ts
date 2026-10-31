import { Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink } from '@angular/router';
import {
  AlertController,
  IonButton,
  IonContent,
  IonHeader,
  IonIcon,
  IonTitle,
  IonToolbar,
  ToastController,
} from '@ionic/angular';
import { addIcons } from 'ionicons';
import {
  addOutline,
  arrowForward,
  calendarOutline,
  cashOutline,
  locationOutline,
  sparkles,
  timeOutline,
  trashOutline,
} from 'ionicons/icons';
import { Subscription } from 'rxjs';
import { Itinerary } from '../../core/models/itinerary.models';
import { ItineraryService } from '../../core/services/itinerary.service';

@Component({
  selector: 'app-history',
  templateUrl: './history.page.html',
  styleUrls: ['./history.page.scss'],
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    IonHeader,
    IonToolbar,
    IonTitle,
    IonContent,
    IonIcon,
    IonButton,
  ],
})
export class HistoryPage implements OnInit, OnDestroy {
  public savedItineraries: Itinerary[] = [];
  private subscriptions = new Subscription();

  constructor(
    private itineraryService: ItineraryService,
    private router: Router,
    private alertController: AlertController,
    private toastController: ToastController
  ) {
    addIcons({
      timeOutline,
      calendarOutline,
      locationOutline,
      cashOutline,
      trashOutline,
      arrowForward,
      addOutline,
      sparkles,
    });
  }

  public ngOnInit(): void {
    this.subscriptions.add(
      this.itineraryService.itineraries$.subscribe((items) => {
        this.savedItineraries = items || [];
      })
    );
  }

  public ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
  }

  public openItinerary(itinerary: Itinerary): void {
    if (itinerary.id) {
      this.router.navigate(['/custom-builder', itinerary.id]);
    }
  }

  public async deleteItinerary(event: Event, itinerary: Itinerary): Promise<void> {
    event.stopPropagation();
    if (!itinerary.id) return;

    const alert = await this.alertController.create({
      header: 'Delete Itinerary?',
      message: `Are you sure you want to delete "${itinerary.title}"? This action cannot be undone.`,
      buttons: [
        { text: 'Cancel', role: 'cancel' },
        {
          text: 'Delete',
          role: 'destructive',
          handler: () => {
            this.itineraryService.deleteItinerary(itinerary.id).subscribe({
              next: async () => {
                const toast = await this.toastController.create({
                  message: `Itinerary "${itinerary.title}" deleted.`,
                  duration: 2500,
                  color: 'dark',
                  position: 'top',
                });
                await toast.present();
              },
              error: async () => {
                const toast = await this.toastController.create({
                  message: 'Failed to delete itinerary.',
                  duration: 3000,
                  color: 'danger',
                  position: 'top',
                });
                await toast.present();
              },
            });
          },
        },
      ],
    });
    await alert.present();
  }

  public getTotalStops(itinerary: Itinerary): number {
    if (!itinerary.days) return 0;
    return itinerary.days.reduce((acc, day) => acc + (day.items?.length || 0), 0);
  }
}
