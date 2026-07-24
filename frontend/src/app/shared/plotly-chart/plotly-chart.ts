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
  @Input({ required: true }) kind!: 'evolucion' | 'estados';
  @Input() evolucion: Evolucion[] = [];
  @Input() estados: Estado[] = [];
  @Input() expanded = false;
  private ready = false;
  private observer?: ResizeObserver;

  ngAfterViewInit(): void {
    this.ready = true;
    this.render();
    this.observer = new ResizeObserver(() => {
      if (this.ready) void Plotly.Plots.resize(this.chart.nativeElement);
    });
    this.observer.observe(this.chart.nativeElement);
  }

  ngOnChanges(_changes: SimpleChanges): void {
    if (this.ready) this.render();
  }

  ngOnDestroy(): void {
    this.observer?.disconnect();
    if (this.ready) Plotly.purge(this.chart.nativeElement);
  }

  private render(): void {
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
      font: { family: 'Inter, system-ui, sans-serif', color: '#52677d', size: 11 },
      hoverlabel: { bgcolor: '#0b2948', bordercolor: '#0b2948', font: { color: '#fff' } },
    };

    if (this.kind === 'evolucion') {
      const fechas = this.evolucion.map((item) => item.fecha);
      const traces: Plotly.Data[] = [
        {
          x: fechas, y: this.evolucion.map((item) => item.creados),
          name: 'Creados', type: 'scatter', mode: 'lines+markers',
          line: { color: '#2879bd', width: 3, shape: 'spline' },
          marker: { color: '#2879bd', size: 7 },
          hovertemplate: '<b>%{x}</b><br>Creados: %{y}<extra></extra>',
        },
        {
          x: fechas, y: this.evolucion.map((item) => item.resueltos),
          name: 'Resueltos', type: 'scatter', mode: 'lines+markers',
          line: { color: '#32a572', width: 3, shape: 'spline' },
          marker: { color: '#32a572', size: 7 },
          hovertemplate: '<b>%{x}</b><br>Resueltos: %{y}<extra></extra>',
        },
      ];
      void Plotly.react(this.chart.nativeElement, traces, {
        ...common,
        hovermode: 'x unified',
        legend: { orientation: 'h', x: 0, y: 1.12 },
        xaxis: { gridcolor: '#edf3f8', tickformat: '%d/%m' },
        yaxis: { gridcolor: '#edf3f8', rangemode: 'tozero', dtick: 1 },
      }, config);
      return;
    }

    const ordenados = [...this.estados].sort((a, b) => a.total - b.total);
    void Plotly.react(this.chart.nativeElement, [{
      x: ordenados.map((item) => item.total),
      y: ordenados.map((item) => item.estado.replaceAll('_', ' ').toLowerCase()),
      type: 'bar',
      orientation: 'h',
      marker: { color: '#2879bd', line: { color: '#185d98', width: 1 } },
      text: ordenados.map((item) => String(item.total)),
      textposition: 'auto',
      hovertemplate: '<b>%{y}</b><br>Tickets: %{x}<extra></extra>',
    }], {
      ...common,
      margin: { l: this.expanded ? 165 : 125, r: 22, t: 16, b: 40 },
      showlegend: false,
      xaxis: { gridcolor: '#edf3f8', rangemode: 'tozero', dtick: 1 },
      yaxis: { automargin: true },
    }, config);
  }
}
