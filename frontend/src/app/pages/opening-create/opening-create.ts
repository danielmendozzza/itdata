import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { finalize } from 'rxjs';
import { ApiService } from '../../core/api.service';

@Component({
  selector: 'app-opening-create-page',
  imports: [ReactiveFormsModule, RouterLink],
  templateUrl: './opening-create.html',
  styleUrl: './opening-create.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class OpeningCreatePage {
  private readonly fb = inject(FormBuilder);
  private readonly api = inject(ApiService);
  private readonly router = inject(Router);
  readonly guardando = signal(false);
  readonly error = signal('');
  readonly form = this.fb.group({
    titulo: ['', [Validators.required, Validators.maxLength(150)]],
  });

  guardar(): void {
    if (this.form.invalid || this.guardando()) return;
    this.guardando.set(true);
    this.error.set('');
    this.api.crearApertura(this.form.controls.titulo.value!.trim())
      .pipe(finalize(() => this.guardando.set(false)))
      .subscribe({
        next: (apertura) => void this.router.navigate(['/aperturas', apertura.id]),
        error: (e) => this.error.set(e?.error?.titulo?.[0] ?? 'No se pudo crear la apertura.'),
      });
  }
}
