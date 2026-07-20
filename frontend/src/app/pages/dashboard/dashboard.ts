import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../core/api.service';
import { AuthService } from '../../core/auth.service';
import { DashboardData } from '../../core/models';

@Component({
  selector: 'app-dashboard-page',
  imports: [RouterLink, DatePipe],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DashboardPage implements OnInit {
  readonly auth = inject(AuthService);
  private readonly api = inject(ApiService);
  readonly datos = signal<DashboardData | null>(null);
  readonly cargando = signal(true);
  readonly hoy = new Date();

  ngOnInit(): void {
    const cargar = () => {
      this.api.dashboard(this.auth.esRolGlobal()).subscribe({
        next: (datos) => this.datos.set(datos),
        complete: () => this.cargando.set(false),
        error: () => this.cargando.set(false),
      });
    };
    if (this.auth.usuario()) cargar();
    else this.auth.cargarUsuario().subscribe({ next: cargar });
  }

  etiqueta(estado: string): string {
    return estado.replaceAll('_', ' ').toLowerCase();
  }
}
