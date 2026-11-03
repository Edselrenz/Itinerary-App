import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { AlertController, ToastController } from '@ionic/angular';
import { BehaviorSubject, of } from 'rxjs';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { AppComponent } from './app.component';
import { ConnectivityService } from './core/services/connectivity.service';

describe('AppComponent', () => {
  let fixture: ComponentFixture<AppComponent>;
  let component: AppComponent;

  const isHostOfflineSub = new BehaviorSubject<boolean>(false);
  const isCheckingHealthSub = new BehaviorSubject<boolean>(false);

  const mockConnectivityService = {
    isHostOffline$: isHostOfflineSub.asObservable(),
    isCheckingHealth$: isCheckingHealthSub.asObservable(),
    checkHostHealth: vi.fn().mockReturnValue(of(true)),
    dismissBanner: vi.fn(),
    currentApiUrl: 'https://anybody-cube-surprise.ngrok-free.dev/api/v1',
    isValidApiUrl: vi.fn((url: string) => url.includes('ngrok') || url.includes('trycloudflare') || url.includes('localhost')),
    setCustomApiUrl: vi.fn(),
    clearCustomApiUrl: vi.fn(),
  };

  const mockToast = {
    present: vi.fn().mockResolvedValue(undefined),
  };
  const mockToastController = {
    create: vi.fn().mockResolvedValue(mockToast),
  };

  const mockAlert = {
    present: vi.fn().mockResolvedValue(undefined),
  };
  const mockAlertController = {
    create: vi.fn().mockResolvedValue(mockAlert),
  };

  beforeEach(async () => {
    vi.clearAllMocks();
    if (typeof window !== 'undefined' && window.sessionStorage) {
      sessionStorage.clear();
    }
    isHostOfflineSub.next(false);
    isCheckingHealthSub.next(false);
    mockConnectivityService.checkHostHealth.mockReturnValue(of(true));

    await TestBed.configureTestingModule({
      imports: [AppComponent],
      providers: [
        provideRouter([]),
        { provide: ConnectivityService, useValue: mockConnectivityService },
        { provide: ToastController, useValue: mockToastController },
        { provide: AlertController, useValue: mockAlertController },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(AppComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create the app and initialize splash screen', () => {
    expect(component).toBeTruthy();
    expect(component.showSplashScreen).toBe(true);
  });

  it('dismisses splash screen on demand', () => {
    component.dismissSplash();
    expect(component.isFadingOut).toBe(true);
    expect(sessionStorage.getItem('ne_splash_seen_v1')).toBe('true');
  });

  it('skips splash screen if already seen in current session (UI-05)', () => {
    sessionStorage.setItem('ne_splash_seen_v1', 'true');
    const newComponent = new AppComponent(mockConnectivityService as any, mockToastController as any);
    newComponent.ngOnInit();
    expect(newComponent.showSplashScreen).toBe(false);
  });

  it('dismisses splash screen when Escape key is pressed (DEF-09)', () => {
    expect(component.showSplashScreen).toBe(true);
    component.onEscapeKey();
    expect(component.isFadingOut).toBe(true);
  });

  it('calls checkHostHealth and shows success toast when retryConnection succeeds', async () => {
    mockConnectivityService.checkHostHealth.mockReturnValue(of(true));
    component.retryConnection();
    expect(mockConnectivityService.checkHostHealth).toHaveBeenCalled();
    // Allow microtasks to resolve
    await new Promise((resolve) => setTimeout(resolve, 10));
    expect(mockToastController.create).toHaveBeenCalledWith(
      expect.objectContaining({
        color: 'success',
      })
    );
  });

  it('shows warning toast when retryConnection fails while server is offline', async () => {
    mockConnectivityService.checkHostHealth.mockReturnValue(of(false));
    component.retryConnection();
    expect(mockConnectivityService.checkHostHealth).toHaveBeenCalled();
    await new Promise((resolve) => setTimeout(resolve, 10));
    expect(mockToastController.create).toHaveBeenCalledWith(
      expect.objectContaining({
        color: 'warning',
      })
    );
  });

  it('calls dismissBanner when dismissOfflineBanner is triggered', () => {
    component.dismissOfflineBanner();
    expect(mockConnectivityService.dismissBanner).toHaveBeenCalled();
  });

  it('renders offline banner and wires Retry and Dismiss actions', () => {
    isHostOfflineSub.next(true);
    fixture.detectChanges();

    const banner = fixture.nativeElement.querySelector('.offline-host-banner');
    expect(banner).toBeTruthy();
    expect(banner.textContent).toContain('Offline Mode');
    expect(banner.textContent).toContain('Cloud sync paused');

    // Verify retry button is wired
    const retryBtn = banner.querySelector('.banner-retry-btn');
    expect(retryBtn).toBeTruthy();
    retryBtn.click();
    expect(mockConnectivityService.checkHostHealth).toHaveBeenCalled();

    // Verify dismiss button is wired
    const dismissBtn = banner.querySelector('.banner-dismiss-btn');
    expect(dismissBtn).toBeTruthy();
    dismissBtn.click();
    expect(mockConnectivityService.dismissBanner).toHaveBeenCalled();
  });
});
