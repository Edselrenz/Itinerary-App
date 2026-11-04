import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
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

  constructor(
    private router: Router,
    private authService: AuthService,
    private guestMigrationService: GuestMigrationService,
    private toastController: ToastController
  ) {
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
          this.errorMessage =
            err.error?.detail ||
            'Unable to log in. Please check your credentials or network connection.';
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

  public async onForgotPassword(): Promise<void> {
    const emailControl = this.loginForm.get('email');
    if (!emailControl || emailControl.invalid || !emailControl.value) {
      this.openForgotPasswordModal();
      const toast = await this.toastController.create({
        message: 'Please enter a valid email address first.',
        duration: 3000,
        position: 'top',
        color: 'warning',
      });
      await toast.present();
      return;
    }

    const email = String(emailControl.value).trim();
    this.openForgotPasswordModal();
    const toast = await this.toastController.create({
      message: `Self-service password reset is disabled in this pilot build. Please contact your administrator to reset credentials for ${email}.`,
      duration: 4000,
      position: 'top',
    });
    await toast.present();
  }
}
