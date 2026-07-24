import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../core/api.service';
import { TicketLista } from '../../core/models';

@Component({
  selector: 'app-openings-page',
  imports: [DatePipe, FormsModule, RouterLink],
  templateUrl: './openings.html',
  styleUrl: './openings.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class OpeningsPage implements OnInit {
  private readonly api = inject(ApiService);
  readonly aperturas = signal<TicketLista[]>([]);
  readonly total = signal(0);
  readonly cargando = signal(true);
  search = '';
  estado = '';

  ngOnInit(): void { this.cargar(); }
  cargar(): void {
    this.cargando.set(true);
    this.api.aperturas({ search: this.search, estado: this.estado }).subscribe({
      next: (pagina) => { this.aperturas.set(pagina.results); this.total.set(pagina.count); },
      complete: () => this.cargando.set(false),
      error: () => this.cargando.set(false),
    });
  }
  texto(valor: string): string { return valor.replaceAll('_', ' ').toLowerCase(); }
}
