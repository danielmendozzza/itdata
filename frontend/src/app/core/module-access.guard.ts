import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { catchError, map, of } from 'rxjs';
import { AuthService } from './auth.service';

export const internalModulesGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const decide = () =>
    auth.usuario()?.rol === 'SUCURSAL'
      ? router.createUrlTree(['/tickets'])
      : true;

  return auth.usuario()
    ? decide()
    : auth.cargarUsuario().pipe(
        map(() => decide()),
        catchError(() => of(router.createUrlTree(['/login']))),
      );
};

export const reportsGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const decide = () =>
    auth.puedeVerReportes() ? true : router.createUrlTree(['/dashboard']);

  return auth.usuario()
    ? decide()
    : auth.cargarUsuario().pipe(
        map(() => decide()),
        catchError(() => of(router.createUrlTree(['/login']))),
      );
};

export const aperturasGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const decide = () =>
    auth.puedeGestionarAperturas() ? true : router.createUrlTree(['/dashboard']);

  return auth.usuario()
    ? decide()
    : auth.cargarUsuario().pipe(
        map(() => decide()),
        catchError(() => of(router.createUrlTree(['/login']))),
      );
};
