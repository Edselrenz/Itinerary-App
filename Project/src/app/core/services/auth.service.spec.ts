import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { AuthService } from './auth.service';
import { GuestStorageService } from './guest-storage.service';
import { SecureTokenStorageService } from './secure-token-storage.service';
import type { AuthResponse, User } from '../models/auth.models';
import { environment } from '../../../environments/environment';

describe('AuthService with SecureTokenStorage (SEC-02)', () => {
  let service: AuthService;
  let httpMock: HttpTestingController;
  let guestStorageMock: any;
  let secureTokenStorageMock: any;

  const mockUser: User = {
    id: 'user-auth-1',
    first_name: 'Test',
    last_name: 'Pilot',
    username_normalized: 'test_pilot',
    email_normalized: 'test@example.com',
    is_active: true,
    created_at: '2026-11-04T00:00:00Z',
  };

  const mockAuthResponse: AuthResponse = {
    access_token: 'valid.access.token',
    refresh_token: 'valid.refresh.token',
    token_type: 'bearer',
    user: mockUser,
  };

  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();

    guestStorageMock = {
      setGuestMode: vi.fn().mockResolvedValue(undefined),
    };

    secureTokenStorageMock = {
      init: vi.fn().mockResolvedValue(undefined),
      getAccessTokenSync: vi.fn().mockReturnValue('mock.access.token'),
      getRefreshTokenSync: vi.fn().mockReturnValue('mock.refresh.token'),
      saveTokens: vi.fn().mockResolvedValue(undefined),
      clearTokens: vi.fn().mockResolvedValue(undefined),
    };

    TestBed.configureTestingModule({
      providers: [
        AuthService,
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: GuestStorageService, useValue: guestStorageMock },
        { provide: SecureTokenStorageService, useValue: secureTokenStorageMock },
      ],
    });

    service = TestBed.inject(AuthService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('delegates getAccessToken and getRefreshToken to SecureTokenStorageService', () => {
    expect(service.getAccessToken()).toBe('mock.access.token');
    expect(service.getRefreshToken()).toBe('mock.refresh.token');
    expect(secureTokenStorageMock.getAccessTokenSync).toHaveBeenCalled();
    expect(secureTokenStorageMock.getRefreshTokenSync).toHaveBeenCalled();
  });

  it('persists tokens securely via saveTokens on login', () => {
    service.login({ email: 'test@example.com', password: 'Password123!' }, true).subscribe((res) => {
      expect(res.user.email_normalized).toBe('test@example.com');
    });

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/auth/login`);
    expect(req.request.method).toBe('POST');
    req.flush(mockAuthResponse);

    expect(secureTokenStorageMock.saveTokens).toHaveBeenCalledWith(
      'valid.access.token',
      'valid.refresh.token',
      true
    );
  });

  it('clears tokens and guest mode on logout', async () => {
    await service.logout();

    expect(secureTokenStorageMock.clearTokens).toHaveBeenCalled();
    expect(guestStorageMock.setGuestMode).toHaveBeenCalledWith(false);
  });

  it('clears tokens and enables guest mode on continueAsGuest', async () => {
    await service.continueAsGuest();

    expect(secureTokenStorageMock.clearTokens).toHaveBeenCalled();
    expect(guestStorageMock.setGuestMode).toHaveBeenCalledWith(true);
  });

  it('authenticates demo persona via loginDemo without server network request', () => {
    service.loginDemo(true).subscribe((res) => {
      expect(res.user.id).toBe('usr_pattranite_demo_01');
      expect(res.user.first_name).toBe('Pattranite');
      expect(service.isDemoUser()).toBe(true);
    });

    httpMock.expectNone(`${environment.apiBaseUrl}/auth/login`);
    expect(secureTokenStorageMock.saveTokens).toHaveBeenCalled();
  });
});
