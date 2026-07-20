import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, tap } from 'rxjs';
import { environment } from '../../environments/environment';
import { UsuarioActual } from './models';

interface TokenResponse {
  access: string;
  refresh: string;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);
  private readonly usuarioSignal = signal<UsuarioActual | null>(null);

  readonly usuario = this.usuarioSignal.asReadonly();
  readonly autenticado = computed(() => Boolean(this.accessToken));

  get accessToken(): string | null {
    return localStorage.getItem('itdata_access');
  }

  get refreshTokenValue(): string | null {
    return localStorage.getItem('itdata_refresh');
  }

  login(username: string, password: string): Observable<TokenResponse> {
    return this.http
      .post<TokenResponse>(`${environment.apiUrl}/auth/login/`, { username, password })
      .pipe(tap((tokens) => this.guardarTokens(tokens)));
  }

  cargarUsuario(): Observable<UsuarioActual> {
    return this.http
      .get<UsuarioActual>(`${environment.apiUrl}/auth/me/`)
      .pipe(tap((usuario) => this.usuarioSignal.set(usuario)));
  }

  refresh(): Observable<{ access: string }> {
    return this.http
      .post<{ access: string }>(`${environment.apiUrl}/auth/refresh/`, {
        refresh: this.refreshTokenValue,
      })
      .pipe(tap(({ access }) => localStorage.setItem('itdata_access', access)));
  }

  cerrarSesion(): void {
    localStorage.removeItem('itdata_access');
    localStorage.removeItem('itdata_refresh');
    this.usuarioSignal.set(null);
    void this.router.navigate(['/login']);
  }

  esRolGlobal(): boolean {
    return ['ADMINISTRADOR', 'SUPERVISOR', 'CONSULTOR'].includes(
      this.usuarioSignal()?.rol ?? '',
    );
  }

  puedeConfigurar(): boolean {
    return ['ADMINISTRADOR', 'SUPERVISOR'].includes(this.usuarioSignal()?.rol ?? '');
  }

  private guardarTokens(tokens: TokenResponse): void {
    localStorage.setItem('itdata_access', tokens.access);
    localStorage.setItem('itdata_refresh', tokens.refresh);
  }
}
