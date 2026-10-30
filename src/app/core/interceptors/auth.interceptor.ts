import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, throwError } from 'rxjs';
import { AuthService } from '../services/auth.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const token = authService.getAccessToken();

  let authReq = req;
  if (token && !req.headers.has('Authorization')) {
    authReq = req.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`,
      },
    });
  }

  return next(authReq).pipe(
    catchError((error: HttpErrorResponse) => {
      // Step 9 / Build Guide: Graceful Laptop-Offline State
      if (error.status === 0 || error.status === 502 || error.status === 504) {
        console.warn(
          'Pilot backend is currently unreachable (host laptop or tunnel may be offline). Local guest data remains accessible.'
        );
      }
      return throwError(() => error);
    })
  );
};

