import { Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonApp, IonIcon, IonRouterOutlet, IonSpinner } from '@ionic/angular';
import { addIcons } from 'ionicons';
import { closeOutline, cloudOfflineOutline, refreshOutline, settingsOutline } from 'ionicons/icons';
import { ConnectivityService } from './core/services/connectivity.service';

@Component({
  selector: 'app-root',
  templateUrl: 'app.component.html',
  styleUrls: ['app.component.scss'],
  standalone: true,
  imports: [CommonModule, IonApp, IonRouterOutlet, IonIcon, IonSpinner],
})
export class AppComponent implements OnInit, OnDestroy {
  public showSplashScreen = true;
  public isFadingOut = false;

  private autoDismissTimer?: ReturnType<typeof setTimeout>;
  private touchStartY = 0;
  private touchStartX = 0;

  constructor(public connectivityService: ConnectivityService) {
    addIcons({
      cloudOfflineOutline,
      refreshOutline,
      closeOutline,
      settingsOutline,
    });
  }

  public ngOnInit(): void {
    // Auto-dismiss after 2.8 seconds once the underlying frontend has initialized
    this.autoDismissTimer = setTimeout(() => {
      this.dismissSplash();
    }, 2800);
  }

  public ngOnDestroy(): void {
    if (this.autoDismissTimer) {
      clearTimeout(this.autoDismissTimer);
    }
  }

  public retryConnection(): void {
    this.connectivityService.checkHostHealth().subscribe();
  }

  public configureApiUrl(): void {
    const current = this.connectivityService.currentApiUrl;
    const entered = window.prompt(
      'Configure Backend URL (e.g. Cloudflare tunnel https://*.trycloudflare.com or custom host):',
      current
    );
    if (entered !== null) {
      this.connectivityService.setCustomApiUrl(entered.trim() ? entered.trim() : null);
      this.connectivityService.checkHostHealth().subscribe();
    }
  }

  public dismissOfflineBanner(): void {
    this.connectivityService.dismissBanner();
  }

  public dismissSplash(): void {
    if (this.isFadingOut || !this.showSplashScreen) {
      return;
    }

    if (this.autoDismissTimer) {
      clearTimeout(this.autoDismissTimer);
      this.autoDismissTimer = undefined;
    }

    this.isFadingOut = true;

    // Remove from DOM after smooth 500ms fade/scale animation completes
    setTimeout(() => {
      this.showSplashScreen = false;
    }, 500);
  }

  public onTouchStart(event: TouchEvent): void {
    if (event.touches.length > 0) {
      this.touchStartY = event.touches[0].clientY;
      this.touchStartX = event.touches[0].clientX;
    }
  }

  public onTouchEnd(event: TouchEvent): void {
    if (event.changedTouches.length > 0) {
      const deltaY = event.changedTouches[0].clientY - this.touchStartY;
      const deltaX = event.changedTouches[0].clientX - this.touchStartX;

      // Any gesture / swipe threshold of 25px triggers immediate dismissal
      if (Math.abs(deltaY) > 25 || Math.abs(deltaX) > 25) {
        this.dismissSplash();
      }
    }
  }
}
