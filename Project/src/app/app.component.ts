import { CommonModule, Location } from '@angular/common';
import type { OnDestroy, OnInit } from '@angular/core';
import { ChangeDetectorRef, Component, HostListener, inject } from '@angular/core';
import { App } from '@capacitor/app';
import { Capacitor } from '@capacitor/core';
import { StatusBar, Style } from '@capacitor/status-bar';
import { IonApp, IonIcon, IonRouterOutlet, IonSpinner, ModalController, ToastController } from '@ionic/angular';
import { addIcons } from 'ionicons';
import { closeOutline, cloudOfflineOutline, refreshOutline } from 'ionicons/icons';

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

  public connectivityService = inject(ConnectivityService);
  private toastController = inject(ToastController);
  private modalController = inject(ModalController, { optional: true });
  private location = inject(Location);
  private cdr = inject(ChangeDetectorRef);

  constructor() {
    addIcons({
      cloudOfflineOutline,
      refreshOutline,
      closeOutline,
    });
  }

  public ngOnInit(): void {
    // QA-14C: Restore user theme mode preference on boot
    if (typeof localStorage !== 'undefined' && typeof document !== 'undefined') {
      const savedTheme = localStorage.getItem('ne_theme_mode');
      if (savedTheme === 'dark') {
        document.body.classList.add('dark');
      } else if (savedTheme === 'light') {
        document.body.classList.remove('dark');
      }
    }

    // Configure native status bar and Android hardware back-button navigation
    if (Capacitor.isNativePlatform()) {
      const isDark = typeof document !== 'undefined' && document.body.classList.contains('dark');
      StatusBar.setStyle({ style: isDark ? Style.Dark : Style.Light }).catch(() => {});
      StatusBar.setBackgroundColor({ color: isDark ? '#0b0f19' : '#0084ff' }).catch(() => {});

      App.addListener('backButton', async ({ canGoBack }) => {
        if (this.modalController) {
          const topModal = await this.modalController.getTop();
          if (topModal) {
            await topModal.dismiss();
            return;
          }
        }
        const currentHash = typeof window !== 'undefined' ? window.location.hash || '' : '';
        const isRootRoute =
          currentHash === '' ||
          currentHash === '#/' ||
          currentHash.startsWith('#/welcome') ||
          currentHash.startsWith('#/tabs/home');

        if (canGoBack && !isRootRoute) {
          this.location.back();
        } else {
          await App.exitApp();
        }
      });
    }

    // Proactively verify server connectivity on application launch
    this.connectivityService.checkHostHealth().subscribe();

    // Check if splash screen was already dismissed in the current session (UI-05)
    if (typeof window !== 'undefined' && window.sessionStorage) {
      if (sessionStorage.getItem('ne_splash_seen_v1') === 'true') {
        this.showSplashScreen = false;
        return;
      }
    }

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
   * If online -> reloads page data.
   * If offline -> shows subtle status toast without exposing technical config.
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
        const toast = await this.toastController.create({
          message: 'Server is currently offline. Your saved trips and places remain available.',
          duration: 3500,
          color: 'warning',
          position: 'top',
        });
        await toast.present();
      }
    });
  }

  public dismissOfflineBanner(): void {
    this.connectivityService.dismissBanner();
  }

  public dismissSplash(): void {
    if (this.isFadingOut || !this.showSplashScreen) {
      return;
    }

    if (typeof window !== 'undefined' && window.sessionStorage) {
      sessionStorage.setItem('ne_splash_seen_v1', 'true');
    }

    if (this.autoDismissTimer) {
      clearTimeout(this.autoDismissTimer);
      this.autoDismissTimer = undefined;
    }

    this.isFadingOut = true;

    // Remove from DOM after smooth 500ms fade/scale animation completes
    setTimeout(() => {
      this.showSplashScreen = false;
      this.isFadingOut = false;
      this.cdr.detectChanges();
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
