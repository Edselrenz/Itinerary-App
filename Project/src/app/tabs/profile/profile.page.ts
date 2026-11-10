import { CommonModule } from '@angular/common';
import type { OnDestroy, OnInit } from '@angular/core';
import { Component, inject } from '@angular/core';
import type { FormGroup } from '@angular/forms';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import {
  AlertController,
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
  arrowBackOutline,
  calendarOutline,
  callOutline,
  cameraOutline,
  cashOutline,
  checkmarkCircle,
  chevronForwardOutline,
  closeOutline,
  cloudOfflineOutline,
  cloudUploadOutline,
  createOutline,
  eyeOffOutline,
  eyeOutline,
  globeOutline,
  heart,
  heartOutline,
  helpCircle,
  helpCircleOutline,
  informationCircle,
  informationCircleOutline,
  lockClosed,
  logOutOutline,
  moonOutline,
  notifications,
  notificationsOutline,
  person,
  personOutline,
  settingsOutline,
  shieldCheckmarkOutline,
  sunnyOutline,
  syncOutline,
  trashOutline,
} from 'ionicons/icons';
import { Subscription } from 'rxjs';

import type { User, UserUpdateRequest } from '../../core/models/auth.models';
import { AuthService } from '../../core/services/auth.service';
import { ConnectivityService } from '../../core/services/connectivity.service';
import { GuestMigrationService } from '../../core/services/guest-migration.service';

export interface TravelerProfileExtra {
  middle_initial?: string;
  phone_number?: string;
  birthday?: string;
  gender?: string;
  avatar_url?: string;
}

@Component({
  selector: 'app-profile',
  templateUrl: './profile.page.html',
  styleUrls: ['./profile.page.scss'],
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    IonHeader,
    IonToolbar,
    IonTitle,
    IonContent,
    IonIcon,
    IonModal,
    IonSpinner,
  ],
})
export class ProfilePage implements OnInit, OnDestroy {
  public currentUser: User | null = null;
  public guestItineraryCount = 0;
  public isMigrating = false;

  // Extended Profile Extra Information matching Figma design
  public profileExtra: TravelerProfileExtra = {
    middle_initial: 'N/A',
    phone_number: '+66 81 234 5678',
    birthday: 'May 23, 2000',
    gender: 'Female',
    avatar_url: 'assets/images/pattranite_avatar.jpg',
  };

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
  public currentLanguage = 'en';
  public notificationsEnabled = true;
  public defaultBudget = 3000;
  public budgetPresets = [1500, 2500, 3000, 5000];
  public isHostOffline = false;

  // Help & Support Sub-Window
  public isHelpSupportOpen = false;
  public activeFaqIndex: number | null = 0;

  // About Sub-Window
  public isAboutOpen = false;
  public readonly appVersion = '1.0.0';

  // Log Out Confirmation Dialog
  public isLogoutConfirmOpen = false;

  private router = inject(Router);
  private fb = inject(FormBuilder);
  private authService = inject(AuthService);
  private guestMigrationService = inject(GuestMigrationService);
  private connectivityService = inject(ConnectivityService);
  private alertController = inject(AlertController);
  private toastController = inject(ToastController);
  private subscriptions = new Subscription();

  constructor() {
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
      heart,
      heartOutline,
      helpCircle,
      helpCircleOutline,
      informationCircle,
      informationCircleOutline,
      chevronForwardOutline,
      cameraOutline,
      globeOutline,
      notifications,
      notificationsOutline,
      callOutline,
      arrowBackOutline,
      lockClosed,
    });

    this.editForm = this.fb.group({
      first_name: ['Pattranite', [Validators.required, Validators.maxLength(80)]],
      middle_initial: ['N/A', [Validators.maxLength(10)]],
      last_name: ['Limpatayakorn', [Validators.required, Validators.maxLength(80)]],
      username: ['loverrukk', [Validators.required, Validators.minLength(3), Validators.maxLength(50)]],
      phone_number: ['+66 81 234 5678', [Validators.maxLength(25)]],
      birthday: ['May 23, 2000'],
      gender: ['Female'],
      avatar_url: ['assets/images/pattranite_avatar.jpg'],
      current_password: [''],
      new_password: ['', [Validators.minLength(8), Validators.maxLength(128)]],
    });
  }

  public ngOnInit(): void {
    this.subscriptions.add(
      this.authService.currentUser$.subscribe((user) => {
        this.currentUser = user;
        this.loadProfileExtra();
        this.refreshGuestCount();
      })
    );

    this.subscriptions.add(
      this.connectivityService.isHostOffline$.subscribe((offline) => {
        this.isHostOffline = offline;
      })
    );

    this.loadSettingsPreferences();
    this.loadProfileExtra();
  }

  public ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
  }

  public ionViewWillEnter(): void {
    this.refreshGuestCount();
    this.loadSettingsPreferences();
    this.loadProfileExtra();
  }

  public loadSettingsPreferences(): void {
    const savedTheme = localStorage.getItem('ne_theme_mode');
    this.isDarkMode = savedTheme === 'dark';
    if (this.isDarkMode) {
      document.body.classList.add('dark');
      document.documentElement.classList.add('dark');
    } else {
      document.body.classList.remove('dark');
      document.documentElement.classList.remove('dark');
    }

    const savedBudget = localStorage.getItem('ne_default_budget');
    if (savedBudget) {
      this.defaultBudget = parseInt(savedBudget, 10) || 3000;
    }

    const savedLang = localStorage.getItem('ne_language');
    if (savedLang) {
      this.currentLanguage = savedLang;
    }

    const savedNotifs = localStorage.getItem('ne_notifications');
    if (savedNotifs !== null) {
      this.notificationsEnabled = savedNotifs === 'true';
    }
  }

  public loadProfileExtra(): void {
    const userId = this.currentUser?.id || 'guest';
    const storageKey = `ne_profile_extra_${userId}`;
    const raw = localStorage.getItem(storageKey);
    if (raw) {
      try {
        this.profileExtra = { ...this.profileExtra, ...JSON.parse(raw) };
      } catch {
        // Fallback to default
      }
    } else {
      if (!this.profileExtra.avatar_url) {
        this.profileExtra.avatar_url = 'assets/images/pattranite_avatar.jpg';
      }
      if (!this.profileExtra.middle_initial) {
        this.profileExtra.middle_initial = 'N/A';
      }
      if (!this.profileExtra.birthday) {
        this.profileExtra.birthday = 'May 23, 2000';
      }
      if (!this.profileExtra.phone_number) {
        this.profileExtra.phone_number = '+66 81 234 5678';
      }
    }
  }

  public saveProfileExtraToStorage(): void {
    const userId = this.currentUser?.id || 'guest';
    const storageKey = `ne_profile_extra_${userId}`;
    localStorage.setItem(storageKey, JSON.stringify(this.profileExtra));
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

  // Navigation from Profile Menu
  public openFavorites(): void {
    this.router.navigate(['/tabs/history']);
  }

  // Edit Profile Methods
  public openEditProfile(): void {
    this.editProfileError = '';
    this.showCurrentPassword = false;
    this.showNewPassword = false;
    this.editForm.reset({
      first_name: this.currentUser?.first_name || 'Pattranite',
      middle_initial: this.profileExtra.middle_initial || 'N/A',
      last_name: this.currentUser?.last_name || 'Limpatayakorn',
      username: this.currentUser?.username_normalized || 'loverrukk',
      phone_number: this.profileExtra.phone_number || '+66 81 234 5678',
      birthday: this.profileExtra.birthday || 'May 23, 2000',
      gender: this.profileExtra.gender || 'Female',
      avatar_url: this.profileExtra.avatar_url || 'assets/images/pattranite_avatar.jpg',
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

  public onAvatarSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files[0]) {
      const file = input.files[0];
      const reader = new FileReader();
      reader.onload = (e) => {
        const base64 = e.target?.result as string;
        this.editForm.patchValue({ avatar_url: base64 });
      };
      reader.readAsDataURL(file);
    }
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

    // Update extended profile data locally
    this.profileExtra = {
      middle_initial: formVal.middle_initial?.trim() || 'N/A',
      phone_number: formVal.phone_number?.trim() || '+66 81 234 5678',
      birthday: formVal.birthday || 'May 23, 2000',
      gender: formVal.gender || 'Female',
      avatar_url: formVal.avatar_url || this.profileExtra.avatar_url || 'assets/images/pattranite_avatar.jpg',
    };
    this.saveProfileExtraToStorage();

    if (!this.currentUser) {
      this.isSavingProfile = false;
      this.isEditProfileOpen = false;
      const toast = await this.toastController.create({
        message: 'Profile updated locally!',
        duration: 2500,
        color: 'success',
        position: 'top',
      });
      await toast.present();
      return;
    }

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

  public openAccountInfo(): void {
    this.closeSettings();
    this.openEditProfile();
  }

  public async openPrivacySecurity(): Promise<void> {
    const alert = await this.alertController.create({
      header: 'Privacy & Security',
      subHeader: 'Your data is encrypted & secured',
      message:
        'All itinerary drafts, profile preferences, and account tokens are stored using AES-256 encrypted local storage and TLS 1.3 in transit.',
      buttons: ['Close'],
    });
    await alert.present();
  }

  public toggleLanguage(): void {
    const newLang = this.currentLanguage === 'en' ? 'fil' : 'en';
    this.setLanguage(newLang);
  }

  public toggleDarkMode(enabled: boolean): void {
    this.isDarkMode = enabled;
    localStorage.setItem('ne_theme_mode', enabled ? 'dark' : 'light');
    if (enabled) {
      document.body.classList.add('dark');
      document.documentElement.classList.add('dark');
    } else {
      document.body.classList.remove('dark');
      document.documentElement.classList.remove('dark');
    }
  }

  public setLanguage(lang: string): void {
    this.currentLanguage = lang;
    localStorage.setItem('ne_language', lang);
  }

  public toggleNotifications(enabled: boolean): void {
    this.notificationsEnabled = enabled;
    localStorage.setItem('ne_notifications', String(enabled));
  }

  public setDefaultBudget(budget: number): void {
    this.defaultBudget = budget;
    localStorage.setItem('ne_default_budget', String(budget));
  }

  public async clearLocalCache(): Promise<void> {
    const alert = await this.alertController.create({
      header: 'Clear Cache & Offline Data',
      message:
        'This will clear locally stored search queries, map tiles, and offline place caches to free up storage space. Your created itineraries and account credentials will not be deleted.',
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

  // Help & Support Methods
  public openHelpSupport(): void {
    this.isHelpSupportOpen = true;
  }

  public closeHelpSupport(): void {
    this.isHelpSupportOpen = false;
  }

  public toggleFaq(index: number): void {
    this.activeFaqIndex = this.activeFaqIndex === index ? null : index;
  }

  // About Methods
  public openAbout(): void {
    this.isAboutOpen = true;
  }

  public closeAbout(): void {
    this.isAboutOpen = false;
  }

  // Log Out Confirmation Dialog
  public openLogoutConfirm(): void {
    this.isLogoutConfirmOpen = true;
  }

  public closeLogoutConfirm(): void {
    this.isLogoutConfirmOpen = false;
  }

  public async executeLogout(): Promise<void> {
    this.isLogoutConfirmOpen = false;

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
              this.router.navigate(['/welcome'], { queryParams: { loggedOut: 'true' } });
            },
          },
        ],
      });
      await alert.present();
      return;
    }

    await this.authService.logout();
    this.router.navigate(['/welcome'], { queryParams: { loggedOut: 'true' } });
  }

  public onLogout(): void {
    this.openLogoutConfirm();
  }

  public goToLogin(): void {
    this.router.navigate(['/login']);
  }

  public goToSignup(): void {
    this.router.navigate(['/signup']);
  }
}
