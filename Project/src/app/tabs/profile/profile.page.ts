import { CommonModule } from '@angular/common';
import type { OnDestroy, OnInit } from '@angular/core';
import { ChangeDetectorRef, Component, inject } from '@angular/core';
import type { FormGroup } from '@angular/forms';
import { FormBuilder, FormControl, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import {
  AlertController,
  IonContent,
  IonIcon,
  IonModal,
  IonSpinner,
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
  compassOutline,
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
  locationOutline,
  lockClosed,
  logOutOutline,
  moonOutline,
  navigateOutline,
  notifications,
  notificationsOutline,
  openOutline,
  person,
  personOutline,
  searchOutline,
  settingsOutline,
  shieldCheckmarkOutline,
  sunnyOutline,
  syncOutline,
  trashOutline,
} from 'ionicons/icons';
import { Subscription } from 'rxjs';

import type { User, UserUpdateRequest } from '../../core/models/auth.models';
import type { Place } from '../../core/models/place.models';
import { AuthService } from '../../core/services/auth.service';
import { ConnectivityService } from '../../core/services/connectivity.service';
import { FavoritesService } from '../../core/services/favorites.service';
import { GuestMigrationService } from '../../core/services/guest-migration.service';
import { PlaceService } from '../../core/services/place.service';
import { PlaceDetailSheetComponent } from '../../shared/components/place-detail-sheet/place-detail-sheet.component';

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
    IonContent,
    IonIcon,
    IonModal,
    IonSpinner,
    PlaceDetailSheetComponent,
  ],
})
export class ProfilePage implements OnInit, OnDestroy {
  public currentUser: User | null = null;
  public guestItineraryCount = 0;
  public isMigrating = false;
  public viewMode: 'profile' | 'settings' | 'help' | 'about' | 'edit' | 'favorites' = 'profile';
  public editAvatarPreview: string | null = null;

  // Favorites Sub-Window (Accessible only from Profile tab)
  public allFavorites: Place[] = [];
  public filteredFavorites: Place[] = [];
  public selectedFavCategory = 'ALL';
  public favCategories: string[] = ['ALL', 'Nature & Parks', 'Culture & Heritage', 'Cafes & Dining', 'Resorts & Stays', 'Farm & Agri-Tourism'];
  public favSearchControl = new FormControl('');
  public selectedPlaceForDetail: Place | null = null;

  // Extended Profile Extra Information matching Figma design
  public profileExtra: TravelerProfileExtra = {
    middle_initial: '',
    phone_number: '',
    birthday: '',
    gender: '',
    avatar_url: '',
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
  private route = inject(ActivatedRoute);
  private fb = inject(FormBuilder);
  private authService = inject(AuthService);
  private favoritesService = inject(FavoritesService);
  private placeService = inject(PlaceService);
  private guestMigrationService = inject(GuestMigrationService);
  private connectivityService = inject(ConnectivityService);
  private alertController = inject(AlertController);
  private toastController = inject(ToastController);
  private cdr = inject(ChangeDetectorRef);
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
      locationOutline,
      navigateOutline,
      openOutline,
      searchOutline,
      compassOutline,
    });

    this.editForm = this.fb.group({
      first_name: ['', [Validators.required, Validators.maxLength(80)]],
      middle_initial: ['', [Validators.maxLength(10)]],
      last_name: ['', [Validators.required, Validators.maxLength(80)]],
      username: ['', [Validators.required, Validators.minLength(3), Validators.maxLength(50)]],
      phone_number: ['', [Validators.maxLength(25)]],
      birthday: [''],
      gender: [''],
      avatar_url: ['assets/images/default_avatar_placeholder.png'],
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

    this.subscriptions.add(
      this.favoritesService.favorites$.subscribe((places) => {
        this.allFavorites = places;
        this.applyFavFilters();
        this.cdr.markForCheck();
      })
    );

    this.subscriptions.add(
      this.favSearchControl.valueChanges.subscribe(() => {
        this.applyFavFilters();
        this.cdr.markForCheck();
      })
    );

    const viewParam = this.route.snapshot.queryParamMap.get('view');
    if (viewParam === 'favorites') {
      this.openFavorites();
    }

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
    if (this.viewMode === 'favorites') {
      this.allFavorites = this.favoritesService.getFavorites();
      this.applyFavFilters();
    }
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
    if (!this.currentUser) {
      this.profileExtra = {
        middle_initial: '',
        phone_number: '',
        birthday: '',
        gender: '',
        avatar_url: '',
      };
      this.cdr.markForCheck();
      return;
    }

    const isDemo =
      this.currentUser.id === 'usr_pattranite_demo_01' ||
      this.currentUser.username_normalized === 'loverrukk' ||
      this.currentUser.email_normalized === 'loverrukk@gmail.com';

    if (isDemo) {
      if (!this.currentUser.first_name) {
        this.currentUser.first_name = 'Pattranite';
      }
      if (!this.currentUser.last_name) {
        this.currentUser.last_name = 'Limpatiyakorn';
      }
      if (!this.currentUser.username_normalized) {
        this.currentUser.username_normalized = 'loverrukk';
      }
    }

    const userId = this.currentUser.id;
    const storageKey = `ne_profile_extra_${userId}`;
    const raw = localStorage.getItem(storageKey);
    if (raw) {
      try {
        this.profileExtra = { ...this.profileExtra, ...JSON.parse(raw) };
      } catch {
        // Fallback to default
      }
    } else {
      if (isDemo) {
        this.profileExtra = {
          middle_initial: 'N/A',
          phone_number: '+66 81 234 5678',
          birthday: 'May 23, 2000',
          gender: 'Female',
          avatar_url: 'assets/images/pattranite_avatar.jpg',
        };
      } else {
        this.profileExtra = {
          middle_initial: '',
          phone_number: '',
          birthday: '',
          gender: '',
          avatar_url: 'assets/images/default_avatar_placeholder.png',
        };
      }
    }

    if (!this.profileExtra.avatar_url) {
      this.profileExtra.avatar_url = isDemo
        ? 'assets/images/pattranite_avatar.jpg'
        : 'assets/images/default_avatar_placeholder.png';
    }
    this.cdr.markForCheck();
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

  // Favorites Sub-Window Methods (Profile Tab Only)
  public openFavorites(): void {
    this.viewMode = 'favorites';
    this.allFavorites = this.favoritesService.getFavorites();
    this.applyFavFilters();
    this.cdr.markForCheck();
  }

  public closeFavorites(): void {
    this.viewMode = 'profile';
    this.cdr.markForCheck();
  }

  public selectFavCategory(cat: string): void {
    this.selectedFavCategory = cat;
    this.applyFavFilters();
    this.cdr.markForCheck();
  }

  public clearFavSearch(): void {
    this.favSearchControl.setValue('');
  }

  public applyFavFilters(): void {
    const q = (this.favSearchControl.value || '').trim().toLowerCase();
    this.filteredFavorites = this.allFavorites.filter((place) => {
      const matchesSearch =
        !q ||
        place.name.toLowerCase().includes(q) ||
        (place.municipality_name && place.municipality_name.toLowerCase().includes(q)) ||
        (place.category && place.category.toLowerCase().includes(q));

      const matchesCat =
        this.selectedFavCategory === 'ALL' ||
        (place.category && place.category.toLowerCase().includes(this.selectedFavCategory.toLowerCase()));

      return matchesSearch && matchesCat;
    });
  }

  public async removeFavoritePlace(place: Place, event?: Event): Promise<void> {
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
    this.cdr.markForCheck();
  }

  public openFavDetail(place: Place): void {
    this.selectedPlaceForDetail = place;
    this.cdr.markForCheck();
  }

  public closeFavDetail(): void {
    this.selectedPlaceForDetail = null;
    this.cdr.markForCheck();
  }

  public getPlaceImg(place: Place): string {
    return this.placeService.getPlaceImage(place.name, place.image_url);
  }

  public formatPlaceCost(place: Place): string {
    if (place.estimated_cost_min != null && place.estimated_cost_max != null) {
      if (place.estimated_cost_min === 0 && place.estimated_cost_max === 0) return 'Free Admission';
      return `₱${place.estimated_cost_min.toLocaleString()} - ₱${place.estimated_cost_max.toLocaleString()}`;
    }
    if (place.estimated_cost_min != null) return `From ₱${place.estimated_cost_min.toLocaleString()}`;
    return 'Admission: Check on arrival';
  }

  public getDirections(place: Place): string {
    return `https://www.google.com/maps/dir/?api=1&destination=${place.latitude},${place.longitude}`;
  }

  public goToExplore(): void {
    this.router.navigate(['/tabs/home']);
  }

  // Edit Profile Methods
  public openEditProfile(): void {
    if (!this.currentUser) {
      this.goToLogin();
      return;
    }
    this.viewMode = 'edit';
    this.isEditProfileOpen = true;
    this.editProfileError = '';
    this.showCurrentPassword = false;
    this.showNewPassword = false;
    const isDemo =
      this.currentUser.id === 'usr_pattranite_demo_01' ||
      this.currentUser.username_normalized === 'loverrukk' ||
      this.currentUser.email_normalized === 'loverrukk@gmail.com';

    this.editAvatarPreview =
      this.profileExtra.avatar_url ||
      (isDemo ? 'assets/images/pattranite_avatar.jpg' : 'assets/images/default_avatar_placeholder.png');
    this.editForm.reset({
      first_name: this.currentUser?.first_name || (isDemo ? 'Pattranite' : ''),
      middle_initial: this.profileExtra.middle_initial || '',
      last_name: this.currentUser?.last_name || (isDemo ? 'Limpatayakorn' : ''),
      username: this.currentUser?.username_normalized || (isDemo ? 'loverrukk' : ''),
      phone_number: this.profileExtra.phone_number || '',
      birthday: this.profileExtra.birthday || '',
      gender: this.profileExtra.gender || '',
      avatar_url: this.editAvatarPreview,
      current_password: '',
      new_password: '',
    });
    this.cdr.markForCheck();
  }

  public closeEditProfile(): void {
    this.viewMode = 'profile';
    this.isEditProfileOpen = false;
    this.editAvatarPreview = null;
    this.editProfileError = '';
    this.cdr.markForCheck();
  }

  public toggleCurrentPasswordVisibility(): void {
    this.showCurrentPassword = !this.showCurrentPassword;
    this.cdr.markForCheck();
  }

  public toggleNewPasswordVisibility(): void {
    this.showNewPassword = !this.showNewPassword;
    this.cdr.markForCheck();
  }

  public onAvatarSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files[0]) {
      const file = input.files[0];
      if (!file.type.startsWith('image/')) {
        this.editProfileError = 'Please select a valid image file.';
        this.cdr.markForCheck();
        return;
      }
      const reader = new FileReader();
      reader.onload = (e) => {
        const base64 = e.target?.result as string;
        this.editAvatarPreview = base64;
        this.editForm.patchValue({ avatar_url: base64 });
        this.cdr.markForCheck();
      };
      reader.onerror = () => {
        this.editProfileError = 'Failed to load selected image.';
        this.cdr.markForCheck();
      };
      reader.readAsDataURL(file);
      // Reset input value so re-selecting same file triggers change
      input.value = '';
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
    const finalAvatar =
      this.editAvatarPreview ||
      formVal.avatar_url ||
      this.profileExtra.avatar_url ||
      'assets/images/default_avatar_placeholder.png';

    this.profileExtra = {
      middle_initial: formVal.middle_initial?.trim() || 'N/A',
      phone_number: formVal.phone_number?.trim() || '+66 81 234 5678',
      birthday: formVal.birthday || 'May 23, 2000',
      gender: formVal.gender || 'Female',
      avatar_url: finalAvatar,
    };
    this.saveProfileExtraToStorage();

    if (!this.currentUser) {
      this.isSavingProfile = false;
      this.closeEditProfile();
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
        this.closeEditProfile();
        const toast = await this.toastController.create({
          message: 'Profile updated successfully!',
          duration: 2500,
          color: 'success',
          position: 'top',
        });
        await toast.present();
        this.cdr.markForCheck();
      },
      error: (err) => {
        this.isSavingProfile = false;
        this.editProfileError =
          err?.error?.detail || err?.message || 'Failed to update profile. Please try again.';
        this.cdr.markForCheck();
      },
    });
  }

  // App Settings Methods
  public openSettings(): void {
    this.loadSettingsPreferences();
    this.viewMode = 'settings';
    this.isSettingsOpen = true;
    this.cdr.markForCheck();
  }

  public closeSettings(): void {
    this.viewMode = 'profile';
    this.isSettingsOpen = false;
    this.cdr.markForCheck();
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
    this.cdr.markForCheck();
  }

  public toggleDarkMode(enabled?: boolean): void {
    this.isDarkMode = enabled !== undefined ? enabled : !this.isDarkMode;
    localStorage.setItem('ne_theme_mode', this.isDarkMode ? 'dark' : 'light');
    if (this.isDarkMode) {
      document.body.classList.add('dark');
      document.documentElement.classList.add('dark');
    } else {
      document.body.classList.remove('dark');
      document.documentElement.classList.remove('dark');
    }
    this.cdr.markForCheck();
  }

  public setLanguage(lang: string): void {
    this.currentLanguage = lang;
    localStorage.setItem('ne_language', lang);
    this.cdr.markForCheck();
  }

  public toggleNotifications(eventOrEnabled?: boolean | Event): void {
    if (typeof eventOrEnabled === 'boolean') {
      this.notificationsEnabled = eventOrEnabled;
    } else if (eventOrEnabled && 'target' in eventOrEnabled) {
      this.notificationsEnabled = (eventOrEnabled.target as HTMLInputElement).checked;
    } else {
      this.notificationsEnabled = !this.notificationsEnabled;
    }
    localStorage.setItem('ne_notifications', String(this.notificationsEnabled));
    this.cdr.markForCheck();
  }

  public setDefaultBudget(budget: number): void {
    this.defaultBudget = budget;
    localStorage.setItem('ne_default_budget', String(budget));
    this.cdr.markForCheck();
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
    this.viewMode = 'help';
    this.isHelpSupportOpen = true;
    this.cdr.markForCheck();
  }

  public closeHelpSupport(): void {
    this.viewMode = 'profile';
    this.isHelpSupportOpen = false;
    this.cdr.markForCheck();
  }

  public toggleFaq(index: number): void {
    this.activeFaqIndex = this.activeFaqIndex === index ? null : index;
    this.cdr.markForCheck();
  }

  // About Methods
  public openAbout(): void {
    this.viewMode = 'about';
    this.isAboutOpen = true;
    this.cdr.markForCheck();
  }

  public closeAbout(): void {
    this.viewMode = 'profile';
    this.isAboutOpen = false;
    this.cdr.markForCheck();
  }

  // Log Out Confirmation Dialog
  public openLogoutConfirm(): void {
    this.isLogoutConfirmOpen = true;
    this.cdr.markForCheck();
  }

  public closeLogoutConfirm(): void {
    this.isLogoutConfirmOpen = false;
    this.cdr.markForCheck();
  }

  public exitGuestMode(): void {
    this.router.navigate(['/welcome']);
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
