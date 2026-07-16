from django.contrib import admin

from .models import Activo, Criticidad, TipoActivo


@admin.register(Criticidad)
class CriticidadAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "nivel",
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

    ordering = (
        "-nivel",
    )


@admin.register(TipoActivo)
class TipoActivoAdmin(admin.ModelAdmin):
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


@admin.register(Activo)
class ActivoAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "nombre",
        "tipo_activo",
        "sucursal",
        "criticidad",
        "estado",
        "activo",
    )

    list_filter = (
        "tipo_activo",
        "criticidad",
        "estado",
        "activo",
    )

    search_fields = (
        "codigo",
        "nombre",
        "marca",
        "modelo",
        "numero_serie",
        "direccion_ip",
    )

    readonly_fields = (
        "id",
        "fecha_creacion",
        "fecha_modificacion",
    )

    autocomplete_fields = (
        "sucursal",
        "tipo_activo",
        "criticidad",
    )