import { HttpErrorResponse, HttpInterceptorFn, HttpResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { BehaviorSubject, catchError, filter, switchMap, take, tap, throwError } from 'rxjs';
import { AuthService } from '../services/auth.service';
import { ConnectivityService } from '../services/connectivity.service';
import { environment } from '../../../environments/environment';

let isRefreshing = false;
const refreshTokenSubject = new BehaviorSubject<string | null>(null);

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const connectivityService = inject(ConnectivityService);
  const token = authService.getAccessToken();

  let authReq = req;
  const isApiRequest = req.url.startsWith(environment.apiBaseUrl);

  // CR-012: Attach Bearer token strictly to requests matching apiBaseUrl
  if (token && isApiRequest && !req.headers.has('Authorization')) {
    authReq = req.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`,
      },
    });
  }

  return next(authReq).pipe(
    tap((event) => {
      if (event instanceof HttpResponse) {
        connectivityService.setHostOffline(false);
      }
    }),
    catchError((error: HttpErrorResponse) => {
      // Step 9 / Build Guide: Graceful Laptop-Offline State
      if (error.status === 0 || error.status === 502 || error.status === 504) {
        console.warn(
          'Pilot backend is currently unreachable (host laptop or tunnel may be offline). Local guest data remains accessible.'
        );
        connectivityService.setHostOffline(true);
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
              return next(
                req.clone({
                  setHeaders: {
                    Authorization: `Bearer ${tokenResponse.access_token}`,
                  },
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
              return next(
                req.clone({
                  setHeaders: {
                    Authorization: `Bearer ${newToken}`,
                  },
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
