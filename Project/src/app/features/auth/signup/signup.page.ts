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
  atOutline,
  checkmarkCircle,
  eyeOffOutline,
  eyeOutline,
  keyOutline,
  logoApple,
  mailOutline,
  personOutline,
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
      username: new FormControl('', [
        Validators.required,
        Validators.minLength(3),
        Validators.maxLength(50),
        Validators.pattern(/^[a-zA-Z0-9_.-]+$/),
      ]),
      email: new FormControl('', [Validators.required, Validators.email]),
      password: new FormControl('', [
        Validators.required,
        Validators.minLength(8),
      ]),
      confirmPassword: new FormControl('', [Validators.required]),
    },
    { validators: [passwordMatchValidator] }
  );

  public isUsernameCustom = false;

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
      atOutline,
      personOutline,
    });
  }

  public autoSuggestUsername(): void {
    if (this.isUsernameCustom) return;
    const fn = (this.signupForm.get('firstName')?.value || '').trim().toLowerCase().replace(/[^a-z0-9]/g, '');
    const ln = (this.signupForm.get('lastName')?.value || '').trim().toLowerCase().replace(/[^a-z0-9]/g, '');
    const usernameCtrl = this.signupForm.get('username');
    if (usernameCtrl) {
      if (fn && ln) {
        usernameCtrl.setValue(`${fn}_${ln}`, { emitEvent: false });
      } else if (fn) {
        usernameCtrl.setValue(fn, { emitEvent: false });
      }
    }
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
    const username = (val.username || '').trim().toLowerCase();
    const mid = (val.middleInitial || '').trim().replace(/\.+$/, '');
    const firstName = mid ? `${val.firstName!.trim()} ${mid}.` : val.firstName!.trim();
    const lastName = (val.lastName || '').trim();

    this.authService
      .register({
        first_name: firstName,
        last_name: lastName,
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
      message: 'Google Sign-Up is disabled in this pilot build.',
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
