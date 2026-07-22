import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { finalize } from 'rxjs';
import { ApiService } from '../../core/api.service';
import { AuthService } from '../../core/auth.service';
import { ArticuloConocimiento } from '../../core/models';

@Component({ selector:'app-knowledge-page', imports:[FormsModule,RouterLink], templateUrl:'./knowledge.html', styleUrl:'./knowledge.scss', changeDetection:ChangeDetectionStrategy.OnPush })
export class KnowledgePage implements OnInit {
  private readonly api = inject(ApiService);
  readonly auth = inject(AuthService);
  readonly articulos = signal<ArticuloConocimiento[]>([]);
  readonly total = signal(0);
  readonly cargando = signal(true);
  readonly procesando = signal<string | null>(null);
  readonly error = signal('');
  search = '';

  ngOnInit(): void { this.cargar(); }
  cargar(): void { this.cargando.set(true); this.api.articulos(this.search).subscribe({ next:(p) => { this.articulos.set(p.results); this.total.set(p.count); }, complete:() => this.cargando.set(false), error:() => this.cargando.set(false) }); }
  puedeEnviar(a: ArticuloConocimiento): boolean { return a.estado === 'BORRADOR' && (this.esAdministrador() || a.autor === this.auth.usuario()?.username); }
  puedePublicar(a: ArticuloConocimiento): boolean { return ['BORRADOR', 'EN_REVISION'].includes(a.estado) && this.esAdministrador(); }
  enviarRevision(a: ArticuloConocimiento): void { this.ejecutar(a.id, this.api.enviarArticuloRevision(a.id)); }
  publicar(a: ArticuloConocimiento): void { this.ejecutar(a.id, this.api.publicarArticulo(a.id)); }
  private esAdministrador(): boolean { return ['ADMINISTRADOR', 'SUPERVISOR'].includes(this.auth.usuario()?.rol ?? ''); }
  private ejecutar(id: string, peticion: ReturnType<ApiService['publicarArticulo']>): void { this.procesando.set(id); this.error.set(''); peticion.pipe(finalize(() => this.procesando.set(null))).subscribe({ next: () => this.cargar(), error: (e) => this.error.set(e?.error?.detail ?? 'No se pudo completar la operación editorial.') }); }
}
