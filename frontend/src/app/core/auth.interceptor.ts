import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, switchMap, throwError } from 'rxjs';
import { AuthService } from './auth.service';

export const authInterceptor: HttpInterceptorFn = (request, next) => {
  const auth = inject(AuthService);
  const token = auth.accessToken;
  const autenticada = token
    ? request.clone({ setHeaders: { Authorization: `Bearer ${token}` } })
    : request;

  return next(autenticada).pipe(
    catchError((error: HttpErrorResponse) => {
      const esEndpointAuth = request.url.includes('/auth/login/') || request.url.includes('/auth/refresh/');
      if (error.status !== 401 || esEndpointAuth || !auth.refreshTokenValue) {
        return throwError(() => error);
      }
      return auth.refresh().pipe(
        switchMap(({ access }) =>
          next(request.clone({ setHeaders: { Authorization: `Bearer ${access}` } })),
        ),
        catchError((refreshError) => {
          auth.cerrarSesion();
          return throwError(() => refreshError);
        }),
      );
    }),
  );
};
