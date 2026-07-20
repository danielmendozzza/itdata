import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ApiService } from '../../core/api.service';
import { TicketDetalle } from '../../core/models';

@Component({ selector: 'app-ticket-detail-page', imports: [DatePipe, FormsModule, RouterLink], templateUrl: './ticket-detail.html', styleUrl: './ticket-detail.scss', changeDetection: ChangeDetectionStrategy.OnPush })
export class TicketDetailPage implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly api = inject(ApiService);
  readonly ticket = signal<TicketDetalle | null>(null);
  readonly cargando = signal(true);
  readonly guardando = signal(false);
  tipoComentario = 'NOTA';
  comentario = '';
  private id = '';

  ngOnInit(): void { this.id = this.route.snapshot.paramMap.get('id') ?? ''; this.cargar(); }
  cargar(): void { this.api.ticket(this.id).subscribe({ next: (ticket) => this.ticket.set(ticket), complete: () => this.cargando.set(false), error: () => this.cargando.set(false) }); }
  guardarComentario(): void {
    if (!this.comentario.trim()) return;
    this.guardando.set(true);
    this.api.agregarComentario(this.id, this.tipoComentario, this.comentario).subscribe({ next: () => { this.comentario = ''; this.cargar(); }, complete: () => this.guardando.set(false), error: () => this.guardando.set(false) });
  }
  texto(valor: string): string { return valor.replaceAll('_', ' '); }
}
