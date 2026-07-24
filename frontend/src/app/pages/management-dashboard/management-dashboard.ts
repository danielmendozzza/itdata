import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';
import { ApiService } from '../../core/api.service';
import { PlotlyChartComponent } from '../../shared/plotly-chart/plotly-chart';
import {
  DashboardData,
  OpcionCatalogo,
  ReporteTicketsData,
} from '../../core/models';

@Component({
  selector: 'app-management-dashboard-page',
  imports: [FormsModule, RouterLink, PlotlyChartComponent],
  templateUrl: './management-dashboard.html',
  styleUrls: ['./management-dashboard.scss', './management-dashboard-modal.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ManagementDashboardPage implements OnInit {
  private readonly api = inject(ApiService);
  readonly resumen = signal<DashboardData | null>(null);
  readonly reporte = signal<ReporteTicketsData | null>(null);
  readonly sucursales = signal<OpcionCatalogo[]>([]);
  readonly tecnicos = signal<Array<{ id: string; username: string; nombre_completo: string }>>([]);
  readonly cargando = signal(true);
  readonly error = signal('');
  readonly graficoExpandido = signal<'evolucion' | 'estados' | null>(null);
  fechaDesde = '';
  fechaHasta = '';
  sucursal = '';
  tecnico = '';
  estado = '';

  ngOnInit(): void {
    const hasta = new Date();
    const desde = new Date();
    desde.setDate(hasta.getDate() - 29);
    this.fechaDesde = this.fechaLocal(desde);
    this.fechaHasta = this.fechaLocal(hasta);
    forkJoin({ sucursales: this.api.sucursales(), tecnicos: this.api.tecnicos() }).subscribe({
      next: ({ sucursales, tecnicos }) => {
        this.sucursales.set(sucursales.results);
        this.tecnicos.set(tecnicos);
      },
    });
    this.cargar();
  }

  cargar(): void {
    this.cargando.set(true);
    this.error.set('');
    const filtros = {
      fecha_desde: this.fechaDesde,
      fecha_hasta: this.fechaHasta,
      sucursal: this.sucursal,
      tecnico_asignado: this.tecnico,
      estado: this.estado,
    };
    forkJoin({
      resumen: this.api.dashboardGestion(filtros),
      reporte: this.api.reporteTickets(filtros),
    }).subscribe({
      next: ({ resumen, reporte }) => {
        this.resumen.set(resumen);
        this.reporte.set(reporte);
      },
      error: () => {
        this.error.set('No se pudo cargar el informe con los filtros seleccionados.');
        this.cargando.set(false);
      },
      complete: () => this.cargando.set(false),
    });
  }

  limpiar(): void {
    this.sucursal = '';
    this.tecnico = '';
    this.estado = '';
    this.cargar();
  }

  etiqueta(valor: string | null): string {
    return (valor || 'Sin asignar').replaceAll('_', ' ').toLowerCase();
  }

  private fechaLocal(fecha: Date): string {
    const offset = fecha.getTimezoneOffset() * 60_000;
    return new Date(fecha.getTime() - offset).toISOString().slice(0, 10);
  }
}
