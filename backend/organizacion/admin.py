from django.contrib import admin

from .models import Sucursal


@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "nombre",
        "encargado",
        "telefono",
        "activo",
        "fecha_creacion",
    )

    list_filter = (
        "activo",
    )

    search_fields = (
        "codigo",
        "nombre",
        "encargado",
    )

    readonly_fields = (
        "id",
        "fecha_creacion",
        "fecha_modificacion",
    )

    ordering = (
        "nombre",
    )