import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import type { ComponentFixture} from '@angular/core/testing';
import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { ToastController } from '@ionic/angular';
import { of, throwError } from 'rxjs';
import { describe, it, expect, beforeEach, vi } from 'vitest';

import { AuthService } from '../../../core/services/auth.service';
import { GuestMigrationService } from '../../../core/services/guest-migration.service';

import { LoginPage } from './login.page';

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
    loginDemo: vi.fn().mockReturnValue(of({ user: { id: 'usr_pattranite_demo_01' }, access_token: 'tok' })),
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

  it('should pass rememberMe parameter to authService.login on submit (UI-22)', () => {
    component.loginForm.setValue({
      email: 'juan@example.ph',
      password: 'Password123!',
      rememberMe: true,
    });

    component.onSubmit();

    expect(mockAuthService.login).toHaveBeenCalledWith(
      { email: 'juan@example.ph', password: 'Password123!' },
      true
    );
  });

  it('should open and handle recovery modal with validation (UI-22)', () => {
    component.loginForm.get('email')?.setValue('pedro@example.ph');
    component.openForgotPasswordModal();

    expect(component.isForgotModalOpen).toBe(true);
    expect(component.recoveryEmail).toBe('pedro@example.ph');

    component.recoveryEmail = 'invalid-email';
    component.submitRecoveryRequest();
    expect(component.recoveryError).toBe('Please enter a valid email address.');
    expect(component.recoverySubmitted).toBe(false);

    component.recoveryEmail = 'pedro@valid.ph';
    component.submitRecoveryRequest(0);
    expect(component.recoveryError).toBeNull();
    expect(component.recoverySubmitted).toBe(true);

    component.closeForgotPasswordModal();
    expect(component.isForgotModalOpen).toBe(false);
  });

  it('should track isSubmittingRecovery state during recovery submission (Phase 43.3)', async () => {
    component.recoveryEmail = 'pedro@valid.ph';
    component.submitRecoveryRequest(50);
    expect(component.isSubmittingRecovery).toBe(true);
    await new Promise((resolve) => setTimeout(resolve, 80));
    expect(component.isSubmittingRecovery).toBe(false);
    expect(component.recoverySubmitted).toBe(true);
  });

  it('should open recovery modal without duplicate toasts on forgot password click (QA-09)', () => {
    component.loginForm.get('email')?.setValue('juan@example.ph');
    component.onForgotPassword();

    expect(component.isForgotModalOpen).toBe(true);
    expect(component.recoveryEmail).toBe('juan@example.ph');
    expect(mockToastController.create).not.toHaveBeenCalled();
  });

  it('should open recovery modal cleanly even if email is empty (QA-09)', () => {
    component.loginForm.get('email')?.setValue('');
    component.onForgotPassword();

    expect(component.isForgotModalOpen).toBe(true);
    expect(mockToastController.create).not.toHaveBeenCalled();
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

  it('should authenticate demo account when onDemoLogin is clicked (Finding 1)', async () => {
    expect(component.isDemoLoading).toBe(false);
    component.onDemoLogin();
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(mockAuthService.loginDemo).toHaveBeenCalled();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/tabs/home']);
    expect(component.isDemoLoading).toBe(false);
  });

  it('should display error message on login failure with reactive change detection (FIX-01C)', () => {
    mockAuthService.login.mockReturnValueOnce(
      throwError(() => ({ status: 401, error: { detail: 'Incorrect email or password' } }))
    );

    component.loginForm.setValue({
      email: 'wrong@example.ph',
      password: 'WrongPassword!',
      rememberMe: false,
    });

    component.onSubmit();

    expect(component.isLoading).toBe(false);
    expect(component.errorMessage).toBe('Incorrect email or password');

    // Also verify offline / gateway error message
    mockAuthService.login.mockReturnValueOnce(
      throwError(() => ({ status: 0 }))
    );

    component.onSubmit();
    expect(component.errorMessage).toContain('Authentication server is currently unreachable');
  });
});

