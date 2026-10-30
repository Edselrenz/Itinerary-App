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
  IonBackButton,
  IonButton,
  IonButtons,
  IonContent,
  IonHeader,
  IonIcon,
  IonInput,
  IonItem,
  IonLabel,
  IonSpinner,
  IonToolbar,
} from '@ionic/angular';
import { addIcons } from 'ionicons';
import {
  alertCircleOutline,
  arrowBackOutline,
  eyeOffOutline,
  eyeOutline,
  lockClosedOutline,
  mailOutline,
  personOutline,
} from 'ionicons/icons';
import { AuthService } from '../../../core/services/auth.service';

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
    IonHeader,
    IonToolbar,
    IonButtons,
    IonBackButton,
    IonContent,
    IonLabel,
    IonItem,
    IonInput,
    IonButton,
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

  constructor(
    private router: Router,
    private authService: AuthService
  ) {
    addIcons({
      arrowBackOutline,
      personOutline,
      mailOutline,
      lockClosedOutline,
      eyeOutline,
      eyeOffOutline,
      alertCircleOutline,
    });
  }

  public togglePassword(): void {
    this.showPassword = !this.showPassword;
  }

  public toggleConfirmPassword(): void {
    this.showConfirmPassword = !this.showConfirmPassword;
  }

  public onSubmit(): void {
    if (this.signupForm.invalid) {
      this.signupForm.markAllAsTouched();
      return;
    }

    this.isLoading = true;
    this.errorMessage = null;

    const val = this.signupForm.value;
    this.authService
      .register({
        first_name: val.firstName!.trim(),
        last_name: val.lastName!.trim(),
        username: val.username!.trim(),
        email: val.email!.trim(),
        password: val.password!,
      })
      .subscribe({
        next: () => {
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

  public goToLogin(): void {
    this.router.navigate(['/login']);
  }
}

