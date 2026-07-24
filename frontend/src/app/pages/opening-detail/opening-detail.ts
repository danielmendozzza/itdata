import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { finalize } from 'rxjs';
import { ApiService } from '../../core/api.service';
import { TicketDetalle } from '../../core/models';

@Component({
  selector: 'app-opening-detail-page',
  imports: [DatePipe, FormsModule, RouterLink],
  templateUrl: './opening-detail.html',
  styleUrl: './opening-detail.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class OpeningDetailPage implements OnInit {
  private readonly api = inject(ApiService);
  private readonly route = inject(ActivatedRoute);
  readonly apertura = signal<TicketDetalle | null>(null);
  readonly cargando = signal(true);
  readonly guardando = signal(false);
  readonly error = signal('');
  estado = 'EN_PROCESO';
  comentarioEstado = '';
  private id = '';
  readonly estados = [
    { value: 'EN_PROCESO', label: 'En proceso' },
    { value: 'ESPERANDO_PROVEEDOR', label: 'Esperando proveedor' },
    { value: 'EN_PRUEBAS', label: 'En pruebas' },
    { value: 'REALIZADO', label: 'Realizado' },
  ];

  ngOnInit(): void {
    this.id = this.route.snapshot.paramMap.get('id') ?? '';
    this.cargar();
  }

  cargar(): void {
    this.api.apertura(this.id).subscribe({
      next: (item) => { this.apertura.set(item); this.estado = item.estado; },
      complete: () => this.cargando.set(false),
      error: () => this.cargando.set(false),
    });
  }

  cambiarEstado(): void {
    const actual = this.apertura();
    if (!actual || actual.estado === this.estado || this.guardando()) return;
    this.guardando.set(true);
    this.error.set('');
    this.api.cambiarEstadoApertura(this.id, this.estado, this.comentarioEstado.trim())
      .pipe(finalize(() => this.guardando.set(false)))
      .subscribe({
        next: (item) => { this.apertura.set(item); this.comentarioEstado = ''; this.cargar(); },
        error: (e) => this.error.set(e?.error?.detail ?? 'No se pudo cambiar el estado.'),
      });
  }

  texto(valor: string): string { return valor.replaceAll('_', ' ').toLowerCase(); }
}
