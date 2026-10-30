import { Component, OnInit } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { Router } from '@angular/router';
import {
  IonButton,
  IonContent,
  IonHeader,
  IonIcon,
  IonTitle,
  IonToolbar,
} from '@ionic/angular';
import { addIcons } from 'ionicons';
import {
  calendarOutline,
  checkmarkCircle,
  cloudOfflineOutline,
  logOutOutline,
  person,
  personOutline,
} from 'ionicons/icons';
import { User } from '../../core/models/auth.models';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-profile',
  templateUrl: './profile.page.html',
  styleUrls: ['./profile.page.scss'],
  standalone: true,
  imports: [
    CommonModule,
    DatePipe,
    IonHeader,
    IonToolbar,
    IonTitle,
    IonContent,
    IonButton,
    IonIcon,
  ],
})
export class ProfilePage implements OnInit {
  public currentUser: User | null = null;

  constructor(
    private router: Router,
    private authService: AuthService
  ) {
    addIcons({
      person,
      personOutline,
      checkmarkCircle,
      calendarOutline,
      logOutOutline,
      cloudOfflineOutline,
    });
  }

  public ngOnInit(): void {
    this.authService.currentUser$.subscribe((user) => {
      this.currentUser = user;
    });
  }

  public async onLogout(): Promise<void> {
    await this.authService.logout();
    this.router.navigate(['/welcome']);
  }

  public goToLogin(): void {
    this.router.navigate(['/login']);
  }

  public goToSignup(): void {
    this.router.navigate(['/signup']);
  }
}

