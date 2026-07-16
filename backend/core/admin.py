from django.contrib import admin

from .models import NumeradorDocumento


@admin.register(NumeradorDocumento)
class NumeradorDocumentoAdmin(admin.ModelAdmin):
    list_display = (
        "clave",
        "nombre",
        "prefijo",
        "ultimo_numero",
        "longitud",
        "activo",
    )

    list_filter = (
        "activo",
    )

    search_fields = (
        "clave",
        "nombre",
        "prefijo",
    )

    readonly_fields = (
        "id",
        "fecha_creacion",
        "fecha_modificacion",
    )

    ordering = (
        "nombre",
    )