import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { ConnectivityService } from './connectivity.service';
import { environment } from '../../../environments/environment';

describe('ConnectivityService', () => {
  let service: ConnectivityService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        ConnectivityService,
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });
    service = TestBed.inject(ConnectivityService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created with initial offline status as false', () => {
    expect(service).toBeTruthy();
    let isOffline = true;
    service.isHostOffline$.subscribe((val) => (isOffline = val));
    expect(isOffline).toBe(false);
  });

  it('updates host offline status when setHostOffline is called', () => {
    let isOffline = false;
    service.isHostOffline$.subscribe((val) => (isOffline = val));

    service.setHostOffline(true);
    expect(isOffline).toBe(true);

    service.setHostOffline(false);
    expect(isOffline).toBe(false);
  });

  it('dismisses banner manually and prevents re-triggering until recovery', () => {
    service.setHostOffline(true);
    let isOffline = false;
    service.isHostOffline$.subscribe((val) => (isOffline = val));
    expect(isOffline).toBe(true);

    service.dismissBanner();
    expect(isOffline).toBe(false);

    // Another offline notification while dismissed should stay hidden
    service.setHostOffline(true);
    expect(isOffline).toBe(false);

    // Recovery clears manual dismissal
    service.setHostOffline(false);
    expect(isOffline).toBe(false);

    // Subsequent offline triggers banner again
    service.setHostOffline(true);
    expect(isOffline).toBe(true);
  });

  it('probes health endpoint and recovers if online', () => {
    service.setHostOffline(true);
    let isOffline = true;
    service.isHostOffline$.subscribe((val) => (isOffline = val));

    service.checkHostHealth().subscribe((success) => {
      expect(success).toBe(true);
    });

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/health`);
    expect(req.request.method).toBe('GET');
    req.flush({ status: 'ok', province_scope: 'Nueva Ecija', environment: 'development' });

    expect(isOffline).toBe(false);
  });

  it('probes health endpoint and remains offline if check fails', () => {
    let isOffline = false;
    service.isHostOffline$.subscribe((val) => (isOffline = val));

    service.checkHostHealth().subscribe((success) => {
      expect(success).toBe(false);
    });

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/health`);
    req.error(new ProgressEvent('error'));

    expect(isOffline).toBe(true);
  });

  it('SEC-01: validates and restricts custom API URLs to trusted hostnames', () => {
    // Trusted hostnames succeed
    expect(service.isValidApiUrl('https://anybody-cube-surprise.ngrok-free.dev/api/v1')).toBe(true);
    expect(service.isValidApiUrl('http://localhost:8000/api/v1')).toBe(true);
    expect(service.isValidApiUrl('http://127.0.0.1:8000/api/v1')).toBe(true);

    // Untrusted hostnames fail
    expect(service.isValidApiUrl('https://evil-attacker.com/api/v1')).toBe(false);
    expect(service.isValidApiUrl('http://untrusted-domain.org')).toBe(false);
    expect(service.isValidApiUrl('not-a-valid-url')).toBe(false);

    // Setting untrusted URL throws error and leaves localStorage clean
    localStorage.removeItem('ne_custom_api_url');
    expect(() => service.setCustomApiUrl('https://evil-attacker.com/api/v1')).toThrowError(/trusted host/);
    expect(localStorage.getItem('ne_custom_api_url')).toBeNull();

    // Setting trusted URL succeeds
    service.setCustomApiUrl('https://anybody-cube-surprise.ngrok-free.dev/api/v1');
    expect(localStorage.getItem('ne_custom_api_url')).toBe('https://anybody-cube-surprise.ngrok-free.dev/api/v1');
    localStorage.removeItem('ne_custom_api_url');
  });
});
