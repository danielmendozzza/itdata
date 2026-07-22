import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';
import { ApiService } from '../../core/api.service';
import { ActivoCatalogo, OpcionCatalogo } from '../../core/models';

@Component({
  selector: 'app-ticket-create-page',
  imports: [ReactiveFormsModule, RouterLink],
  templateUrl: './ticket-create.html',
  styleUrl: './ticket-create.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TicketCreatePage implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly api = inject(ApiService);
  private readonly router = inject(Router);
  readonly sucursales = signal<OpcionCatalogo[]>([]);
  readonly categorias = signal<OpcionCatalogo[]>([]);
  readonly subcategorias = signal<OpcionCatalogo[]>([]);
  readonly activos = signal<ActivoCatalogo[]>([]);
  readonly cargando = signal(true);
  readonly guardando = signal(false);
  readonly error = signal('');
  readonly form = this.fb.group({
    titulo: ['', [Validators.required, Validators.maxLength(150)]],
    descripcion: ['', Validators.required],
    sucursal: ['', Validators.required],
    activo: [''],
    categoria: ['', Validators.required],
    subcategoria: [''],
    origen: ['TECNICO', Validators.required],
  });

  ngOnInit(): void {
    forkJoin({ sucursales: this.api.sucursales(), categorias: this.api.categorias() }).subscribe({
      next: ({ sucursales, categorias }) => {
        this.sucursales.set(sucursales.results);
        this.categorias.set(categorias);
        if (sucursales.results.length === 1) {
          this.form.controls.sucursal.setValue(sucursales.results[0].id);
          this.cargarActivos();
        }
      },
      complete: () => this.cargando.set(false),
      error: () => { this.error.set('No pudimos cargar los catálogos.'); this.cargando.set(false); },
    });
  }

  cargarSubcategorias(): void {
    const categoria = this.form.controls.categoria.value;
    this.form.controls.subcategoria.setValue('');
    if (!categoria) { this.subcategorias.set([]); return; }
    this.api.subcategorias(categoria).subscribe((items) => this.subcategorias.set(items));
  }

  cargarActivos(): void {
    const sucursal = this.form.controls.sucursal.value;
    this.form.controls.activo.setValue('');
    if (!sucursal) { this.activos.set([]); return; }
    this.api.activosPorSucursal(sucursal).subscribe((items) => this.activos.set(items));
  }

  guardar(): void {
    if (this.form.invalid || this.guardando()) return;
    this.guardando.set(true);
    this.error.set('');
    const raw = this.form.getRawValue();
    this.api.crearTicket({ ...raw, subcategoria: raw.subcategoria || null, activo: raw.activo || null }).subscribe({
      next: (ticket) => void this.router.navigate(['/tickets', ticket.id]),
      error: (e) => { this.error.set(this.mensajeError(e?.error)); this.guardando.set(false); },
    });
  }

  private mensajeError(error: unknown): string {
    if (!error || typeof error !== 'object') return 'No se pudo crear el ticket. Intentá nuevamente.';
    const mensajes = Object.entries(error as Record<string, unknown>).flatMap(([campo, detalle]) => {
      const textos = Array.isArray(detalle) ? detalle : [detalle];
      return textos.filter((item) => typeof item === 'string').map((item) => `${campo}: ${item}`);
    });
    return mensajes.join(' · ') || 'No se pudo crear el ticket. Intentá nuevamente.';
  }
}
