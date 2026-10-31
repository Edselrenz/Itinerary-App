import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  AbstractControl,
  FormControl,
  FormGroup,
  ReactiveFormsModule,
  ValidationErrors,
  ValidatorFn,
  Validators,
} from '@angular/forms';
import { Router } from '@angular/router';
import {
  IonContent,
  IonIcon,
  IonSpinner,
  ToastController,
} from '@ionic/angular';
import { addIcons } from 'ionicons';
import {
  alertCircleOutline,
  arrowBackOutline,
  checkmarkCircle,
  eyeOffOutline,
  eyeOutline,
  keyOutline,
  logoApple,
  mailOutline,
} from 'ionicons/icons';
import { AuthService } from '../../../core/services/auth.service';
import { GuestMigrationService } from '../../../core/services/guest-migration.service';

export const passwordMatchValidator: ValidatorFn = (
  control: AbstractControl
): ValidationErrors | null => {
  const password = control.get('password');
  const confirm = control.get('confirmPassword');
  if (!password || !confirm) {
    return null;
  }
  return password.value === confirm.value ? null : { passwordsMismatch: true };
};

@Component({
  selector: 'app-signup',
  templateUrl: './signup.page.html',
  styleUrls: ['./signup.page.scss'],
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    IonContent,
    IonIcon,
    IonSpinner,
  ],
})
export class SignupPage {
  public showPassword = false;
  public showConfirmPassword = false;
  public isLoading = false;
  public errorMessage: string | null = null;

  public signupForm = new FormGroup(
    {
      firstName: new FormControl('', [Validators.required]),
      middleInitial: new FormControl(''),
      lastName: new FormControl('', [Validators.required]),
      email: new FormControl('', [Validators.required, Validators.email]),
      password: new FormControl('', [
        Validators.required,
        Validators.minLength(8),
      ]),
      confirmPassword: new FormControl('', [Validators.required]),
    },
    { validators: [passwordMatchValidator] }
  );

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
      checkmarkCircle,
      eyeOutline,
      eyeOffOutline,
      logoApple,
      alertCircleOutline,
    });
  }

  public togglePassword(): void {
    this.showPassword = !this.showPassword;
  }

  public toggleConfirmPassword(): void {
    this.showConfirmPassword = !this.showConfirmPassword;
  }

  public goBack(): void {
    this.router.navigate(['/welcome']);
  }

  public goToLogin(): void {
    this.router.navigate(['/login']);
  }

  public onSubmit(): void {
    if (this.signupForm.invalid) {
      this.signupForm.markAllAsTouched();
      return;
    }

    this.isLoading = true;
    this.errorMessage = null;

    const val = this.signupForm.value;
    const emailStr = (val.email || '').trim();
    const rawUsername = (
      emailStr.split('@')[0] || `${val.firstName || ''}${val.lastName || ''}`
    ).replace(/[^a-zA-Z0-9_]/g, '');
    const username =
      rawUsername.length >= 3
        ? rawUsername.slice(0, 50)
        : `${rawUsername}usr`.slice(0, 50);

    this.authService
      .register({
        first_name: (val.firstName || '').trim(),
        last_name: (val.lastName || '').trim(),
        username,
        email: emailStr,
        password: val.password!,
      })
      .subscribe({
        next: async () => {
          try {
            await this.guestMigrationService.migrateGuestData(true);
          } catch {
            // Non-blocking
          }
          this.isLoading = false;
          this.router.navigate(['/tabs/home']);
        },
        error: (err) => {
          this.isLoading = false;
          this.errorMessage =
            err.error?.detail ||
            'Unable to complete registration. Please check your information.';
        },
      });
  }

  public async onGoogleSignup(): Promise<void> {
    const toast = await this.toastController.create({
      message: 'Google Sign-Up is configured for production credentials.',
      duration: 2500,
      position: 'top',
    });
    await toast.present();
  }

  public async onAppleSignup(): Promise<void> {
    const toast = await this.toastController.create({
      message: 'Apple Sign-Up is disabled in this pilot build.',
      duration: 2500,
      position: 'top',
    });
    await toast.present();
  }
}
