import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DecimalPipe } from '@angular/common';
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
  imports: [FormsModule, DecimalPipe, RouterLink, PlotlyChartComponent],
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
  readonly graficoExpandido = signal<'evolucion' | 'estados' | 'incidentes-mes' | 'sucursales-mes' | 'tiempo-ti' | 'tiempo-terceros' | null>(null);
  readonly graficoComparativo = signal<'incidentes-mes' | 'sucursales-mes' | 'tiempo-ti' | 'tiempo-terceros'>('incidentes-mes');
  fechaDesde = '';
  fechaHasta = '';
  sucursal = '';
  tecnico = '';
  estado = '';
  meses = '12';

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
      meses: this.meses,
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

  variacionIncidentes(): number | null {
    const serie = this.reporte()?.comparativa_mensual.serie ?? [];
    if (serie.length < 2) return null;
    const actual = serie.at(-1)!.incidentes;
    const anterior = serie.at(-2)!.incidentes;
    if (!anterior) return actual ? 100 : 0;
    return ((actual - anterior) / anterior) * 100;
  }

  formatoTiempo(segundos: number | null): string {
    if (segundos === null) return 'Sin datos';
    const horas = segundos / 3600;
    if (horas < 24) return `${horas.toFixed(1)} h`;
    return `${(horas / 24).toFixed(1)} días`;
  }

  private fechaLocal(fecha: Date): string {
    const offset = fecha.getTimezoneOffset() * 60_000;
    return new Date(fecha.getTime() - offset).toISOString().slice(0, 10);
  }
}
