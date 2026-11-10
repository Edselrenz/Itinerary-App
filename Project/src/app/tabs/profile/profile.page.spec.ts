import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { Router } from '@angular/router';
import { BehaviorSubject, of, throwError } from 'rxjs';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { AlertController, ToastController } from '@ionic/angular';

import { ProfilePage } from './profile.page';
import { AuthService } from '../../core/services/auth.service';
import { GuestMigrationService } from '../../core/services/guest-migration.service';
import { ConnectivityService } from '../../core/services/connectivity.service';
import { User } from '../../core/models/auth.models';

describe('ProfilePage', () => {
  let component: ProfilePage;
  let fixture: ComponentFixture<ProfilePage>;

  const mockUser: User = {
    id: 'user-123',
    first_name: 'Pattranite',
    last_name: 'Limpatayakorn',
    username_normalized: 'loverrukk',
    email_normalized: 'loverrukk@gmail.com',
    is_active: true,
    created_at: '2026-10-30T00:00:00Z',
  };

  const currentUserSubject = new BehaviorSubject<User | null>(mockUser);

  const mockAuthService = {
    currentUser$: currentUserSubject.asObservable(),
    logout: vi.fn().mockResolvedValue(undefined),
    updateProfile: vi.fn().mockReturnValue(of({ ...mockUser, first_name: 'Pattranite (Updated)' })),
  };

  const mockGuestMigrationService = {
    getUnsyncedCount: vi.fn().mockResolvedValue(2),
    migrateGuestData: vi.fn().mockResolvedValue({ migrated_count: 2 }),
  };

  const mockConnectivityService = {
    isHostOffline$: of(false),
  };

  const mockRouter = {
    navigate: vi.fn().mockResolvedValue(true),
  };

  const mockAlert = { present: vi.fn().mockResolvedValue(undefined) };
  const mockAlertController = { create: vi.fn().mockResolvedValue(mockAlert) };
  const mockToast = { present: vi.fn().mockResolvedValue(undefined) };
  const mockToastController = { create: vi.fn().mockResolvedValue(mockToast) };

  beforeEach(async () => {
    vi.clearAllMocks();
    localStorage.clear();
    sessionStorage.clear();
    currentUserSubject.next(mockUser);

    await TestBed.configureTestingModule({
      imports: [ProfilePage],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: Router, useValue: mockRouter },
        { provide: AuthService, useValue: mockAuthService },
        { provide: GuestMigrationService, useValue: mockGuestMigrationService },
        { provide: ConnectivityService, useValue: mockConnectivityService },
        { provide: AlertController, useValue: mockAlertController },
        { provide: ToastController, useValue: mockToastController },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ProfilePage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create the profile page and receive authenticated user', () => {
    expect(component).toBeTruthy();
    expect(component.currentUser).toEqual(mockUser);
  });

  it('should refresh unsynced guest itinerary count', async () => {
    await component.refreshGuestCount();
    expect(mockGuestMigrationService.getUnsyncedCount).toHaveBeenCalled();
    expect(component.guestItineraryCount).toBe(2);
  });

  it('navigates to /tabs/history when Favorites is selected', () => {
    component.openFavorites();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/tabs/history']);
  });

  it('opens and closes edit profile modal with prefilled data', () => {
    expect(component.isEditProfileOpen).toBe(false);
    component.openEditProfile();
    expect(component.isEditProfileOpen).toBe(true);
    expect(component.editForm.get('first_name')?.value).toBe('Pattranite');
    expect(component.editForm.get('last_name')?.value).toBe('Limpatayakorn');
    expect(component.editForm.get('username')?.value).toBe('loverrukk');

    component.closeEditProfile();
    expect(component.isEditProfileOpen).toBe(false);
  });

  it('toggles password visibility flags in edit profile', () => {
    expect(component.showCurrentPassword).toBe(false);
    component.toggleCurrentPasswordVisibility();
    expect(component.showCurrentPassword).toBe(true);

    expect(component.showNewPassword).toBe(false);
    component.toggleNewPasswordVisibility();
    expect(component.showNewPassword).toBe(true);
  });

  it('saves updated profile, updates local traveler extra, and presents success toast', async () => {
    component.openEditProfile();
    component.editForm.patchValue({
      first_name: 'Pattranite',
      middle_initial: 'L',
      phone_number: '+66 81 234 5678',
      birthday: '2000-05-23',
      gender: 'Female',
    });

    await component.saveProfile();
    expect(mockAuthService.updateProfile).toHaveBeenCalledWith(
      expect.objectContaining({ first_name: 'Pattranite', username: 'loverrukk' })
    );
    expect(mockToastController.create).toHaveBeenCalled();
    expect(component.isEditProfileOpen).toBe(false);
    expect(component.profileExtra.middle_initial).toBe('L');
    expect(component.profileExtra.phone_number).toBe('+66 81 234 5678');
  });

  it('handles profile update error and sets editProfileError', async () => {
    mockAuthService.updateProfile.mockReturnValueOnce(
      throwError(() => ({ error: { detail: 'Username already taken' } }))
    );

    component.openEditProfile();
    component.editForm.patchValue({ first_name: 'Test' });
    await component.saveProfile();

    expect(component.editProfileError).toBe('Username already taken');
    expect(component.isSavingProfile).toBe(false);
  });

  it('opens and closes app settings modal, toggles dark mode, and saves preferences', () => {
    expect(component.isSettingsOpen).toBe(false);
    component.openSettings();
    expect(component.isSettingsOpen).toBe(true);

    // Toggle dark mode
    component.toggleDarkMode(true);
    expect(component.isDarkMode).toBe(true);
    expect(document.body.classList.contains('dark')).toBe(true);
    expect(localStorage.getItem('ne_theme_mode')).toBe('dark');

    component.toggleDarkMode(false);
    expect(component.isDarkMode).toBe(false);
    expect(document.body.classList.contains('dark')).toBe(false);
    expect(localStorage.getItem('ne_theme_mode')).toBe('light');

    // Language
    component.setLanguage('fil');
    expect(component.currentLanguage).toBe('fil');
    expect(localStorage.getItem('ne_language')).toBe('fil');

    // Notifications
    component.toggleNotifications(false);
    expect(component.notificationsEnabled).toBe(false);
    expect(localStorage.getItem('ne_notifications')).toBe('false');

    // Default Budget
    component.setDefaultBudget(5000);
    expect(component.defaultBudget).toBe(5000);
    expect(localStorage.getItem('ne_default_budget')).toBe('5000');

    component.closeSettings();
    expect(component.isSettingsOpen).toBe(false);
  });

  it('clears local cache after confirmation alert', async () => {
    sessionStorage.setItem('test_cache', '123');
    await component.clearLocalCache();
    expect(mockAlertController.create).toHaveBeenCalledWith(
      expect.objectContaining({ header: 'Clear Cache & Offline Data' })
    );

    // Trigger clear handler
    const alertCall = mockAlertController.create.mock.calls[0][0];
    const clearBtn = alertCall.buttons.find((b: any) => b.text === 'Clear Cache');
    await clearBtn.handler();
    expect(sessionStorage.getItem('test_cache')).toBeNull();
    expect(mockToastController.create).toHaveBeenCalled();
  });

  it('opens and closes Help & Support modal and toggles FAQ items', () => {
    expect(component.isHelpSupportOpen).toBe(false);
    component.openHelpSupport();
    expect(component.isHelpSupportOpen).toBe(true);

    expect(component.activeFaqIndex).toBe(0);
    component.toggleFaq(1);
    expect(component.activeFaqIndex).toBe(1);

    component.toggleFaq(1);
    expect(component.activeFaqIndex).toBeNull();

    component.closeHelpSupport();
    expect(component.isHelpSupportOpen).toBe(false);
  });

  it('opens and closes About modal', () => {
    expect(component.isAboutOpen).toBe(false);
    component.openAbout();
    expect(component.isAboutOpen).toBe(true);
    expect(component.appVersion).toBe('1.0.0');

    component.closeAbout();
    expect(component.isAboutOpen).toBe(false);
  });

  it('opens and closes Figma-styled Log Out confirmation dialog', () => {
    expect(component.isLogoutConfirmOpen).toBe(false);
    component.openLogoutConfirm();
    expect(component.isLogoutConfirmOpen).toBe(true);

    component.closeLogoutConfirm();
    expect(component.isLogoutConfirmOpen).toBe(false);
  });

  it('prompts confirmation alert before logging out when unsynced local trips exist', async () => {
    component.guestItineraryCount = 3;
    await component.executeLogout();
    expect(mockAlertController.create).toHaveBeenCalledWith(
      expect.objectContaining({ header: 'Unsynced Local Trips' })
    );
  });

  it('executes logout and navigates to /welcome with loggedOut queryParam when no unsynced trips exist', async () => {
    component.guestItineraryCount = 0;
    await component.executeLogout();
    expect(mockAuthService.logout).toHaveBeenCalled();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/welcome'], { queryParams: { loggedOut: 'true' } });
  });

  it('supports Settings row shortcuts: account info, privacy, language toggle', async () => {
    component.openSettings();
    expect(component.isSettingsOpen).toBe(true);

    component.openAccountInfo();
    expect(component.isSettingsOpen).toBe(false);
    expect(component.isEditProfileOpen).toBe(true);

    await component.openPrivacySecurity();
    expect(mockAlertController.create).toHaveBeenCalledWith(
      expect.objectContaining({ header: 'Privacy & Security' })
    );

    component.currentLanguage = 'en';
    component.toggleLanguage();
    expect(component.currentLanguage).toBe('fil');
    component.toggleLanguage();
    expect(component.currentLanguage).toBe('en');
  });

  it('syncs guest trips and presents success toast', async () => {
    await component.syncGuestTrips();
    expect(mockGuestMigrationService.migrateGuestData).toHaveBeenCalledWith(true);
    expect(mockToastController.create).toHaveBeenCalledWith(
      expect.objectContaining({ color: 'success' })
    );
  });

  it('navigates to /login and /signup from guest view', () => {
    component.goToLogin();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/login']);

    component.goToSignup();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/signup']);
  });

  it('handles guest mode gracefully without displaying mockup persona or opening edit profile', () => {
    component.currentUser = null;
    component.loadProfileExtra();
    fixture.detectChanges();

    expect(component.profileExtra.avatar_url).toBe('');
    expect(component.profileExtra.phone_number).toBe('');

    // Calling openEditProfile in guest mode redirects to login instead of opening modal
    component.openEditProfile();
    expect(component.isEditProfileOpen).toBe(false);
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/login']);

    // Calling exitGuestMode redirects to /welcome
    component.exitGuestMode();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/welcome']);
  });

  it('should clean up subscription on destroy without error', () => {
    expect(() => component.ngOnDestroy()).not.toThrow();
  });
});
