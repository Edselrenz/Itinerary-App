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
  IonContent,
  IonIcon,
  IonSpinner,
  ToastController,
} from '@ionic/angular';
import { addIcons } from 'ionicons';
import {
  alertCircleOutline,
  arrowBackOutline,
  eyeOffOutline,
  eyeOutline,
  keyOutline,
  logoApple,
  mailOutline,
} from 'ionicons/icons';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-login',
  templateUrl: './login.page.html',
  styleUrls: ['./login.page.scss'],
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    IonContent,
    IonIcon,
    IonSpinner,
  ],
})
export class LoginPage {
  public showPassword = false;
  public isLoading = false;
  public errorMessage: string | null = null;

  public loginForm = new FormGroup({
    email: new FormControl('', [Validators.required]),
    password: new FormControl('', [Validators.required]),
    rememberMe: new FormControl(false),
  });

  constructor(
    private router: Router,
    private authService: AuthService,
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

  public async onGoogleLogin(): Promise<void> {
    const toast = await this.toastController.create({
      message: 'Google Sign-In is configured for production credentials.',
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
    const toast = await this.toastController.create({
      message: 'Password reset link will be sent to your registered email address.',
      duration: 3000,
      position: 'top',
    });
    await toast.present();
  }
}
