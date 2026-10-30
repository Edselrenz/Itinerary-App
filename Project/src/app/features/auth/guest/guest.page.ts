import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import {
  IonButton,
  IonContent,
  IonIcon,
} from '@ionic/angular';
import { addIcons } from 'ionicons';
import { arrowBack } from 'ionicons/icons';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-guest',
  templateUrl: './guest.page.html',
  styleUrls: ['./guest.page.scss'],
  standalone: true,
  imports: [CommonModule, IonContent, IonButton, IonIcon],
})
export class GuestPage {
  constructor(
    private router: Router,
    private authService: AuthService
  ) {
    addIcons({ arrowBack });
  }

  public goBack(): void {
    this.router.navigate(['/welcome']);
  }

  public async continueAsGuest(): Promise<void> {
    await this.authService.continueAsGuest();
    this.router.navigate(['/tabs/home']);
  }

  public createAccount(): void {
    this.router.navigate(['/signup']);
  }
}

