# API Contract — Tickets

Base path: `/api/v1/tickets/`

Endpoints:

- GET `/api/v1/tickets/` — Lista de tickets (paginado)
  - Query params: `search`, `ordering`, `estado`, `prioridad_final`, `categoria`, `sucursal`

- POST `/api/v1/tickets/` — Crear ticket
  - Body (JSON):

```json
{
  "titulo": "Falla en impresora",
  "descripcion": "La impresora no enciende",
  "sucursal": "<sucursal_id>",
  "activo": "<activo_id>",
  "categoria": "<categoria_id>",
  "subcategoria": "<subcategoria_id>",
  "origen": "PORTAL_SUCURSAL"
}
```

- GET `/api/v1/tickets/{id}/` — Detalle de ticket (incluye historial)

- PUT/PATCH `/api/v1/tickets/{id}/` — Actualizar ticket
  - Body ejemplo para cambiar estado o prioridad:

```json
{
  "estado": "EN_PROCESO",
  "prioridad_final": "ALTA",
  "motivo_cambio_prioridad": "Aumentó criticidad"
}
```

Authentication: JWT (obtener token en `/api/v1/auth/login/`)

Permissions: implementadas por rol. Ver `operacion/permissions.py`.

Notes for frontend:
- Use the `TicketCreateSerializer` fields for create requests.
- Responses include `codigo`, `numero` generated server-side.
- Consult the OpenAPI schema at `/api/schema/` (drf-spectacular) for full contract.

## Reportes y dashboard

Disponibles para Administrador, Supervisor y Consultor:

- GET `/api/v1/reportes/tickets/`
  - Filtros: `fecha_desde`, `fecha_hasta`, `estado`, `prioridad_final`,
    `responsable_actual`, `origen`, `categoria`, `sucursal` y
    `tecnico_asignado`.
  - Devuelve totales por estado, prioridad, responsable, sucursal,
    categoría y técnico.
  - Incluye el tiempo promedio de resolución en segundos cuando existen
    tickets resueltos.

- GET `/api/v1/dashboard/general/`
  - Devuelve indicadores generales, distribución por estado y evolución
    diaria.

Ejemplo:

```text
/api/v1/reportes/tickets/?fecha_desde=2026-07-01&fecha_hasta=2026-07-31&sucursal=<uuid>
```

## Ciclo operativo del ticket

Las transiciones se realizan mediante acciones específicas; el campo `estado`
no se modifica directamente con el `PATCH` genérico.

- POST `/api/v1/tickets/{id}/asignar/`
  - Administrador o Supervisor.
  - Body: `{"tecnico": "<uuid>"}`.
- POST `/api/v1/tickets/{id}/tomar/`
  - Técnico asignado, o un técnico cuando el ticket todavía no tiene asignación.
- POST `/api/v1/tickets/{id}/resolver/`
  - Administrador, Supervisor o Técnico responsable.
  - Body: `{"solucion": "Descripción de la solución"}`.
- POST `/api/v1/tickets/{id}/cerrar/`
  - Administrador o Supervisor.
  - El ticket debe encontrarse en estado `RESUELTO`.
  - Body opcional: `{"comentario": "Validación de cierre"}`.

Cada acción actualiza el estado, el usuario responsable, la fecha correspondiente
y el historial dentro de una misma transacción de base de datos.

## Documentación técnica del ticket

- GET/POST `/api/v1/tickets/{id}/comentarios/`
  - Tipos: `NOTA`, `DIAGNOSTICO`, `ACCION_REALIZADA` y
    `RESPUESTA_USUARIO`.
  - El autor y la fecha se registran automáticamente.
  - Consultor tiene acceso de solo lectura.
- GET/POST `/api/v1/tickets/{id}/adjuntos/`
  - Formato `multipart/form-data`.
  - Tamaño máximo: 10 MB.
  - Extensiones: PDF, imágenes, texto, logs, CSV, DOCX y XLSX.
- DELETE `/api/v1/tickets/{id}/adjuntos/{adjunto_id}/`
  - Puede eliminar el autor del archivo, Administrador o Supervisor.

Los comentarios y adjuntos también generan entradas en el historial del ticket.

## Separación de dashboards

- GET `/api/v1/dashboard/general/`
  - Exclusivo para Administrador, Supervisor y Consultor.
- GET `/api/v1/dashboard/mio/`
  - Resumen personal con tickets activos, resueltos y distribución por estado.
  - Para un Técnico considera únicamente tickets asignados o tomados por él.
  - Para Jefe de Distrito y Sucursal respeta su alcance de sucursales.

## Base de conocimiento

- GET/POST `/api/v1/conocimiento/articulos/`
- GET/PATCH `/api/v1/conocimiento/articulos/{id}/`
- POST `/api/v1/conocimiento/articulos/desde-ticket/`
  - Genera un borrador a partir de un ticket resuelto o cerrado.
  - Reutiliza descripción, diagnóstico, acciones, solución, categoría y activo.
  - El Técnico debe ser responsable del ticket.
- POST `/api/v1/conocimiento/articulos/{id}/enviar-a-revision/`
- POST `/api/v1/conocimiento/articulos/{id}/publicar/`
- POST `/api/v1/conocimiento/articulos/{id}/archivar/`

Flujo editorial:

```text
BORRADOR -> EN_REVISION -> PUBLICADO -> ARCHIVADO
```

Los Técnicos crean y editan sus borradores. Administrador y Supervisor revisan,
publican y archivan. Consultor, Jefe de Distrito y Sucursal solo visualizan
artículos publicados. El parámetro `search` busca dentro del título, resumen,
síntomas, diagnóstico, causa, procedimiento, palabras clave y tickets relacionados.
