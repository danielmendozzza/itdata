import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { finalize, switchMap } from 'rxjs';
import { AuthService } from '../../core/auth.service';

@Component({
  selector: 'app-login-page',
  imports: [ReactiveFormsModule],
  templateUrl: './login.html',
  styleUrl: './login.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LoginPage {
  private readonly fb = inject(FormBuilder);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  readonly cargando = signal(false);
  readonly error = signal('');
  readonly form = this.fb.nonNullable.group({
    username: ['', Validators.required],
    password: ['', Validators.required],
  });

  ingresar(): void {
    if (this.form.invalid || this.cargando()) return;
    this.cargando.set(true);
    this.error.set('');
    const { username, password } = this.form.getRawValue();
    this.auth
      .login(username, password)
      .pipe(
        switchMap(() => this.auth.cargarUsuario()),
        finalize(() => this.cargando.set(false)),
      )
      .subscribe({
        next: () => void this.router.navigate(['/dashboard']),
        error: () => this.error.set('Usuario o contraseña incorrectos.'),
      });
  }
}
