import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import {
  IonButton,
  IonContent,
  IonIcon,
  IonModal,
} from '@ionic/angular';
import { addIcons } from 'ionicons';
import {
  arrowForwardOutline,
  closeOutline,
  person,
} from 'ionicons/icons';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-welcome',
  templateUrl: './welcome.page.html',
  styleUrls: ['./welcome.page.scss'],
  standalone: true,
  imports: [CommonModule, IonContent, IonButton, IonIcon, IonModal],
})
export class WelcomePage {
  public isGuestModalOpen = false;

  constructor(
    private router: Router,
    private authService: AuthService
  ) {
    addIcons({
      person,
      closeOutline,
      arrowForwardOutline,
    });
  }

  public goToLogin(): void {
    this.router.navigate(['/login']);
  }

  public goToSignup(): void {
    this.router.navigate(['/signup']);
  }

  public openGuestModal(): void {
    this.isGuestModalOpen = true;
  }

  public closeGuestModal(): void {
    this.isGuestModalOpen = false;
  }

  public async continueAsGuest(): Promise<void> {
    this.isGuestModalOpen = false;
    await this.authService.continueAsGuest();
    this.router.navigate(['/tabs/home']);
  }
}
