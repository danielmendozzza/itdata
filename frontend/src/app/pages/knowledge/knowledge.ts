import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/api.service';
import { ArticuloConocimiento } from '../../core/models';

@Component({ selector:'app-knowledge-page', imports:[FormsModule,DatePipe], templateUrl:'./knowledge.html', styleUrl:'./knowledge.scss', changeDetection:ChangeDetectionStrategy.OnPush })
export class KnowledgePage implements OnInit {
  private readonly api=inject(ApiService); readonly articulos=signal<ArticuloConocimiento[]>([]); readonly total=signal(0); readonly cargando=signal(true); search='';
  ngOnInit():void{this.cargar()} cargar():void{this.cargando.set(true);this.api.articulos(this.search).subscribe({next:(p)=>{this.articulos.set(p.results);this.total.set(p.count)},complete:()=>this.cargando.set(false),error:()=>this.cargando.set(false)})}
}
