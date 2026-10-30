import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  FormControl,
  FormGroup,
  ReactiveFormsModule,
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
  logoApple,
  logoGoogle,
  mailOutline,
} from 'ionicons/icons';
import { environment } from '../../../../environments/environment';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-login',
  templateUrl: './login.page.html',
  styleUrls: ['./login.page.scss'],
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
export class LoginPage {
  public showPassword = false;
  public isLoading = false;
  public errorMessage: string | null = null;
  public readonly enableAppleAuth = environment.enableAppleAuth;

  public loginForm = new FormGroup({
    email: new FormControl('', [Validators.required]),
    password: new FormControl('', [Validators.required]),
    rememberMe: new FormControl(false),
  });

  constructor(
    private router: Router,
    private authService: AuthService
  ) {
    addIcons({
      arrowBackOutline,
      mailOutline,
      lockClosedOutline,
      eyeOutline,
      eyeOffOutline,
      logoGoogle,
      logoApple,
      alertCircleOutline,
    });
  }

  public togglePassword(): void {
    this.showPassword = !this.showPassword;
  }

  public onSubmit(): void {
    if (this.loginForm.invalid) {
      this.loginForm.markAllAsTouched();
      return;
    }

    this.isLoading = true;
    this.errorMessage = null;

    const { email, password } = this.loginForm.value;
    this.authService
      .login({ email: email!.trim(), password: password! })
      .subscribe({
        next: () => {
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

  public onGoogleLogin(): void {
    // Note: In development/pilot, Google OAuth requires configured Client ID and Google Sign-In SDK
    alert(
      'Google Sign-In requires your Google Client ID to be configured in environment.ts.'
    );
  }

  public onAppleLogin(): void {
    if (!this.enableAppleAuth) {
      alert('Apple Sign-In is disabled in this pilot build until Apple credentials exist.');
    }
  }

  public onForgotPassword(): void {
    alert('Please contact your administrator or use guest mode for password reset.');
  }

  public goToSignup(): void {
    this.router.navigate(['/signup']);
  }
}

