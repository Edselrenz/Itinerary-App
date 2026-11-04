import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { BehaviorSubject, of } from 'rxjs';
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
    id: 'user-1',
    first_name: 'Maria',
    last_name: 'Santos',
    username_normalized: 'traveler',
    email_normalized: 'traveler@example.ph',
    is_active: true,
    created_at: '2026-10-30T00:00:00Z',
  };

  const currentUserSubject = new BehaviorSubject<User | null>(mockUser);

  const mockAuthService = {
    currentUser$: currentUserSubject.asObservable(),
    logout: vi.fn().mockResolvedValue(undefined),
    updateProfile: vi.fn().mockReturnValue(of({ ...mockUser, first_name: 'Maria Clara' })),
  };

  const mockGuestMigrationService = {
    getUnsyncedCount: vi.fn().mockResolvedValue(2),
    migrateGuestData: vi.fn().mockResolvedValue({ migrated_count: 2 }),
  };

  const mockConnectivityService = {
    isHostOffline$: of(false),
  };

  const mockAlert = { present: vi.fn().mockResolvedValue(undefined) };
  const mockAlertController = { create: vi.fn().mockResolvedValue(mockAlert) };
  const mockToast = { present: vi.fn().mockResolvedValue(undefined) };
  const mockToastController = { create: vi.fn().mockResolvedValue(mockToast) };

  beforeEach(async () => {
    vi.clearAllMocks();
    currentUserSubject.next(mockUser);

    await TestBed.configureTestingModule({
      imports: [ProfilePage],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
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

  it('should create the profile page and receive current user', () => {
    expect(component).toBeTruthy();
    expect(component.currentUser).toEqual(mockUser);
  });

  it('should refresh unsynced guest itinerary count', async () => {
    await component.refreshGuestCount();
    expect(mockGuestMigrationService.getUnsyncedCount).toHaveBeenCalled();
    expect(component.guestItineraryCount).toBe(2);
  });

  it('opens and closes edit profile modal with prefilled data', () => {
    expect(component.isEditProfileOpen).toBe(false);
    component.openEditProfile();
    expect(component.isEditProfileOpen).toBe(true);
    expect(component.editForm.get('first_name')?.value).toBe('Maria');
    expect(component.editForm.get('last_name')?.value).toBe('Santos');
    expect(component.editForm.get('username')?.value).toBe('traveler');

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

  it('saves updated profile and presents success toast', async () => {
    component.openEditProfile();
    component.editForm.patchValue({ first_name: 'Maria Clara' });

    await component.saveProfile();
    expect(mockAuthService.updateProfile).toHaveBeenCalledWith(
      expect.objectContaining({ first_name: 'Maria Clara' })
    );
    expect(mockToastController.create).toHaveBeenCalled();
    expect(component.isEditProfileOpen).toBe(false);
  });

  it('opens and closes app settings modal and toggles dark mode', () => {
    expect(component.isSettingsOpen).toBe(false);
    component.openSettings();
    expect(component.isSettingsOpen).toBe(true);

    component.toggleDarkMode(true);
    expect(component.isDarkMode).toBe(true);
    expect(document.body.classList.contains('dark')).toBe(true);

    component.toggleDarkMode(false);
    expect(component.isDarkMode).toBe(false);
    expect(document.body.classList.contains('dark')).toBe(false);

    component.setDefaultBudget(5000);
    expect(component.defaultBudget).toBe(5000);

    component.closeSettings();
    expect(component.isSettingsOpen).toBe(false);
  });

  it('prompts confirmation alert before logging out with unsynced trips', async () => {
    component.guestItineraryCount = 3;
    await component.onLogout();
    expect(mockAlertController.create).toHaveBeenCalledWith(
      expect.objectContaining({ header: 'Unsynced Local Trips' })
    );
  });

  it('prompts standard logout alert when no unsynced trips exist', async () => {
    component.guestItineraryCount = 0;
    await component.onLogout();
    expect(mockAlertController.create).toHaveBeenCalledWith(
      expect.objectContaining({ header: 'Log Out' })
    );
  });

  it('should clean up subscription on destroy without error', () => {
    expect(() => component.ngOnDestroy()).not.toThrow();
  });
});
