import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { Router } from '@angular/router';
import { ToastController } from '@ionic/angular';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { of, throwError } from 'rxjs';

import { SignupPage } from './signup.page';
import { AuthService } from '../../../core/services/auth.service';
import { GuestMigrationService } from '../../../core/services/guest-migration.service';

describe('SignupPage', () => {
  let component: SignupPage;
  let fixture: ComponentFixture<SignupPage>;

  const mockToast = {
    present: vi.fn().mockResolvedValue(undefined),
  };

  const mockToastController = {
    create: vi.fn().mockResolvedValue(mockToast),
  };

  const mockRouter = {
    navigate: vi.fn(),
  };

  const mockAuthService = {
    register: vi.fn().mockReturnValue(of({ user: { id: 'u2' }, access_token: 'tok2' })),
  };

  const mockGuestMigrationService = {
    migrateGuestData: vi.fn().mockResolvedValue({ migrated_count: 0 }),
  };

  beforeEach(async () => {
    vi.clearAllMocks();

    await TestBed.configureTestingModule({
      imports: [SignupPage],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: ToastController, useValue: mockToastController },
        { provide: Router, useValue: mockRouter },
        { provide: AuthService, useValue: mockAuthService },
        { provide: GuestMigrationService, useValue: mockGuestMigrationService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(SignupPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create the signup page and initialize form', () => {
    expect(component).toBeTruthy();
    expect(component.signupForm.valid).toBe(false);
  });

  it('should validate password matching', () => {
    component.signupForm.patchValue({
      firstName: 'Maria',
      lastName: 'Santos',
      username: 'maria_santos',
      email: 'maria@example.ph',
      password: 'Password123!',
      confirmPassword: 'MismatchPassword!',
    });
    expect(component.signupForm.valid).toBe(false);
    expect(component.signupForm.errors?.['passwordsMismatch']).toBe(true);

    component.signupForm.patchValue({
      confirmPassword: 'Password123!',
    });
    expect(component.signupForm.valid).toBe(true);
  });

  it('should auto-suggest username from firstName and lastName when pristine', () => {
    component.signupForm.patchValue({
      firstName: 'Juan',
      lastName: 'Dela Cruz',
    });
    component.autoSuggestUsername();
    expect(component.signupForm.get('username')?.value).toBe('juan_delacruz');
  });

  it('should preserve middleInitial in first_name and send explicit username on submit (UI-21)', () => {
    component.signupForm.setValue({
      firstName: 'Juan',
      middleInitial: 'M',
      lastName: 'Dela Cruz',
      username: 'juan_custom',
      email: 'juan@example.ph',
      password: 'Password123!',
      confirmPassword: 'Password123!',
    });

    component.onSubmit();

    expect(mockAuthService.register).toHaveBeenCalledWith({
      first_name: 'Juan M.',
      last_name: 'Dela Cruz',
      username: 'juan_custom',
      email: 'juan@example.ph',
      password: 'Password123!',
    });
  });

  it('should display truthful disabled notice on Google and Apple signup buttons (DEF-02)', async () => {
    await component.onGoogleSignup();
    expect(mockToastController.create).toHaveBeenCalledWith(
      expect.objectContaining({
        message: 'Google Sign-Up is disabled in this pilot build.',
      })
    );

    await component.onAppleSignup();
    expect(mockToastController.create).toHaveBeenCalledWith(
      expect.objectContaining({
        message: 'Apple Sign-Up is disabled in this pilot build.',
      })
    );
  });

  it('should display error message on registration failure with reactive change detection', () => {
    mockAuthService.register.mockReturnValueOnce(
      throwError(() => ({ status: 409, error: { detail: 'Username is already taken' } }))
    );

    component.signupForm.patchValue({
      firstName: 'Maria',
      lastName: 'Santos',
      username: 'mariasantos',
      email: 'maria@example.ph',
      password: 'Password123!',
      confirmPassword: 'Password123!',
    });

    component.onSubmit();

    expect(component.isLoading).toBe(false);
    expect(component.errorMessage).toBe('Username is already taken');
  });
});

