import {
  AfterViewInit,
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  Input,
  OnChanges,
  OnDestroy,
  SimpleChanges,
  ViewChild,
} from '@angular/core';
import * as Plotly from 'plotly.js-dist-min';

type Evolucion = { fecha: string; creados: number; resueltos: number };
type Estado = { estado: string; total: number };
type Comparativa = {
  serie: Array<{ mes: string; incidentes: number; ti_promedio_segundos: number | null; ti_mediana_segundos: number | null; terceros_promedio_segundos: number | null; terceros_mediana_segundos: number | null }>;
  sucursales: Array<{ mes: string; sucursal: string; total: number }>;
};

@Component({
  selector: 'app-plotly-chart',
  template: '<div #chart class="chart" role="img"></div>',
  styles: [
    ':host{display:block;width:100%;height:340px;min-height:340px}.chart{display:block;width:100%;height:100%}',
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PlotlyChartComponent implements AfterViewInit, OnChanges, OnDestroy {
  @ViewChild('chart', { static: true }) private chart!: ElementRef<HTMLDivElement>;
  @Input({ required: true }) kind!: 'evolucion' | 'estados' | 'incidentes-mes' | 'sucursales-mes' | 'tiempo-ti' | 'tiempo-terceros';
  @Input() evolucion: Evolucion[] = [];
  @Input() estados: Estado[] = [];
  @Input() comparativa: Comparativa = { serie: [], sucursales: [] };
  @Input() expanded = false;
  private ready = false;
  private observer?: ResizeObserver;
  private readonly themeListener = () => this.render();

  ngAfterViewInit(): void {
    this.ready = true;
    this.render();
    this.observer = new ResizeObserver(() => {
      if (this.ready) void Plotly.Plots.resize(this.chart.nativeElement);
    });
    this.observer.observe(this.chart.nativeElement);
    window.addEventListener('itdata-theme-change', this.themeListener);
  }

  ngOnChanges(_changes: SimpleChanges): void {
    if (this.ready) this.render();
  }

  ngOnDestroy(): void {
    this.observer?.disconnect();
    window.removeEventListener('itdata-theme-change', this.themeListener);
    if (this.ready) Plotly.purge(this.chart.nativeElement);
  }

  private render(): void {
    const estilos = getComputedStyle(document.documentElement);
    const oscuro = document.documentElement.dataset['theme'] === 'dark';
    const cian = oscuro ? '#20c7e8' : '#2879bd';
    const violeta = oscuro ? '#8b6cf0' : '#32a572';
    const texto = estilos.getPropertyValue('--slate-500').trim() || '#52677d';
    const grilla = estilos.getPropertyValue('--blue-border').trim() || '#edf3f8';
    const tooltip = estilos.getPropertyValue('--surface-strong').trim() || '#0b2948';
    const config: Partial<Plotly.Config> = {
      responsive: true,
      displaylogo: false,
      modeBarButtonsToRemove: ['lasso2d', 'select2d'],
    };
    const common: Partial<Plotly.Layout> = {
      autosize: true,
      height: this.expanded ? 520 : 340,
      margin: { l: 48, r: 22, t: 16, b: 45 },
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)',
      font: { family: 'Inter, system-ui, sans-serif', color: texto, size: 11 },
      hoverlabel: { bgcolor: tooltip, bordercolor: grilla, font: { color: estilos.getPropertyValue('--navy-950').trim() } },
    };

    if (this.kind === 'evolucion') {
      const fechas = this.evolucion.map((item) => item.fecha);
      const traces: Plotly.Data[] = [
        {
          x: fechas, y: this.evolucion.map((item) => item.creados),
          name: 'Creados', type: 'scatter', mode: 'lines+markers',
          line: { color: cian, width: 3, shape: 'spline' },
          marker: { color: cian, size: 7, line: { color: oscuro ? '#0f1a26' : '#fff', width: 1 } },
          fill: 'tozeroy', fillcolor: oscuro ? 'rgba(32,199,232,.10)' : 'rgba(40,121,189,.07)',
          hovertemplate: '<b>%{x}</b><br>Creados: %{y}<extra></extra>',
        },
        {
          x: fechas, y: this.evolucion.map((item) => item.resueltos),
          name: 'Resueltos', type: 'scatter', mode: 'lines+markers',
          line: { color: violeta, width: 3, shape: 'spline' },
          marker: { color: violeta, size: 7, line: { color: oscuro ? '#0f1a26' : '#fff', width: 1 } },
          fill: 'tozeroy', fillcolor: oscuro ? 'rgba(139,108,240,.09)' : 'rgba(50,165,114,.06)',
          hovertemplate: '<b>%{x}</b><br>Resueltos: %{y}<extra></extra>',
        },
      ];
      void Plotly.react(this.chart.nativeElement, traces, {
        ...common,
        hovermode: 'x unified',
        legend: { orientation: 'h', x: 0, y: 1.12 },
        xaxis: { gridcolor: grilla, tickformat: '%d/%m' },
        yaxis: { gridcolor: grilla, rangemode: 'tozero', dtick: 1 },
      }, config);
      return;
    }

    if (this.kind === 'incidentes-mes') {
      void Plotly.react(this.chart.nativeElement, [{ x: this.comparativa.serie.map(i => i.mes), y: this.comparativa.serie.map(i => i.incidentes), type: 'scatter', mode: 'lines+markers', name: 'Incidentes', line: { color: cian, width: 3, shape: 'spline' }, marker: { color: cian, size: 7, line: { color: oscuro ? '#0f1a26' : '#fff', width: 1 } }, fill: 'tozeroy', fillcolor: oscuro ? 'rgba(32,199,232,.12)' : 'rgba(40,121,189,.08)', hovertemplate: '<b>%{x}</b><br>Incidentes: %{y}<extra></extra>' }], { ...common, showlegend: false, xaxis: { type: 'category', gridcolor: grilla }, yaxis: { gridcolor: grilla, rangemode: 'tozero', dtick: 1 } }, config);
      return;
    }

    if (this.kind === 'sucursales-mes') {
      const totales = new Map<string, number>();
      this.comparativa.sucursales.forEach(i => totales.set(i.sucursal, (totales.get(i.sucursal) ?? 0) + i.total));
      const top = [...totales.entries()].sort((a, b) => b[1] - a[1]).slice(0, 5).map(i => i[0]);
      const meses = this.comparativa.serie.map(i => i.mes);
      const colores = oscuro ? ['#20c7e8', '#8b6cf0', '#4cc99a', '#e8a84d', '#e36b86'] : ['#2879bd', '#32a572', '#e59a32', '#8b67c7', '#d85b73'];
      const traces: Plotly.Data[] = top.map((sucursal, indice) => ({ x: meses, y: meses.map(mes => this.comparativa.sucursales.find(i => i.mes === mes && i.sucursal === sucursal)?.total ?? 0), name: sucursal, type: 'scatter', mode: 'lines+markers', line: { color: colores[indice], width: 2.5, shape: 'spline' }, marker: { color: colores[indice], size: 6 }, hovertemplate: `<b>${sucursal}</b><br>%{x}: %{y}<extra></extra>` }));
      void Plotly.react(this.chart.nativeElement, traces, { ...common, hovermode: 'x unified', legend: { orientation: 'h', x: 0, y: 1.16 }, xaxis: { type: 'category', gridcolor: grilla }, yaxis: { gridcolor: grilla, rangemode: 'tozero', dtick: 1 } }, config);
      return;
    }

    if (this.kind === 'tiempo-ti' || this.kind === 'tiempo-terceros') {
      const esTi = this.kind === 'tiempo-ti';
      const promedio = esTi ? 'ti_promedio_segundos' : 'terceros_promedio_segundos';
      const mediana = esTi ? 'ti_mediana_segundos' : 'terceros_mediana_segundos';
      const meses = this.comparativa.serie.map(i => i.mes);
      const horas = (valor: number | null) => valor === null ? null : Number((valor / 3600).toFixed(2));
      const traces: Plotly.Data[] = [
        { x: meses, y: this.comparativa.serie.map(i => horas(i[promedio])), name: 'Promedio', type: 'scatter', mode: 'lines+markers', line: { color: cian, width: 3, shape: 'spline' }, marker: { color: cian, size: 7 }, fill: 'tozeroy', fillcolor: oscuro ? 'rgba(32,199,232,.10)' : 'rgba(40,121,189,.06)', hovertemplate: '<b>%{x}</b><br>Promedio: %{y:.1f} h<extra></extra>' },
        { x: meses, y: this.comparativa.serie.map(i => horas(i[mediana])), name: 'Mediana', type: 'scatter', mode: 'lines+markers', line: { color: violeta, width: 2.5, dash: 'dot', shape: 'spline' }, marker: { color: violeta, size: 6 }, hovertemplate: '<b>%{x}</b><br>Mediana: %{y:.1f} h<extra></extra>' },
      ];
      void Plotly.react(this.chart.nativeElement, traces, { ...common, hovermode: 'x unified', legend: { orientation: 'h', x: 0, y: 1.12 }, xaxis: { type: 'category', gridcolor: grilla }, yaxis: { title: { text: 'Horas' }, gridcolor: grilla, rangemode: 'tozero' } }, config);
      return;
    }

    const ordenados = [...this.estados].sort((a, b) => a.total - b.total);
    void Plotly.react(this.chart.nativeElement, [{
      x: ordenados.map((item) => item.total),
      y: ordenados.map((item) => item.estado.replaceAll('_', ' ').toLowerCase()),
      type: 'bar',
      orientation: 'h',
      marker: { color: oscuro ? cian : '#2879bd', line: { color: oscuro ? '#167d91' : '#185d98', width: 1 } },
      text: ordenados.map((item) => String(item.total)),
      textposition: 'auto',
      hovertemplate: '<b>%{y}</b><br>Tickets: %{x}<extra></extra>',
    }], {
      ...common,
      margin: { l: this.expanded ? 165 : 125, r: 22, t: 16, b: 40 },
      showlegend: false,
      xaxis: { gridcolor: grilla, rangemode: 'tozero', dtick: 1 },
      yaxis: { automargin: true },
    }, config);
  }
}
