import { Component, OnInit } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { Router } from '@angular/router';
import {
  IonButton,
  IonContent,
  IonHeader,
  IonIcon,
  IonSpinner,
  IonTitle,
  IonToolbar,
} from '@ionic/angular';
import { addIcons } from 'ionicons';
import {
  calendarOutline,
  checkmarkCircle,
  cloudOfflineOutline,
  cloudUploadOutline,
  logOutOutline,
  person,
  personOutline,
  syncOutline,
} from 'ionicons/icons';
import { User } from '../../core/models/auth.models';
import { AuthService } from '../../core/services/auth.service';
import { GuestMigrationService } from '../../core/services/guest-migration.service';

@Component({
  selector: 'app-profile',
  templateUrl: './profile.page.html',
  styleUrls: ['./profile.page.scss'],
  standalone: true,
  imports: [
    CommonModule,
    DatePipe,
    IonHeader,
    IonToolbar,
    IonTitle,
    IonContent,
    IonButton,
    IonIcon,
    IonSpinner,
  ],
})
export class ProfilePage implements OnInit {
  public currentUser: User | null = null;
  public guestItineraryCount = 0;
  public isMigrating = false;

  constructor(
    private router: Router,
    private authService: AuthService,
    private guestMigrationService: GuestMigrationService
  ) {
    addIcons({
      person,
      personOutline,
      checkmarkCircle,
      calendarOutline,
      logOutOutline,
      cloudOfflineOutline,
      cloudUploadOutline,
      syncOutline,
    });
  }

  public ngOnInit(): void {
    this.authService.currentUser$.subscribe((user) => {
      this.currentUser = user;
      this.refreshGuestCount();
    });
  }

  public ionViewWillEnter(): void {
    this.refreshGuestCount();
  }

  public async refreshGuestCount(): Promise<void> {
    try {
      this.guestItineraryCount = await this.guestMigrationService.getUnsyncedCount();
    } catch {
      this.guestItineraryCount = 0;
    }
  }

  public async syncGuestTrips(): Promise<void> {
    if (this.isMigrating) return;
    this.isMigrating = true;
    try {
      await this.guestMigrationService.migrateGuestData(true);
      await this.refreshGuestCount();
    } finally {
      this.isMigrating = false;
    }
  }

  public async onLogout(): Promise<void> {
    await this.authService.logout();
    this.router.navigate(['/welcome']);
  }

  public goToLogin(): void {
    this.router.navigate(['/login']);
  }

  public goToSignup(): void {
    this.router.navigate(['/signup']);
  }
}
