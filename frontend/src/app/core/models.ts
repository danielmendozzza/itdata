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

export interface CategoriaGestion {
  id: string;
  nombre: string;
  descripcion: string;
  activo: boolean;
}

export interface SubcategoriaGestion extends CategoriaGestion {
  categoria: string;
}

export interface TicketLista {
  id: string;
  codigo: string;
  titulo: string;
  sucursal: string | null;
  activo: string | null;
  prioridad_final: string;
  estado: string;
  tecnico_asignado: string | null;
  responsable_actual: string;
  responsable_actual_nombre: string;
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
  sucursal_nombre: string | null;
  activo_nombre: string | null;
  tecnico_asignado_nombre: string | null;
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
  tickets_activos?: number;
  tickets_criticos_abiertos?: number;
  esperando_terceros?: number;
  aperturas_pendientes?: number;
  aperturas_concretadas?: number;
  tiempo_promedio_resolucion_segundos?: number | null;
  por_estado: Array<{ estado: string; total: number }>;
  evolucion_diaria?: Array<{ fecha: string; creados: number; resueltos: number }>;
}

export interface ReporteTicketsData {
  total: number;
  por_estado: Array<{ estado: string; total: number }>;
  por_prioridad: Array<{ prioridad_final: string; total: number }>;
  por_responsable: Array<{ responsable_actual: string; total: number }>;
  por_sucursal: Array<{ sucursal__nombre: string; total: number }>;
  por_categoria: Array<{ categoria__nombre: string; total: number }>;
  por_tecnico: Array<{ tecnico_asignado__username: string | null; total: number }>;
  tiempo_promedio_resolucion_segundos: number | null;
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
  tickets_relacionados?: string[];
}

export interface OpcionCatalogo {
  id: string;
  nombre: string;
  codigo?: string;
  categoria?: string;
}

export interface SucursalGestion {
  id: string;
  codigo: string;
  nombre: string;
  direccion: string;
  telefono: string;
  encargado: string;
  activo: boolean;
}

export interface TipoActivoGestion {
  id: string;
  nombre: string;
  descripcion: string;
  activo: boolean;
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

export interface ActivoGestion {
  id: string;
  codigo: string;
  nombre: string;
  tipo_activo: string;
  tipo_activo_nombre: string;
  sucursal: string | null;
  sucursal_nombre: string | null;
  criticidad: string;
  criticidad_nombre: string;
  marca: string;
  modelo: string;
  numero_serie: string;
  direccion_ip: string | null;
  estado: 'OPERATIVO' | 'EN_REPARACION' | 'FUERA_SERVICIO' | 'BAJA';
  activo: boolean;
}

export interface ActivoCatalogo {
  id: string;
  codigo: string;
  nombre: string;
  sucursal: string | null;
  estado: string;
}
