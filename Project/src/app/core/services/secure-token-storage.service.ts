import { Injectable } from '@angular/core';
import { Capacitor } from '@capacitor/core';
import { SecureStoragePlugin } from 'capacitor-secure-storage-plugin';

export interface StoredTokens {
  accessToken: string | null;
  refreshToken: string | null;
}

@Injectable({
  providedIn: 'root',
})
export class SecureTokenStorageService {
  public static readonly ACCESS_TOKEN_KEY = 'ne_access_token';
  public static readonly REFRESH_TOKEN_KEY = 'ne_refresh_token';
  public static readonly REMEMBER_ME_KEY = 'ne_auth_remember_me';

  private cachedAccessToken: string | null = null;
  private cachedRefreshToken: string | null = null;
  private isInitialized = false;

  constructor() {
    this.initSyncFallback();
  }

  /**
   * Immediately seeds memory cache from web storage so synchronous
   * interceptors work even before async native init completes.
   */
  private initSyncFallback(): void {
    const localAccess = localStorage.getItem(SecureTokenStorageService.ACCESS_TOKEN_KEY);
    const sessionAccess = sessionStorage.getItem(SecureTokenStorageService.ACCESS_TOKEN_KEY);
    this.cachedAccessToken = localAccess || sessionAccess || null;

    const localRefresh = localStorage.getItem(SecureTokenStorageService.REFRESH_TOKEN_KEY);
    const sessionRefresh = sessionStorage.getItem(SecureTokenStorageService.REFRESH_TOKEN_KEY);
    this.cachedRefreshToken = localRefresh || sessionRefresh || null;
  }

  /**
   * Initializes token cache from native Keystore if available.
   */
  public async init(): Promise<void> {
    if (this.isInitialized) return;

    if (this.isNativeSecureStorage()) {
      try {
        const accessRes = await SecureStoragePlugin.get({
          key: SecureTokenStorageService.ACCESS_TOKEN_KEY,
        });
        if (accessRes?.value) {
          this.cachedAccessToken = accessRes.value;
        }

        const refreshRes = await SecureStoragePlugin.get({
          key: SecureTokenStorageService.REFRESH_TOKEN_KEY,
        });
        if (refreshRes?.value) {
          this.cachedRefreshToken = refreshRes.value;
        }
      } catch {
        // Fallback already initialized from web storage
      }
    }
    this.isInitialized = true;
  }

  public isNativeSecureStorage(): boolean {
    return Capacitor.isNativePlatform();
  }

  /**
   * Synchronous getter for HTTP interceptors and guards.
   */
  public getAccessTokenSync(): string | null {
    if (this.cachedAccessToken) {
      return this.cachedAccessToken;
    }
    return (
      localStorage.getItem(SecureTokenStorageService.ACCESS_TOKEN_KEY) ||
      sessionStorage.getItem(SecureTokenStorageService.ACCESS_TOKEN_KEY)
    );
  }

  /**
   * Synchronous getter for refresh token.
   */
  public getRefreshTokenSync(): string | null {
    if (this.cachedRefreshToken) {
      return this.cachedRefreshToken;
    }
    return (
      localStorage.getItem(SecureTokenStorageService.REFRESH_TOKEN_KEY) ||
      sessionStorage.getItem(SecureTokenStorageService.REFRESH_TOKEN_KEY)
    );
  }

  /**
   * Persists tokens securely (Keystore on native, scoped storage on web).
   */
  public async saveTokens(
    accessToken: string,
    refreshToken: string,
    rememberMe = true
  ): Promise<void> {
    this.cachedAccessToken = accessToken;
    this.cachedRefreshToken = refreshToken;

    // Save to web storage for browser or web fallback
    const targetStorage = rememberMe ? localStorage : sessionStorage;
    const alternateStorage = rememberMe ? sessionStorage : localStorage;

    targetStorage.setItem(SecureTokenStorageService.ACCESS_TOKEN_KEY, accessToken);
    targetStorage.setItem(SecureTokenStorageService.REFRESH_TOKEN_KEY, refreshToken);
    targetStorage.setItem(SecureTokenStorageService.REMEMBER_ME_KEY, String(rememberMe));

    alternateStorage.removeItem(SecureTokenStorageService.ACCESS_TOKEN_KEY);
    alternateStorage.removeItem(SecureTokenStorageService.REFRESH_TOKEN_KEY);
    alternateStorage.removeItem(SecureTokenStorageService.REMEMBER_ME_KEY);

    // Save to hardware Keystore if on native device (SEC-02)
    if (this.isNativeSecureStorage()) {
      try {
        await SecureStoragePlugin.set({
          key: SecureTokenStorageService.ACCESS_TOKEN_KEY,
          value: accessToken,
        });
        await SecureStoragePlugin.set({
          key: SecureTokenStorageService.REFRESH_TOKEN_KEY,
          value: refreshToken,
        });
      } catch {
        // Handled via web storage fallback
      }
    }
  }

  /**
   * Clears tokens across all storage tiers.
   */
  public async clearTokens(): Promise<void> {
    this.cachedAccessToken = null;
    this.cachedRefreshToken = null;

    localStorage.removeItem(SecureTokenStorageService.ACCESS_TOKEN_KEY);
    localStorage.removeItem(SecureTokenStorageService.REFRESH_TOKEN_KEY);
    localStorage.removeItem(SecureTokenStorageService.REMEMBER_ME_KEY);

    sessionStorage.removeItem(SecureTokenStorageService.ACCESS_TOKEN_KEY);
    sessionStorage.removeItem(SecureTokenStorageService.REFRESH_TOKEN_KEY);
    sessionStorage.removeItem(SecureTokenStorageService.REMEMBER_ME_KEY);

    if (this.isNativeSecureStorage()) {
      try {
        await SecureStoragePlugin.remove({
          key: SecureTokenStorageService.ACCESS_TOKEN_KEY,
        });
        await SecureStoragePlugin.remove({
          key: SecureTokenStorageService.REFRESH_TOKEN_KEY,
        });
      } catch {
        // Safe ignore
      }
    }
  }
}
