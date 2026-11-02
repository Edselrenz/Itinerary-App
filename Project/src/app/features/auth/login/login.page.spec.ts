import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { Router } from '@angular/router';
import { ToastController } from '@ionic/angular';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { of } from 'rxjs';

import { LoginPage } from './login.page';
import { AuthService } from '../../../core/services/auth.service';
import { GuestMigrationService } from '../../../core/services/guest-migration.service';

describe('LoginPage', () => {
  let component: LoginPage;
  let fixture: ComponentFixture<LoginPage>;

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
    login: vi.fn().mockReturnValue(of({ user: { id: 'u1' }, access_token: 'tok' })),
  };

  const mockGuestMigrationService = {
    migrateGuestData: vi.fn().mockResolvedValue({ migrated_count: 0 }),
  };

  beforeEach(async () => {
    vi.clearAllMocks();

    await TestBed.configureTestingModule({
      imports: [LoginPage],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: ToastController, useValue: mockToastController },
        { provide: Router, useValue: mockRouter },
        { provide: AuthService, useValue: mockAuthService },
        { provide: GuestMigrationService, useValue: mockGuestMigrationService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(LoginPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create the login page and initialize form', () => {
    expect(component).toBeTruthy();
    expect(component.loginForm.valid).toBe(false);
  });

  it('should validate email format and password', () => {
    const emailControl = component.loginForm.get('email');
    const passwordControl = component.loginForm.get('password');

    emailControl?.setValue('invalid-email');
    passwordControl?.setValue('123456');
    expect(component.loginForm.valid).toBe(false);

    emailControl?.setValue('valid.traveler@example.ph');
    passwordControl?.setValue('Password123!');
    expect(component.loginForm.valid).toBe(true);
  });

  it('should reject forgot password with warning toast if email is empty or invalid (DEF-01)', async () => {
    component.loginForm.get('email')?.setValue('');
    await component.onForgotPassword();

    expect(mockToastController.create).toHaveBeenCalledWith(
      expect.objectContaining({
        message: 'Please enter a valid email address first.',
        color: 'warning',
      })
    );
    expect(mockToast.present).toHaveBeenCalled();
  });

  it('should display honest administrator notice if forgot password is clicked with valid email (DEF-01)', async () => {
    component.loginForm.get('email')?.setValue('juan@example.ph');
    await component.onForgotPassword();

    expect(mockToastController.create).toHaveBeenCalledWith(
      expect.objectContaining({
        message: expect.stringContaining('Self-service password reset is disabled in this pilot build'),
      })
    );
    expect(mockToast.present).toHaveBeenCalled();
  });

  it('should display truthful disabled notice on Google and Apple login buttons (DEF-02, DEF-08)', async () => {
    await component.onGoogleLogin();
    expect(mockToastController.create).toHaveBeenCalledWith(
      expect.objectContaining({
        message: 'Google Sign-In is disabled in this pilot build.',
      })
    );

    await component.onAppleLogin();
    expect(mockToastController.create).toHaveBeenCalledWith(
      expect.objectContaining({
        message: 'Apple Sign-In is disabled in this pilot build.',
      })
    );
  });
});

