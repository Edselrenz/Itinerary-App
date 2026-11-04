import { Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import {
  AlertController,
  IonButton,
  IonContent,
  IonHeader,
  IonIcon,
  IonModal,
  IonSpinner,
  IonTitle,
  IonToolbar,
  ToastController,
} from '@ionic/angular';
import { addIcons } from 'ionicons';
import {
  alertCircleOutline,
  calendarOutline,
  cashOutline,
  checkmarkCircle,
  closeOutline,
  cloudOfflineOutline,
  cloudUploadOutline,
  createOutline,
  eyeOffOutline,
  eyeOutline,
  logOutOutline,
  moonOutline,
  person,
  personOutline,
  settingsOutline,
  shieldCheckmarkOutline,
  sunnyOutline,
  syncOutline,
  trashOutline,
} from 'ionicons/icons';
import { Subscription } from 'rxjs';
import { User, UserUpdateRequest } from '../../core/models/auth.models';
import { AuthService } from '../../core/services/auth.service';
import { ConnectivityService } from '../../core/services/connectivity.service';
import { GuestMigrationService } from '../../core/services/guest-migration.service';

@Component({
  selector: 'app-profile',
  templateUrl: './profile.page.html',
  styleUrls: ['./profile.page.scss'],
  standalone: true,
  imports: [
    CommonModule,
    DatePipe,
    ReactiveFormsModule,
    IonHeader,
    IonToolbar,
    IonTitle,
    IonContent,
    IonButton,
    IonIcon,
    IonModal,
    IonSpinner,
  ],
})
export class ProfilePage implements OnInit, OnDestroy {
  public currentUser: User | null = null;
  public guestItineraryCount = 0;
  public isMigrating = false;

  // Edit Profile Sub-Window
  public isEditProfileOpen = false;
  public isSavingProfile = false;
  public editProfileError = '';
  public editForm: FormGroup;
  public showCurrentPassword = false;
  public showNewPassword = false;

  // App Settings Sub-Window
  public isSettingsOpen = false;
  public isDarkMode = false;
  public defaultBudget = 3000;
  public budgetPresets = [1500, 2500, 3000, 5000];
  public isHostOffline = false;

  private subscriptions = new Subscription();

  constructor(
    private router: Router,
    private fb: FormBuilder,
    private authService: AuthService,
    private guestMigrationService: GuestMigrationService,
    private connectivityService: ConnectivityService,
    private alertController: AlertController,
    private toastController: ToastController
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
      createOutline,
      settingsOutline,
      closeOutline,
      moonOutline,
      sunnyOutline,
      cashOutline,
      trashOutline,
      eyeOutline,
      eyeOffOutline,
      shieldCheckmarkOutline,
      alertCircleOutline,
    });

    this.editForm = this.fb.group({
      first_name: ['', [Validators.required, Validators.maxLength(80)]],
      last_name: ['', [Validators.required, Validators.maxLength(80)]],
      username: ['', [Validators.required, Validators.minLength(3), Validators.maxLength(50)]],
      current_password: [''],
      new_password: ['', [Validators.minLength(8), Validators.maxLength(128)]],
    });
  }

  public ngOnInit(): void {
    this.subscriptions.add(
      this.authService.currentUser$.subscribe((user) => {
        this.currentUser = user;
        this.refreshGuestCount();
      })
    );

    this.subscriptions.add(
      this.connectivityService.isHostOffline$.subscribe((offline) => {
        this.isHostOffline = offline;
      })
    );

    this.loadSettingsPreferences();
  }

  public ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
  }

  public ionViewWillEnter(): void {
    this.refreshGuestCount();
    this.loadSettingsPreferences();
  }

  public loadSettingsPreferences(): void {
    const savedTheme = localStorage.getItem('ne_theme_mode');
    this.isDarkMode = savedTheme === 'dark';
    if (this.isDarkMode) {
      document.body.classList.add('dark');
    } else {
      document.body.classList.remove('dark');
    }

    const savedBudget = localStorage.getItem('ne_default_budget');
    if (savedBudget) {
      this.defaultBudget = parseInt(savedBudget, 10) || 3000;
    }
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
      const toast = await this.toastController.create({
        message: 'Local guest trips synced successfully to your account!',
        duration: 2500,
        color: 'success',
        position: 'top',
      });
      await toast.present();
    } catch {
      const toast = await this.toastController.create({
        message: 'Could not sync trips right now. Please try again when online.',
        duration: 2500,
        color: 'warning',
        position: 'top',
      });
      await toast.present();
    } finally {
      this.isMigrating = false;
    }
  }

  // Edit Profile Methods
  public openEditProfile(): void {
    if (!this.currentUser) return;
    this.editProfileError = '';
    this.showCurrentPassword = false;
    this.showNewPassword = false;
    this.editForm.reset({
      first_name: this.currentUser.first_name,
      last_name: this.currentUser.last_name,
      username: this.currentUser.username_normalized,
      current_password: '',
      new_password: '',
    });
    this.isEditProfileOpen = true;
  }

  public closeEditProfile(): void {
    this.isEditProfileOpen = false;
    this.editProfileError = '';
  }

  public toggleCurrentPasswordVisibility(): void {
    this.showCurrentPassword = !this.showCurrentPassword;
  }

  public toggleNewPasswordVisibility(): void {
    this.showNewPassword = !this.showNewPassword;
  }

  public async saveProfile(): Promise<void> {
    if (this.editForm.invalid) {
      this.editForm.markAllAsTouched();
      return;
    }

    const formVal = this.editForm.value;
    const updatePayload: UserUpdateRequest = {
      first_name: formVal.first_name?.trim(),
      last_name: formVal.last_name?.trim(),
      username: formVal.username?.trim(),
    };

    if (formVal.new_password) {
      if (!formVal.current_password) {
        this.editProfileError = 'Current password is required to change your password.';
        return;
      }
      updatePayload.current_password = formVal.current_password;
      updatePayload.new_password = formVal.new_password;
    }

    this.isSavingProfile = true;
    this.editProfileError = '';

    this.authService.updateProfile(updatePayload).subscribe({
      next: async (updatedUser) => {
        this.currentUser = updatedUser;
        this.isSavingProfile = false;
        this.isEditProfileOpen = false;
        const toast = await this.toastController.create({
          message: 'Profile updated successfully!',
          duration: 2500,
          color: 'success',
          position: 'top',
        });
        await toast.present();
      },
      error: (err) => {
        this.isSavingProfile = false;
        this.editProfileError =
          err?.error?.detail || err?.message || 'Failed to update profile. Please try again.';
      },
    });
  }

  // App Settings Methods
  public openSettings(): void {
    this.loadSettingsPreferences();
    this.isSettingsOpen = true;
  }

  public closeSettings(): void {
    this.isSettingsOpen = false;
  }

  public toggleDarkMode(enabled: boolean): void {
    this.isDarkMode = enabled;
    localStorage.setItem('ne_theme_mode', enabled ? 'dark' : 'light');
    if (enabled) {
      document.body.classList.add('dark');
    } else {
      document.body.classList.remove('dark');
    }
  }

  public setDefaultBudget(budget: number): void {
    this.defaultBudget = budget;
    localStorage.setItem('ne_default_budget', String(budget));
  }

  public async clearLocalCache(): Promise<void> {
    const alert = await this.alertController.create({
      header: 'Clear Cache & Offline Data',
      message:
        'This will clear locally stored search caches and reset offline destination references. Your created itineraries will not be deleted.',
      buttons: [
        { text: 'Cancel', role: 'cancel' },
        {
          text: 'Clear Cache',
          role: 'destructive',
          handler: async () => {
            sessionStorage.clear();
            const toast = await this.toastController.create({
              message: 'Local cache cleared successfully.',
              duration: 2000,
              color: 'dark',
              position: 'top',
            });
            await toast.present();
          },
        },
      ],
    });
    await alert.present();
  }

  // Logout with Unsynced Trips Alert
  public async onLogout(): Promise<void> {
    if (this.guestItineraryCount > 0) {
      const alert = await this.alertController.create({
        header: 'Unsynced Local Trips',
        message: `You have ${this.guestItineraryCount} local ${this.guestItineraryCount === 1 ? 'trip' : 'trips'} not yet synced to your account. Logging out now will leave them on this device without cloud backup. Are you sure you want to log out?`,
        buttons: [
          { text: 'Cancel', role: 'cancel' },
          {
            text: 'Log Out Anyway',
            role: 'destructive',
            handler: async () => {
              await this.authService.logout();
              this.router.navigate(['/welcome']);
            },
          },
        ],
      });
      await alert.present();
      return;
    }

    const alert = await this.alertController.create({
      header: 'Log Out',
      message: 'Are you sure you want to log out of your Nueva Ecija Travel account?',
      buttons: [
        { text: 'Cancel', role: 'cancel' },
        {
          text: 'Log Out',
          role: 'destructive',
          handler: async () => {
            await this.authService.logout();
            this.router.navigate(['/welcome']);
          },
        },
      ],
    });
    await alert.present();
  }

  public goToLogin(): void {
    this.router.navigate(['/login']);
  }

  public goToSignup(): void {
    this.router.navigate(['/signup']);
  }
}
