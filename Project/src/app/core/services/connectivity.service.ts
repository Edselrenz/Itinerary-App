import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, catchError, map, of, tap } from 'rxjs';
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

  private isCheckingHealthSubject = new BehaviorSubject<boolean>(false);
  public isCheckingHealth$: Observable<boolean> = this.isCheckingHealthSubject.asObservable();

  private isDismissedManually = false;

  constructor(private http: HttpClient) {}

  /**
   * Sets the host offline status. If dismissed manually, offline state will not re-display
   * until a new offline event occurs.
   */
  public setHostOffline(isOffline: boolean): void {
    if (isOffline) {
      if (!this.isDismissedManually) {
        this.isHostOfflineSubject.next(true);
      }
    } else {
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
   * Actively probes the backend health endpoint to verify connectivity.
   */
  public checkHostHealth(): Observable<boolean> {
    this.isCheckingHealthSubject.next(true);
    const healthUrl = `${environment.apiBaseUrl}/health`;

    return this.http.get<HealthResponse>(healthUrl).pipe(
      tap(() => {
        this.isCheckingHealthSubject.next(false);
        this.setHostOffline(false);
      }),
      map(() => true),
      catchError(() => {
        this.isCheckingHealthSubject.next(false);
        this.isDismissedManually = false;
        this.isHostOfflineSubject.next(true);
        return of(false);
      })
    );
  }
}
