import { TestBed } from '@angular/core/testing';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { SecureStoragePlugin } from 'capacitor-secure-storage-plugin';
import { SecureTokenStorageService } from './secure-token-storage.service';

vi.mock('capacitor-secure-storage-plugin', () => ({
  SecureStoragePlugin: {
    get: vi.fn().mockResolvedValue({ value: null }),
    set: vi.fn().mockResolvedValue({ value: true }),
    remove: vi.fn().mockResolvedValue({ value: true }),
    clear: vi.fn().mockResolvedValue({ value: true }),
  },
}));

describe('SecureTokenStorageService (SEC-02)', () => {
  let service: SecureTokenStorageService;

  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
    vi.clearAllMocks();

    TestBed.configureTestingModule({
      providers: [SecureTokenStorageService],
    });
    service = TestBed.inject(SecureTokenStorageService);
  });

  it('initializes from web storage when present', () => {
    localStorage.setItem(SecureTokenStorageService.ACCESS_TOKEN_KEY, 'stored_access');
    localStorage.setItem(SecureTokenStorageService.REFRESH_TOKEN_KEY, 'stored_refresh');

    const freshService = new SecureTokenStorageService();
    expect(freshService.getAccessTokenSync()).toBe('stored_access');
    expect(freshService.getRefreshTokenSync()).toBe('stored_refresh');
  });

  it('saves tokens to localStorage when rememberMe is true', async () => {
    await service.saveTokens('access_123', 'refresh_456', true);

    expect(service.getAccessTokenSync()).toBe('access_123');
    expect(service.getRefreshTokenSync()).toBe('refresh_456');
    expect(localStorage.getItem(SecureTokenStorageService.ACCESS_TOKEN_KEY)).toBe('access_123');
    expect(sessionStorage.getItem(SecureTokenStorageService.ACCESS_TOKEN_KEY)).toBeNull();
  });

  it('saves tokens to sessionStorage when rememberMe is false', async () => {
    await service.saveTokens('session_access', 'session_refresh', false);

    expect(service.getAccessTokenSync()).toBe('session_access');
    expect(service.getRefreshTokenSync()).toBe('session_refresh');
    expect(sessionStorage.getItem(SecureTokenStorageService.ACCESS_TOKEN_KEY)).toBe('session_access');
    expect(localStorage.getItem(SecureTokenStorageService.ACCESS_TOKEN_KEY)).toBeNull();
  });

  it('clears tokens from cache and both web storage scopes', async () => {
    await service.saveTokens('token_to_clear', 'refresh_to_clear', true);
    await service.clearTokens();

    expect(service.getAccessTokenSync()).toBeNull();
    expect(service.getRefreshTokenSync()).toBeNull();
    expect(localStorage.getItem(SecureTokenStorageService.ACCESS_TOKEN_KEY)).toBeNull();
    expect(sessionStorage.getItem(SecureTokenStorageService.ACCESS_TOKEN_KEY)).toBeNull();
  });

  it('interacts with hardware Keystore via SecureStoragePlugin when running on native platform', async () => {
    vi.spyOn(service, 'isNativeSecureStorage').mockReturnValue(true);

    await service.saveTokens('native_access', 'native_refresh', true);
    expect(SecureStoragePlugin.set).toHaveBeenCalledWith(
      expect.objectContaining({
        key: SecureTokenStorageService.ACCESS_TOKEN_KEY,
        value: 'native_access',
      })
    );

    await service.clearTokens();
    expect(SecureStoragePlugin.remove).toHaveBeenCalledWith(
      expect.objectContaining({
        key: SecureTokenStorageService.ACCESS_TOKEN_KEY,
      })
    );
  });
});
