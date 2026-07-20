from django.contrib import admin

from .models import (
    AdjuntoTicket,
    Categoria,
    ComentarioTicket,
    HistorialTicket,
    Subcategoria,
    Ticket,
)
from .services import crear_movimiento_historial


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "activo",
        "fecha_creacion",
    )

    list_filter = (
        "activo",
    )

    search_fields = (
        "nombre",
        "descripcion",
    )


@admin.register(Subcategoria)
class SubcategoriaAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "categoria",
        "activo",
    )

    list_filter = (
        "categoria",
        "activo",
    )

    search_fields = (
        "nombre",
        "categoria__nombre",
    )

    autocomplete_fields = (
        "categoria",
    )


class HistorialTicketInline(admin.TabularInline):
    model = HistorialTicket
    extra = 0
    can_delete = False

    fields = (
        "fecha_creacion",
        "usuario",
        "tipo_movimiento",
        "comentario",
    )

    readonly_fields = (
        "fecha_creacion",
        "usuario",
        "tipo_movimiento",
        "comentario",
    )

    ordering = (
        "fecha_creacion",
    )


class ComentarioTicketInline(admin.TabularInline):
    model = ComentarioTicket
    extra = 0
    can_delete = False
    fields = ("fecha_creacion", "tipo", "autor", "texto")
    readonly_fields = fields
    ordering = ("fecha_creacion",)


class AdjuntoTicketInline(admin.TabularInline):
    model = AdjuntoTicket
    extra = 0
    can_delete = False
    fields = (
        "fecha_creacion",
        "nombre_original",
        "descripcion",
        "subido_por",
        "archivo",
    )
    readonly_fields = fields
    ordering = ("fecha_creacion",)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "titulo",
        "sucursal",
        "activo",
        "prioridad_final",
        "estado",
        "tecnico_asignado",
        "responsable_actual",
        "fecha_creacion",
    )

    list_filter = (
        "estado",
        "prioridad_final",
        "responsable_actual",
        "origen",
        "categoria",
        "sucursal",
    )

    search_fields = (
        "codigo",
        "titulo",
        "descripcion",
        "sucursal__nombre",
        "activo__nombre",
        "activo__codigo",
    )

    autocomplete_fields = (
        "sucursal",
        "activo",
        "categoria",
        "subcategoria",
        "tecnico_asignado",
    )

    readonly_fields = (
        "id",
        "numero",
        "codigo",
        "creado_por",
        "prioridad_sugerida",
        "tomado_por",
        "resuelto_por",
        "cerrado_por",
        "fecha_creacion",
        "fecha_modificacion",
        "fecha_toma",
        "fecha_resolucion",
        "fecha_cierre",
    )

    inlines = (
        HistorialTicketInline,
        ComentarioTicketInline,
        AdjuntoTicketInline,
    )

    fieldsets = (
        (
            "Identificación",
            {
                "fields": (
                    "id",
                    "numero",
                    "codigo",
                    "titulo",
                    "descripcion",
                )
            },
        ),
        (
            "Origen del ticket",
            {
                "fields": (
                    "sucursal",
                    "activo",
                    "categoria",
                    "subcategoria",
                    "origen",
                    "creado_por",
                )
            },
        ),
        (
            "Gestión técnica",
            {
                "fields": (
                    "estado",
                    "prioridad_sugerida",
                    "prioridad_final",
                    "motivo_cambio_prioridad",
                    "responsable_actual",
                    "tecnico_asignado",
                    "tomado_por",
                    "resuelto_por",
                    "cerrado_por",
                )
            },
        ),
        (
            "Fechas",
            {
                "fields": (
                    "fecha_reporte",
                    "fecha_creacion",
                    "fecha_modificacion",
                    "fecha_toma",
                    "fecha_resolucion",
                    "fecha_cierre",
                )
            },
        ),
        (
            "Resolución",
            {
                "fields": (
                    "solucion",
                )
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        es_nuevo = not change

        estado_anterior = ""
        prioridad_anterior = ""
        responsable_anterior = ""

        if change:
            ticket_anterior = Ticket.objects.get(pk=obj.pk)

            estado_anterior = ticket_anterior.estado
            prioridad_anterior = ticket_anterior.prioridad_final
            responsable_anterior = ticket_anterior.responsable_actual

        if es_nuevo:
            obj.creado_por = request.user

        super().save_model(
            request,
            obj,
            form,
            change,
        )

        if es_nuevo:
            crear_movimiento_historial(
                ticket=obj,
                usuario=request.user,
                tipo_movimiento=HistorialTicket.TipoMovimiento.CREACION,
                comentario="Ticket creado.",
                estado_nuevo=obj.estado,
                prioridad_nueva=obj.prioridad_final,
                responsable_nuevo=obj.responsable_actual,
            )

            return

        if estado_anterior != obj.estado:
            crear_movimiento_historial(
                ticket=obj,
                usuario=request.user,
                tipo_movimiento=(
                    HistorialTicket.TipoMovimiento.CAMBIO_ESTADO
                ),
                comentario=(
                    f"Estado cambiado de "
                    f"{estado_anterior} a {obj.estado}."
                ),
                estado_anterior=estado_anterior,
                estado_nuevo=obj.estado,
            )

        if prioridad_anterior != obj.prioridad_final:
            crear_movimiento_historial(
                ticket=obj,
                usuario=request.user,
                tipo_movimiento=(
                    HistorialTicket.TipoMovimiento.CAMBIO_PRIORIDAD
                ),
                comentario=(
                    obj.motivo_cambio_prioridad
                    or "Prioridad modificada."
                ),
                prioridad_anterior=prioridad_anterior,
                prioridad_nueva=obj.prioridad_final,
            )

        if responsable_anterior != obj.responsable_actual:
            crear_movimiento_historial(
                ticket=obj,
                usuario=request.user,
                tipo_movimiento=(
                    HistorialTicket.TipoMovimiento.CAMBIO_RESPONSABLE
                ),
                comentario=(
                    f"Responsable cambiado de "
                    f"{responsable_anterior} a "
                    f"{obj.responsable_actual}."
                ),
                responsable_anterior=responsable_anterior,
                responsable_nuevo=obj.responsable_actual,
            )


@admin.register(HistorialTicket)
class HistorialTicketAdmin(admin.ModelAdmin):
    list_display = (
        "ticket",
        "tipo_movimiento",
        "usuario",
        "fecha_creacion",
    )

    list_filter = (
        "tipo_movimiento",
    )

    search_fields = (
        "ticket__codigo",
        "comentario",
        "usuario__username",
    )

    readonly_fields = (
        "id",
        "fecha_creacion",
        "fecha_modificacion",
    )

    autocomplete_fields = (
        "ticket",
        "usuario",
    )
