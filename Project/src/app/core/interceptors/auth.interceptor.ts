import { HttpResponse, type HttpErrorResponse, type HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { BehaviorSubject, catchError, filter, switchMap, take, tap, throwError } from 'rxjs';

import { environment } from '../../../environments/environment';
import { AuthService } from '../services/auth.service';
import { ConnectivityService } from '../services/connectivity.service';

let isRefreshing = false;
const refreshTokenSubject = new BehaviorSubject<string | null>(null);

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const connectivityService = inject(ConnectivityService);
  const token = authService.getAccessToken();

  let authReq = req;
  const activeBaseUrl = connectivityService.activeApiBaseUrl;
  const isApiRequest =
    req.url.startsWith(activeBaseUrl) || req.url.startsWith(environment.apiBaseUrl);

  // CR-012: Attach Bearer token strictly to requests matching apiBaseUrl
  // ngrok: Set 'ngrok-skip-browser-warning': 'true' to bypass interstitial page on free tunnels
  if (isApiRequest) {
    const headersConfig: Record<string, string> = {
      'ngrok-skip-browser-warning': 'true',
    };
    if (token && !req.headers.has('Authorization')) {
      headersConfig['Authorization'] = `Bearer ${token}`;
    }
    authReq = req.clone({
      setHeaders: headersConfig,
    });
  }

  return next(authReq).pipe(
    tap((event) => {
      if (event instanceof HttpResponse && isApiRequest) {
        connectivityService.setHostOffline(false);
      }
    }),
    catchError((error: HttpErrorResponse) => {
      // Ignore client-aborted requests (e.g. cancelled during debounced search/pan or navigation)
      const isAborted =
        (error as any)?.name === 'AbortError' ||
        (error.error instanceof ProgressEvent && (error.error as any).type === 'abort') ||
        (typeof error.message === 'string' && error.message.toLowerCase().includes('abort'));

      // Step 9 / Build Guide: Graceful Laptop-Offline State
      // Only API requests that encounter genuine gateway failures or connection refusals trigger offline state
      const isGatewayOrOffline =
        isApiRequest &&
        !isAborted &&
        (error.status === 0 ||
          error.status === 502 ||
          error.status === 503 ||
          error.status === 504 ||
          (error.status === 404 && (req.url.endsWith('/health') || req.url.includes('/api/v1/health'))));

      if (isGatewayOrOffline) {
        console.warn(
          'Pilot backend is currently unreachable (host laptop or tunnel may be offline). Local guest data remains accessible.'
        );
        connectivityService.setHostOffline(true);
        // Asynchronously check host health on gateway error to reconcile state without blocking user (QA-01)
        if (typeof connectivityService.checkHostHealth === 'function') {
          connectivityService.checkHostHealth().subscribe({ error: () => {} });
        }
        return throwError(() => error);
      }

      // CR-006: 401 Unauthorized handling with token refresh queue
      const isAuthEndpoint =
        req.url.includes('/auth/login') ||
        req.url.includes('/auth/register') ||
        req.url.includes('/auth/refresh');

      if (error.status === 401 && isApiRequest && !isAuthEndpoint) {
        const refreshToken = authService.getRefreshToken();
        if (!refreshToken) {
          authService.logout();
          return throwError(() => error);
        }

        if (!isRefreshing) {
          isRefreshing = true;
          refreshTokenSubject.next(null);

          return authService.refreshSession().pipe(
            switchMap((tokenResponse) => {
              isRefreshing = false;
              refreshTokenSubject.next(tokenResponse.access_token);
              const retryHeaders: Record<string, string> = {
                'ngrok-skip-browser-warning': 'true',
                Authorization: `Bearer ${tokenResponse.access_token}`,
              };
              return next(
                req.clone({
                  setHeaders: retryHeaders,
                })
              );
            }),
            catchError((refreshErr) => {
              isRefreshing = false;
              authService.logout();
              return throwError(() => refreshErr);
            })
          );
        } else {
          // Concurrent request: wait for active refresh to conclude
          return refreshTokenSubject.pipe(
            filter((newToken) => newToken !== null),
            take(1),
            switchMap((newToken) => {
              const retryHeaders: Record<string, string> = {
                'ngrok-skip-browser-warning': 'true',
                Authorization: `Bearer ${newToken}`,
              };
              return next(
                req.clone({
                  setHeaders: retryHeaders,
                })
              );
            })
          );
        }
      }

      return throwError(() => error);
    })
  );
};
