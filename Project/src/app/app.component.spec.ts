import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
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
  };

  beforeEach(async () => {
    vi.clearAllMocks();
    isHostOfflineSub.next(false);
    isCheckingHealthSub.next(false);

    await TestBed.configureTestingModule({
      imports: [AppComponent],
      providers: [
        provideRouter([]),
        { provide: ConnectivityService, useValue: mockConnectivityService },
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
  });

  it('calls checkHostHealth when retryConnection is triggered', () => {
    component.retryConnection();
    expect(mockConnectivityService.checkHostHealth).toHaveBeenCalled();
  });

  it('calls dismissBanner when dismissOfflineBanner is triggered', () => {
    component.dismissOfflineBanner();
    expect(mockConnectivityService.dismissBanner).toHaveBeenCalled();
  });

  it('renders offline banner when isHostOffline$ emits true', () => {
    isHostOfflineSub.next(true);
    fixture.detectChanges();

    const banner = fixture.nativeElement.querySelector('.offline-host-banner');
    expect(banner).toBeTruthy();
    expect(banner.textContent).toContain('Pilot Backend Offline');
  });
});
