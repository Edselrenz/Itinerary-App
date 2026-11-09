import type { HttpErrorResponse} from '@angular/common/http';
import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';

import { environment } from '../../../environments/environment';
import { AuthService } from '../services/auth.service';
import { ConnectivityService } from '../services/connectivity.service';

import { authInterceptor } from './auth.interceptor';

describe('authInterceptor (GAP-04)', () => {
  let http: HttpClient;
  let httpMock: HttpTestingController;
  let authServiceMock: {
    getAccessToken: ReturnType<typeof vi.fn>;
    getRefreshToken: ReturnType<typeof vi.fn>;
    refreshSession: ReturnType<typeof vi.fn>;
    logout: ReturnType<typeof vi.fn>;
    isAuthenticated: ReturnType<typeof vi.fn>;
  };
  let connectivityServiceMock: {
    setHostOffline: ReturnType<typeof vi.fn>;
    checkHostHealth: ReturnType<typeof vi.fn>;
    activeApiBaseUrl: string;
  };

  beforeEach(() => {
    authServiceMock = {
      getAccessToken: vi.fn().mockReturnValue('mock-jwt-token'),
      getRefreshToken: vi.fn().mockReturnValue('mock-refresh-token'),
      refreshSession: vi.fn(),
      logout: vi.fn(),
      isAuthenticated: vi.fn().mockReturnValue(true),
    };

    connectivityServiceMock = {
      setHostOffline: vi.fn(),
      checkHostHealth: vi.fn().mockReturnValue(of(true)),
      activeApiBaseUrl: environment.apiBaseUrl,
    };

    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
        { provide: AuthService, useValue: authServiceMock },
        { provide: ConnectivityService, useValue: connectivityServiceMock },
      ],
    });

    http = TestBed.inject(HttpClient);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('attaches Bearer token and headers strictly to API requests', () => {
    http.get(`${environment.apiBaseUrl}/places`).subscribe();

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/places`);
    expect(req.request.headers.get('Authorization')).toBe('Bearer mock-jwt-token');
    expect(req.request.headers.get('ngrok-skip-browser-warning')).toBe('true');
    req.flush({ items: [] });

    expect(connectivityServiceMock.setHostOffline).toHaveBeenCalledWith(false);
  });

  it('does not attach Bearer token to external non-API requests', () => {
    http.get('https://tile.openstreetmap.org/10/1/1.png').subscribe();

    const req = httpMock.expectOne('https://tile.openstreetmap.org/10/1/1.png');
    expect(req.request.headers.has('Authorization')).toBe(false);
    req.flush({});
  });

  it('sets host offline on genuine API gateway or offline errors (status 0, 502, 503, 504)', () => {
    http.get(`${environment.apiBaseUrl}/places`).subscribe({
      error: (err: HttpErrorResponse) => {
        expect(err.status).toBe(502);
      },
    });

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/places`);
    req.flush('Bad Gateway', { status: 502, statusText: 'Bad Gateway' });

    expect(connectivityServiceMock.setHostOffline).toHaveBeenCalledWith(true);
  });

  it('does NOT set host offline for non-API request failures (GAP-04)', () => {
    http.get('https://tile.openstreetmap.org/10/1/1.png').subscribe({
      error: () => {},
    });

    const req = httpMock.expectOne('https://tile.openstreetmap.org/10/1/1.png');
    req.flush('Not Found', { status: 404, statusText: 'Not Found' });

    expect(connectivityServiceMock.setHostOffline).not.toHaveBeenCalledWith(true);
  });

  it('does NOT set host offline for client-aborted requests (GAP-04)', () => {
    http.get(`${environment.apiBaseUrl}/places?q=cabanatuan`).subscribe({
      error: () => {},
    });

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/places?q=cabanatuan`);
    const abortProgress = new ProgressEvent('abort');
    req.error(abortProgress);

    expect(connectivityServiceMock.setHostOffline).not.toHaveBeenCalledWith(true);
  });
});
