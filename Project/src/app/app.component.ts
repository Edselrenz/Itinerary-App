import { Component, HostListener, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AlertController, IonApp, IonIcon, IonRouterOutlet, IonSpinner, ToastController } from '@ionic/angular';
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

  constructor(
    public connectivityService: ConnectivityService,
    private alertController: AlertController,
    private toastController: ToastController
  ) {
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

  @HostListener('window:keydown.escape')
  public onEscapeKey(): void {
    if (this.showSplashScreen) {
      this.dismissSplash();
    }
  }

  /**
   * Attempts to reconnect to the configured backend server.
   * If online -> shows success toast.
   * If unreachable -> opens connection settings alert so user can view/change tunnel URL.
   */
  public retryConnection(): void {
    this.connectivityService.checkHostHealth().subscribe(async (online) => {
      if (online) {
        const toast = await this.toastController.create({
          message: 'Connected to backend server! Reloading data...',
          duration: 2500,
          color: 'success',
          position: 'top',
        });
        await toast.present();
        setTimeout(() => {
          window.location.reload();
        }, 800);
      } else {
        await this.openServerConfigAlert(true);
      }
    });
  }

  /**
   * Opens interactive alert allowing inspection and configuration of backend URL.
   */
  public async openServerConfigAlert(isRetryFailure = false): Promise<void> {
    const currentUrl = this.connectivityService.currentApiUrl;
    const alert = await this.alertController.create({
      header: isRetryFailure ? 'Server Connection Failed' : 'Server Connection Settings',
      subHeader: isRetryFailure
        ? `Could not reach ${currentUrl}`
        : 'Configure Backend Tunnel or Server URL',
      message:
        'The app is currently in offline mode. Enter your permanent Cloudflare Worker proxy (https://*.workers.dev), Cloudflare Tunnel (https://*.trycloudflare.com), ngrok URL, or localhost address below.',
      inputs: [
        {
          name: 'apiUrl',
          type: 'url',
          placeholder: 'https://your-api.workers.dev',
          value: currentUrl,
        },
      ],
      buttons: [
        {
          text: 'Dismiss',
          role: 'cancel',
        },
        {
          text: 'Reset to Default',
          handler: () => {
            this.connectivityService.clearCustomApiUrl();
            this.connectivityService.checkHostHealth().subscribe(async (online) => {
              const toast = await this.toastController.create({
                message: online
                  ? 'Reset to default and connected successfully!'
                  : `Reset to default (${this.connectivityService.currentApiUrl}), but host is currently unreachable.`,
                duration: 3500,
                color: online ? 'success' : 'warning',
                position: 'top',
              });
              await toast.present();
            });
          },
        },
        {
          text: 'Save & Connect',
          handler: (data) => {
            const rawUrl = data?.apiUrl?.trim();
            if (!rawUrl) {
              return true;
            }
            if (!this.connectivityService.isValidApiUrl(rawUrl)) {
              this.showInvalidUrlToast();
              return false; // keep alert open
            }
            try {
              this.connectivityService.setCustomApiUrl(rawUrl);
              this.connectivityService.checkHostHealth().subscribe(async (online) => {
                const toast = await this.toastController.create({
                  message: online
                    ? 'Connected to backend server! Reloading data...'
                    : `Saved URL (${this.connectivityService.currentApiUrl}), but host check failed. Verify tunnel is running.`,
                  duration: 3500,
                  color: online ? 'success' : 'warning',
                  position: 'top',
                });
                await toast.present();
                if (online) {
                  setTimeout(() => {
                    window.location.reload();
                  }, 800);
                }
              });
              return true;
            } catch {
              this.showInvalidUrlToast();
              return false;
            }
          },
        },
      ],
    });
    await alert.present();
  }

  public async showInvalidUrlToast(): Promise<void> {
    const toast = await this.toastController.create({
      message: 'Invalid URL. Host must be localhost, Cloudflare Worker (*.workers.dev), or trusted tunnel (*.trycloudflare.com, *.ngrok-free.dev).',
      duration: 3500,
      color: 'danger',
      position: 'top',
    });
    await toast.present();
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
