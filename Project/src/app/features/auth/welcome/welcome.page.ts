import { CommonModule } from '@angular/common';
import type { OnInit } from '@angular/core';
import { Component, inject } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import {
  IonButton,
  IonContent,
  IonIcon,
} from '@ionic/angular';
import { addIcons } from 'ionicons';
import { person } from 'ionicons/icons';

@Component({
  selector: 'app-welcome',
  templateUrl: './welcome.page.html',
  styleUrls: ['./welcome.page.scss'],
  standalone: true,
  imports: [CommonModule, IonContent, IonButton, IonIcon],
})
export class WelcomePage implements OnInit {
  public isAfterLogout = false;

  private router = inject(Router);
  private route = inject(ActivatedRoute);

  constructor() {
    addIcons({ person });
  }

  public ngOnInit(): void {
    this.route.queryParams.subscribe((params) => {
      this.isAfterLogout = params['loggedOut'] === 'true' || this.router.url.includes('after-logout');
    });
  }

  public goToLogin(): void {
    this.router.navigate(['/login']);
  }

  public goToSignup(): void {
    this.router.navigate(['/signup']);
  }

  public goToGuest(): void {
    this.router.navigate(['/guest']);
  }
}
