export type Rol =
  | 'ADMINISTRADOR'
  | 'SUPERVISOR'
  | 'TECNICO'
  | 'JDISTRITO'
  | 'SUCURSAL'
  | 'CONSULTOR';

export interface UsuarioActual {
  id: string;
  username: string;
  first_name: string;
  last_name: string;
  nombre_completo: string;
  email: string;
  telefono: string;
  rol: Rol;
  sucursal: string | null;
  sucursal_nombre: string | null;
  sucursales_asignadas: Array<{ id: string; codigo: string; nombre: string }>;
}

export interface Pagina<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface TicketLista {
  id: string;
  codigo: string;
  titulo: string;
  sucursal: string;
  activo: string | null;
  prioridad_final: string;
  estado: string;
  tecnico_asignado: string | null;
  responsable_actual: string;
  creado_por: string;
  fecha_creacion: string;
}

export interface MovimientoTicket {
  id: string;
  fecha_creacion: string;
  usuario: string;
  tipo_movimiento: string;
  comentario: string;
}

export interface ComentarioTicket {
  id: string;
  tipo: string;
  texto: string;
  autor: string;
  fecha_creacion: string;
}

export interface TicketDetalle extends TicketLista {
  descripcion: string;
  solucion: string;
  historial: MovimientoTicket[];
  comentarios: ComentarioTicket[];
  adjuntos: Array<{
    id: string;
    archivo: string;
    nombre_original: string;
    descripcion: string;
    subido_por: string;
    fecha_creacion: string;
  }>;
}

export interface DashboardData {
  tickets_total?: number;
  tickets_abiertos?: number;
  tickets_en_proceso?: number;
  tickets_resueltos: number;
  tickets_cerrados?: number;
  tickets_activos?: number;
  por_estado: Array<{ estado: string; total: number }>;
}

export interface ArticuloConocimiento {
  id: string;
  codigo: string;
  titulo: string;
  resumen: string;
  categoria: string;
  estado: string;
  version: number;
  autor: string;
  fecha_modificacion: string;
  fecha_publicacion: string | null;
}

export interface OpcionCatalogo {
  id: string;
  nombre: string;
  codigo?: string;
  categoria?: string;
}

export interface UsuarioGestion {
  id: string;
  username: string;
  first_name: string;
  last_name: string;
  nombre_completo: string;
  email: string;
  telefono: string;
  rol: Rol;
  sucursal: string | null;
  sucursal_nombre: string | null;
  sucursales_asignadas: string[];
  activo_operativamente: boolean;
  is_active: boolean;
}
