import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import {
  FormControl,
  FormGroup,
  FormsModule,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { Router } from '@angular/router';
import {
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
  closeOutline,
  eyeOffOutline,
  eyeOutline,
  keyOutline,
  logoApple,
  mailOutline,
  shieldCheckmarkOutline,
  sparkles,
} from 'ionicons/icons';

import { AuthService } from '../../../core/services/auth.service';
import { GuestMigrationService } from '../../../core/services/guest-migration.service';

@Component({
  selector: 'app-login',
  templateUrl: './login.page.html',
  styleUrls: ['./login.page.scss'],
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    IonContent,
    IonIcon,
    IonModal,
    IonSpinner,
  ],
})
export class LoginPage {
  public showPassword = false;
  public isLoading = false;
  public errorMessage: string | null = null;
  public isForgotModalOpen = false;
  public recoveryEmail = '';
  public recoverySubmitted = false;
  public recoveryError: string | null = null;

  public loginForm = new FormGroup({
    email: new FormControl('', [Validators.required, Validators.email]),
    password: new FormControl('', [Validators.required]),
    rememberMe: new FormControl(false),
  });

  private router = inject(Router);
  private authService = inject(AuthService);
  private guestMigrationService = inject(GuestMigrationService);
  private toastController = inject(ToastController);

  constructor() {
    addIcons({
      arrowBackOutline,
      mailOutline,
      keyOutline,
      eyeOutline,
      eyeOffOutline,
      logoApple,
      alertCircleOutline,
      closeOutline,
      shieldCheckmarkOutline,
      sparkles,
    });
  }

  public togglePassword(): void {
    this.showPassword = !this.showPassword;
  }

  public goBack(): void {
    this.router.navigate(['/welcome']);
  }

  public goToSignup(): void {
    this.router.navigate(['/signup']);
  }

  public openForgotPasswordModal(): void {
    const emailVal = this.loginForm.get('email')?.value || '';
    this.recoveryEmail = typeof emailVal === 'string' ? emailVal.trim() : '';
    this.recoverySubmitted = false;
    this.recoveryError = null;
    this.isForgotModalOpen = true;
  }

  public closeForgotPasswordModal(): void {
    this.isForgotModalOpen = false;
  }

  public submitRecoveryRequest(): void {
    this.recoveryError = null;
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!this.recoveryEmail || !emailRegex.test(this.recoveryEmail)) {
      this.recoveryError = 'Please enter a valid email address.';
      return;
    }
    this.recoverySubmitted = true;
  }

  public onSubmit(): void {
    if (this.loginForm.invalid) {
      this.loginForm.markAllAsTouched();
      return;
    }

    this.isLoading = true;
    this.errorMessage = null;

    const { email, password, rememberMe } = this.loginForm.value;
    this.authService
      .login({ email: email!.trim(), password: password! }, !!rememberMe)
      .subscribe({
        next: async () => {
          try {
            await this.guestMigrationService.migrateGuestData(true);
          } catch {
            // Migration is best-effort and non-blocking
          }
          this.isLoading = false;
          this.router.navigate(['/tabs/home']);
        },
        error: (err) => {
          this.isLoading = false;
          if (err.status === 0 || err.status === 502 || err.status === 504) {
            this.errorMessage =
              'Authentication server is currently unreachable. You can continue planning trips as a Guest or explore using the Demo Persona below.';
          } else {
            this.errorMessage =
              err.error?.detail ||
              'Invalid email or password. Please check your credentials and try again.';
          }
        },
      });
  }

  public onDemoLogin(): void {
    this.isLoading = true;
    this.errorMessage = null;
    this.authService.loginDemo().subscribe({
      next: async () => {
        try {
          await this.guestMigrationService.migrateGuestData(true);
        } catch {
          // Migration is best-effort and non-blocking
        }
        this.isLoading = false;
        const toast = await this.toastController.create({
          message: 'Signed in as Demo Traveler (Pattranite Persona)',
          duration: 2000,
          position: 'top',
          color: 'primary',
        });
        await toast.present();
        this.router.navigate(['/tabs/home']);
      },
      error: () => {
        this.isLoading = false;
      },
    });
  }

  public async onGoogleLogin(): Promise<void> {
    const toast = await this.toastController.create({
      message: 'Google Sign-In is disabled in this pilot build.',
      duration: 2500,
      position: 'top',
    });
    await toast.present();
  }

  public async onAppleLogin(): Promise<void> {
    const toast = await this.toastController.create({
      message: 'Apple Sign-In is disabled in this pilot build.',
      duration: 2500,
      position: 'top',
    });
    await toast.present();
  }

  public onForgotPassword(): void {
    const emailControl = this.loginForm.get('email');
    if (emailControl && emailControl.value && emailControl.valid) {
      this.recoveryEmail = String(emailControl.value).trim();
    }
    this.openForgotPasswordModal();
  }
}
