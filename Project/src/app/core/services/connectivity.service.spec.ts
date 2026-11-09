import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { describe, it, expect, beforeEach, afterEach } from 'vitest';

import { environment } from '../../../environments/environment';

import { ConnectivityService } from './connectivity.service';

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

  it('updates host offline status after consecutive error threshold (QA-01)', () => {
    let isOffline = false;
    service.isHostOffline$.subscribe((val) => (isOffline = val));

    // First error increments counter to 1, offline stays false (gate prevents false positive)
    service.setHostOffline(true);
    expect(service.consecutiveErrorCount).toBe(1);
    expect(isOffline).toBe(false);

    // Second consecutive error reaches threshold of 2, offline becomes true
    service.setHostOffline(true);
    expect(service.consecutiveErrorCount).toBe(2);
    expect(isOffline).toBe(true);

    // Recovery resets consecutive errors to 0 and offline to false
    service.setHostOffline(false);
    expect(service.consecutiveErrorCount).toBe(0);
    expect(isOffline).toBe(false);

    // Direct force bypass sets offline immediately
    service.setHostOffline(true, true);
    expect(isOffline).toBe(true);
  });

  it('dismisses banner manually and prevents re-triggering until recovery', () => {
    service.setHostOffline(true, true);
    let isOffline = false;
    service.isHostOffline$.subscribe((val) => (isOffline = val));
    expect(isOffline).toBe(true);

    service.dismissBanner();
    expect(isOffline).toBe(false);

    // Another offline notification while dismissed should stay hidden
    service.setHostOffline(true, true);
    expect(isOffline).toBe(false);

    // Recovery clears manual dismissal
    service.setHostOffline(false);
    expect(isOffline).toBe(false);

    // Subsequent offline triggers banner again
    service.setHostOffline(true, true);
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
    expect(service.isValidApiUrl('https://other-subdomain.ngrok-free.dev')).toBe(true);
    expect(service.isValidApiUrl('https://dynamic-tunnel.trycloudflare.com')).toBe(true);
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

    // Setting trusted URL succeeds and normalizes path
    service.setCustomApiUrl('https://anybody-cube-surprise.ngrok-free.dev');
    expect(localStorage.getItem('ne_custom_api_url')).toBe('https://anybody-cube-surprise.ngrok-free.dev/api/v1');

    // Cloudflare tunnels supported (SEC-01)
    service.setCustomApiUrl('https://dynamic-tunnel-demo.trycloudflare.com');
    expect(localStorage.getItem('ne_custom_api_url')).toBe('https://dynamic-tunnel-demo.trycloudflare.com/api/v1');

    // Cloudflare Worker reverse proxies supported (Option 2)
    expect(service.isValidApiUrl('https://ne-itinerary-api.demo-subdomain.workers.dev')).toBe(true);
    service.setCustomApiUrl('https://ne-itinerary-api.demo-subdomain.workers.dev');
    expect(localStorage.getItem('ne_custom_api_url')).toBe('https://ne-itinerary-api.demo-subdomain.workers.dev/api/v1');

    // clearCustomApiUrl clears storage
    service.clearCustomApiUrl();
    expect(localStorage.getItem('ne_custom_api_url')).toBeNull();
  });
});
