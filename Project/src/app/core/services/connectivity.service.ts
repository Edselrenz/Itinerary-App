import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import type { Observable } from 'rxjs';
import { BehaviorSubject, catchError, map, of, tap, timeout } from 'rxjs';

import { environment } from '../../../environments/environment';

export interface HealthResponse {

  status: string;

  province_scope: string;

  environment: string;

}

@Injectable({

  providedIn: 'root',

})

export class ConnectivityService {

  private isHostOfflineSubject = new BehaviorSubject<boolean>(false);

  public isHostOffline$: Observable<boolean> = this.isHostOfflineSubject.asObservable();

  public get isHostOfflineSnapshot(): boolean {
    return this.isHostOfflineSubject.value;
  }

  private isCheckingHealthSubject = new BehaviorSubject<boolean>(false);

  public isCheckingHealth$: Observable<boolean> = this.isCheckingHealthSubject.asObservable();

  private isDismissedManually = false;

  private consecutiveErrors = 0;
  public readonly ERROR_THRESHOLD = 2;

  public get consecutiveErrorCount(): number {
    return this.consecutiveErrors;
  }

  private http = inject(HttpClient);

  /**
   * Reports a gateway or connection failure.
   * Only transitions to offline state when consecutive errors reach the threshold (>= 2).
   */
  public reportGatewayError(): void {
    this.consecutiveErrors++;
    if (this.consecutiveErrors >= this.ERROR_THRESHOLD) {
      if (!this.isDismissedManually) {
        this.isHostOfflineSubject.next(true);
      }
    }
  }

  /**
   * Sets the host offline status. If dismissed manually, offline state will not re-display
   * until a new offline event occurs.
   * Consecutive errors are incremented on offline events and reset on recovery.
   * Pass force=true to bypass the consecutive error threshold.
   */
  public setHostOffline(isOffline: boolean, force = false): void {
    if (isOffline) {
      if (force) {
        this.consecutiveErrors = this.ERROR_THRESHOLD;
        if (!this.isDismissedManually) {
          this.isHostOfflineSubject.next(true);
        }
      } else {
        this.reportGatewayError();
      }
    } else {
      this.consecutiveErrors = 0;
      this.isDismissedManually = false;
      this.isHostOfflineSubject.next(false);
    }
  }

  /**
   * Manually dismisses the offline banner for the current session.
   */
  public dismissBanner(): void {
    this.isDismissedManually = true;
    this.isHostOfflineSubject.next(false);
  }

  /**
   * Returns current active API base URL, checking local storage override first.
   */
  public get activeApiBaseUrl(): string {
    if (typeof localStorage !== 'undefined') {
      const customUrl = localStorage.getItem('ne_custom_api_url');
      if (customUrl && this.isValidApiUrl(customUrl)) {
        return customUrl;
      }
    }
    return environment.apiBaseUrl;
  }

  /**
   * Returns current active API base URL.
   */
  public get currentApiUrl(): string {
    return this.activeApiBaseUrl;
  }

  /**

   * Validates whether a provided URL conforms to secure protocols (https or localhost http).

   */

  public isValidApiUrl(url: string): boolean {
    try {
      const parsed = new URL(url.trim());
      const lower = parsed.hostname.toLowerCase();
      const isTrustedHost =
        lower === 'localhost' ||
        lower === '127.0.0.1' ||
        lower === 'anybody-cube-surprise.ngrok-free.dev' ||
        lower.endsWith('.ngrok-free.dev') ||
        lower.endsWith('.ngrok.app') ||
        lower.endsWith('.ngrok.io') ||
        lower.endsWith('.trycloudflare.com') ||
        lower.endsWith('.workers.dev') ||
        lower.endsWith('.onrender.com') ||
        lower.endsWith('.koyeb.app');

      if (!isTrustedHost) {
        return false;
      }
      if (parsed.protocol === 'https:') {
        return true;
      }
      if (
        parsed.protocol === 'http:' &&
        (lower === 'localhost' || lower === '127.0.0.1')
      ) {
        return true;
      }
      return false;
    } catch {
      return false;
    }
  }

  /**
   * Sets or clears a custom API base URL (e.g. Cloudflare tunnel or ngrok).
   * Validates protocol (https:// or localhost http://) to prevent exfiltration (CR-012, SEC-01).
   * Automatically normalizes the path to ensure it ends with /api/v1.
   */
  public setCustomApiUrl(url: string | null): boolean {
    if (url && url.trim()) {
      let trimmed = url.trim().replace(/\/+$/, '');
      if (!this.isValidApiUrl(trimmed)) {
        throw new Error('Invalid API URL: Must use trusted host with https:// or http://localhost.');
      }
      if (!trimmed.endsWith('/api/v1')) {
        trimmed = `${trimmed}/api/v1`;
      }
      localStorage.setItem('ne_custom_api_url', trimmed);
    } else {
      localStorage.removeItem('ne_custom_api_url');
    }
    this.isDismissedManually = false;
    return true;
  }

  /**
   * Clears any custom API URL override and resets to default environment configuration.
   */
  public clearCustomApiUrl(): void {
    if (typeof localStorage !== 'undefined') {
      localStorage.removeItem('ne_custom_api_url');
    }
    this.isDismissedManually = false;
  }
  /**
   * Actively probes the backend health endpoint to verify connectivity.
   */
  public checkHostHealth(): Observable<boolean> {

    this.isCheckingHealthSubject.next(true);

    const healthUrl = `${this.activeApiBaseUrl}/health`;

    return this.http.get<HealthResponse>(healthUrl).pipe(
      timeout(5000),
      tap(() => {

        this.isCheckingHealthSubject.next(false);

        this.setHostOffline(false);

      }),

      map(() => true),

      catchError(() => {

        this.isCheckingHealthSubject.next(false);

        this.isDismissedManually = false;

        this.consecutiveErrors = this.ERROR_THRESHOLD;

        this.isHostOfflineSubject.next(true);

        return of(false);

      })

    );

  }

}

