import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { environment } from '../../environments/environment';
import {
  ArticuloConocimiento,
  ActivoGestion,
  ActivoCatalogo,
  ComentarioTicket,
  DashboardData,
  ReporteTicketsData,
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

  dashboardGestion(filtros: Record<string, string>) {
    const params = this.crearParametros(filtros);
    return this.http.get<DashboardData>(`${this.base}/dashboard/general/`, { params });
  }

  reporteTickets(filtros: Record<string, string>) {
    const params = this.crearParametros(filtros);
    return this.http.get<ReporteTicketsData>(`${this.base}/reportes/tickets/`, { params });
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

  aperturas(filtros: Record<string, string>) {
    return this.http.get<Pagina<TicketLista>>(`${this.base}/aperturas/`, {
      params: this.crearParametros(filtros),
    });
  }

  apertura(id: string) {
    return this.http.get<TicketDetalle>(`${this.base}/aperturas/${id}/`);
  }

  crearApertura(titulo: string) {
    return this.http.post<TicketDetalle>(`${this.base}/aperturas/`, { titulo });
  }

  cambiarEstadoApertura(id: string, estado: string, comentario = '') {
    return this.http.post<TicketDetalle>(
      `${this.base}/aperturas/${id}/cambiar-estado/`,
      { estado, comentario },
    );
  }

  agregarComentarioApertura(id: string, texto: string) {
    return this.http.post<ComentarioTicket>(
      `${this.base}/aperturas/${id}/comentarios/`,
      { tipo: 'NOTA', texto },
    );
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

  articulo(id: string) {
    return this.http.get<ArticuloConocimiento>(`${this.base}/conocimiento/articulos/${id}/`);
  }

  crearArticuloDesdeTicket(ticket: string) {
    return this.http.post<ArticuloConocimiento>(
      `${this.base}/conocimiento/articulos/desde-ticket/`, { ticket },
    );
  }

  enviarArticuloRevision(id: string) {
    return this.http.post<ArticuloConocimiento>(
      `${this.base}/conocimiento/articulos/${id}/enviar-a-revision/`, {},
    );
  }

  publicarArticulo(id: string) {
    return this.http.post<ArticuloConocimiento>(
      `${this.base}/conocimiento/articulos/${id}/publicar/`, {},
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

  categoriasGestion() {
    return this.http.get<import('./models').CategoriaGestion[]>(`${this.base}/catalogos/categorias/`, {
      params: new HttpParams().set('todos', 'true'),
    });
  }

  crearCategoria(datos: Record<string, unknown>) {
    return this.http.post<import('./models').CategoriaGestion>(`${this.base}/catalogos/categorias/`, datos);
  }

  actualizarCategoria(id: string, datos: Record<string, unknown>) {
    return this.http.patch<import('./models').CategoriaGestion>(`${this.base}/catalogos/categorias/${id}/`, datos);
  }

  desactivarCategoria(id: string) {
    return this.http.delete<void>(`${this.base}/catalogos/categorias/${id}/`);
  }

  subcategoriasGestion() {
    return this.http.get<import('./models').SubcategoriaGestion[]>(`${this.base}/catalogos/subcategorias/`, {
      params: new HttpParams().set('todos', 'true'),
    });
  }

  crearSubcategoria(datos: Record<string, unknown>) {
    return this.http.post<import('./models').SubcategoriaGestion>(`${this.base}/catalogos/subcategorias/`, datos);
  }

  actualizarSubcategoria(id: string, datos: Record<string, unknown>) {
    return this.http.patch<import('./models').SubcategoriaGestion>(`${this.base}/catalogos/subcategorias/${id}/`, datos);
  }

  desactivarSubcategoria(id: string) {
    return this.http.delete<void>(`${this.base}/catalogos/subcategorias/${id}/`);
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

  tecnicos() {
    return this.http.get<Array<{ id: string; username: string; nombre_completo: string }>>(
      `${this.base}/catalogos/tecnicos/`,
    );
  }

  asignarTicket(id: string, tecnico: string) {
    return this.http.post<TicketDetalle>(`${this.base}/tickets/${id}/asignar/`, { tecnico });
  }

  tomarTicket(id: string) {
    return this.http.post<TicketDetalle>(`${this.base}/tickets/${id}/tomar/`, {});
  }

  cambiarEstadoTicket(id: string, estado: string, comentario = '') {
    return this.http.post<TicketDetalle>(`${this.base}/tickets/${id}/cambiar-estado/`, {
      estado,
      comentario,
    });
  }

  resolverTicket(id: string, solucion: string) {
    return this.http.post<TicketDetalle>(`${this.base}/tickets/${id}/resolver/`, { solucion });
  }

  activos(search = '') {
    const params = search ? new HttpParams().set('search', search) : undefined;
    return this.http.get<Pagina<ActivoGestion>>(`${this.base}/configuracion/activos/`, { params });
  }

  crearActivo(datos: Record<string, unknown>) {
    return this.http.post<ActivoGestion>(`${this.base}/configuracion/activos/`, datos);
  }

  actualizarActivo(id: string, datos: Record<string, unknown>) {
    return this.http.patch<ActivoGestion>(`${this.base}/configuracion/activos/${id}/`, datos);
  }

  desactivarActivo(id: string) {
    return this.http.delete<void>(`${this.base}/configuracion/activos/${id}/`);
  }

  tiposActivo() {
    return this.http.get<OpcionCatalogo[]>(`${this.base}/catalogos/tipos-activo/`);
  }

  criticidades() {
    return this.http.get<OpcionCatalogo[]>(`${this.base}/catalogos/criticidades/`);
  }

  activosPorSucursal(sucursal: string) {
    return this.http.get<ActivoCatalogo[]>(`${this.base}/catalogos/activos/`, {
      params: new HttpParams().set('sucursal', sucursal),
    });
  }

  private crearParametros(filtros: Record<string, string>): HttpParams {
    let params = new HttpParams();
    Object.entries(filtros).forEach(([clave, valor]) => {
      if (valor) params = params.set(clave, valor);
    });
    return params;
  }
}
