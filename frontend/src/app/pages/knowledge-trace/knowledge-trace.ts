import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { forkJoin, switchMap } from 'rxjs';
import { ApiService } from '../../core/api.service';
import { ArticuloConocimiento, TicketDetalle } from '../../core/models';

@Component({
  selector: 'app-knowledge-trace-page',
  imports: [DatePipe, RouterLink],
  templateUrl: './knowledge-trace.html',
  styleUrl: './knowledge-trace.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class KnowledgeTracePage implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly api = inject(ApiService);
  readonly articulo = signal<ArticuloConocimiento | null>(null);
  readonly tickets = signal<TicketDetalle[]>([]);
  readonly cargando = signal(true);
  readonly error = signal('');

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id') ?? '';
    this.api.articulo(id).pipe(
      switchMap((articulo) => {
        this.articulo.set(articulo);
        const ids = articulo.tickets_relacionados ?? [];
        return ids.length ? forkJoin(ids.map((ticketId) => this.api.ticket(ticketId))) : forkJoin([]);
      }),
    ).subscribe({
      next: (tickets) => this.tickets.set(tickets),
      error: () => { this.error.set('No se pudo cargar la trazabilidad de este caso.'); this.cargando.set(false); },
      complete: () => this.cargando.set(false),
    });
  }

  texto(valor: string): string { return valor.replaceAll('_', ' '); }
}
