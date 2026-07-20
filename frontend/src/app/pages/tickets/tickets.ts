import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../core/api.service';
import { TicketLista } from '../../core/models';

@Component({ selector: 'app-tickets-page', imports: [FormsModule, RouterLink, DatePipe], templateUrl: './tickets.html', styleUrl: './tickets.scss', changeDetection: ChangeDetectionStrategy.OnPush })
export class TicketsPage implements OnInit {
  private readonly api = inject(ApiService);
  readonly tickets = signal<TicketLista[]>([]);
  readonly total = signal(0);
  readonly cargando = signal(true);
  search = '';
  estado = '';

  ngOnInit(): void { this.cargar(); }
  cargar(): void {
    this.cargando.set(true);
    this.api.tickets({ search: this.search, estado: this.estado }).subscribe({
      next: (pagina) => { this.tickets.set(pagina.results); this.total.set(pagina.count); },
      complete: () => this.cargando.set(false), error: () => this.cargando.set(false),
    });
  }
  claseEstado(estado: string): string { return estado.toLowerCase(); }
  texto(valor: string): string { return valor.replaceAll('_', ' '); }
}
