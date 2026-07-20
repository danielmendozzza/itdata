import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { environment } from '../../environments/environment';
import {
  ArticuloConocimiento,
  ComentarioTicket,
  DashboardData,
  OpcionCatalogo,
  Pagina,
  TicketDetalle,
  TicketLista,
  UsuarioGestion,
} from './models';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);
  private readonly base = environment.apiUrl;

  dashboard(global: boolean) {
    return this.http.get<DashboardData>(
      `${this.base}/dashboard/${global ? 'general' : 'mio'}/`,
    );
  }

  tickets(filtros: Record<string, string>) {
    let params = new HttpParams();
    Object.entries(filtros).forEach(([clave, valor]) => {
      if (valor) params = params.set(clave, valor);
    });
    return this.http.get<Pagina<TicketLista>>(`${this.base}/tickets/`, { params });
  }

  ticket(id: string) {
    return this.http.get<TicketDetalle>(`${this.base}/tickets/${id}/`);
  }

  agregarComentario(id: string, tipo: string, texto: string) {
    return this.http.post<ComentarioTicket>(`${this.base}/tickets/${id}/comentarios/`, {
      tipo,
      texto,
    });
  }

  articulos(search = '') {
    const params = search ? new HttpParams().set('search', search) : undefined;
    return this.http.get<Pagina<ArticuloConocimiento>>(
      `${this.base}/conocimiento/articulos/`,
      { params },
    );
  }

  sucursales() {
    return this.http.get<Pagina<OpcionCatalogo>>(`${this.base}/sucursales/`, {
      params: new HttpParams().set('page_size', '100'),
    });
  }

  categorias() {
    return this.http.get<OpcionCatalogo[]>(`${this.base}/catalogos/categorias/`);
  }

  subcategorias(categoria: string) {
    return this.http.get<OpcionCatalogo[]>(`${this.base}/catalogos/subcategorias/`, {
      params: new HttpParams().set('categoria', categoria),
    });
  }

  crearTicket(datos: Record<string, string | null>) {
    return this.http.post<TicketDetalle>(`${this.base}/tickets/`, datos);
  }

  usuarios(search = '') {
    const params = search ? new HttpParams().set('search', search) : undefined;
    return this.http.get<Pagina<UsuarioGestion>>(`${this.base}/configuracion/usuarios/`, {
      params,
    });
  }

  crearUsuario(datos: Record<string, unknown>) {
    return this.http.post<UsuarioGestion>(`${this.base}/configuracion/usuarios/`, datos);
  }

  actualizarUsuario(id: string, datos: Record<string, unknown>) {
    return this.http.patch<UsuarioGestion>(`${this.base}/configuracion/usuarios/${id}/`, datos);
  }

  desactivarUsuario(id: string) {
    return this.http.delete<void>(`${this.base}/configuracion/usuarios/${id}/`);
  }
}
