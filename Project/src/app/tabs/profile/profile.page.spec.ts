import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { BehaviorSubject } from 'rxjs';
import { describe, it, expect, beforeEach, vi } from 'vitest';

import { ProfilePage } from './profile.page';
import { AuthService } from '../../core/services/auth.service';
import { GuestMigrationService } from '../../core/services/guest-migration.service';
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
    logout: vi.fn(),
  };

  const mockGuestMigrationService = {
    getUnsyncedCount: vi.fn().mockResolvedValue(2),
    migrateGuestData: vi.fn().mockResolvedValue({ migrated_count: 2 }),
  };

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

  it('should clean up subscription on destroy without error', () => {
    expect(() => component.ngOnDestroy()).not.toThrow();
  });
});
