import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { finalize, Observable } from 'rxjs';
import { ApiService } from '../../core/api.service';
import { AuthService } from '../../core/auth.service';
import { TicketDetalle } from '../../core/models';

@Component({ selector: 'app-ticket-detail-page', imports: [DatePipe, FormsModule, RouterLink], templateUrl: './ticket-detail.html', styleUrl: './ticket-detail.scss', changeDetection: ChangeDetectionStrategy.OnPush })
export class TicketDetailPage implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly api = inject(ApiService);
  readonly auth = inject(AuthService);
  readonly ticket = signal<TicketDetalle | null>(null);
  readonly tecnicos = signal<Array<{ id: string; username: string; nombre_completo: string }>>([]);
  readonly cargando = signal(true);
  readonly guardando = signal(false);
  readonly errorAccion = signal('');
  readonly mensajeConocimiento = signal('');
  gestionAccion = 'NOTA'; gestionTexto = ''; tecnicoSeleccionado = '';
  estadoSeleccionado = 'EN_PROCESO';
  private id = '';
  readonly estadosOperativos = [
    { value: 'EN_PROCESO', label: 'En proceso' },
    { value: 'PENDIENTE', label: 'Pendiente' },
    { value: 'ESPERANDO_USUARIO', label: 'Esperando usuario' },
    { value: 'ESPERANDO_PROVEEDOR', label: 'Esperando proveedor' },
    { value: 'ESPERANDO_OTRA_AREA', label: 'Esperando otra área' },
    { value: 'EN_PRUEBAS', label: 'En pruebas' },
  ];

  ngOnInit(): void { this.id = this.route.snapshot.paramMap.get('id') ?? ''; this.cargar(); if (this.auth.usuario()) this.cargarTecnicos(); else this.auth.cargarUsuario().subscribe({ next: () => this.cargarTecnicos() }); }
  private cargarTecnicos(): void { if (this.puedeAdministrar()) this.api.tecnicos().subscribe((items) => this.tecnicos.set(items)); }
  cargar(): void { this.api.ticket(this.id).subscribe({ next: (t) => { this.ticket.set(t); this.tecnicoSeleccionado = t.tecnico_asignado ?? ''; if (this.estadosOperativos.some((e) => e.value === t.estado)) this.estadoSeleccionado = t.estado; }, complete: () => this.cargando.set(false), error: () => this.cargando.set(false) }); }
  guardarGestion(): void {
    const texto = this.gestionTexto.trim();
    if (this.gestionAccion === 'CAMBIO_ESTADO') {
      this.ejecutar(this.api.cambiarEstadoTicket(this.id, this.estadoSeleccionado, texto), () => this.gestionTexto = '');
    } else if (this.gestionAccion === 'RESOLVER') {
      if (texto) this.ejecutar(this.api.resolverTicket(this.id, texto), () => this.gestionTexto = '');
    } else if (texto) {
      this.guardando.set(true);
      this.api.agregarComentario(this.id, this.gestionAccion, texto).pipe(finalize(() => this.guardando.set(false))).subscribe({ next: () => { this.gestionTexto = ''; this.cargar(); }, error: (e) => this.errorAccion.set(e?.error?.detail ?? 'No se pudo guardar la gestión.') });
    }
  }
  asignar(): void { if (this.tecnicoSeleccionado) this.ejecutar(this.api.asignarTicket(this.id, this.tecnicoSeleccionado)); }
  tomar(): void { this.ejecutar(this.api.tomarTicket(this.id)); }
  crearArticulo(): void { if (this.guardando()) return; this.guardando.set(true); this.errorAccion.set(''); this.api.crearArticuloDesdeTicket(this.id).pipe(finalize(() => this.guardando.set(false))).subscribe({ next: () => this.mensajeConocimiento.set('Borrador de conocimiento actualizado.'), error: (e) => this.errorAccion.set(e?.error?.detail ?? 'No se pudo actualizar el borrador de conocimiento.') }); }
  puedeAdministrar(): boolean { return ['ADMINISTRADOR', 'SUPERVISOR'].includes(this.auth.usuario()?.rol ?? ''); }
  puedeTomar(t: TicketDetalle): boolean { return this.auth.usuario()?.rol === 'TECNICO' && (!t.tecnico_asignado || t.tecnico_asignado === this.auth.usuario()?.id) && !['RESUELTO', 'CANCELADO'].includes(t.estado); }
  puedeOperar(t: TicketDetalle): boolean { return this.puedeAdministrar() || (this.auth.usuario()?.rol === 'TECNICO' && t.tecnico_asignado === this.auth.usuario()?.id); }
  puedeDocumentar(t: TicketDetalle): boolean { return this.puedeAdministrar() || (this.auth.usuario()?.rol === 'TECNICO' && t.tecnico_asignado === this.auth.usuario()?.id); }
  gestionRequiereTexto(): boolean { return this.gestionAccion !== 'CAMBIO_ESTADO'; }
  private ejecutar(peticion: Observable<TicketDetalle>, despues?: () => void): void { if (this.guardando()) return; this.guardando.set(true); this.errorAccion.set(''); peticion.pipe(finalize(() => this.guardando.set(false))).subscribe({ next: (t) => { this.ticket.set(t); despues?.(); this.cargar(); }, error: (e) => this.errorAccion.set(e?.error?.detail ?? 'No se pudo completar la acción. Revisá el estado y tus permisos.') }); }
  texto(valor: string): string { return valor.replaceAll('_', ' '); }
}
