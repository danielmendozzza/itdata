from django.contrib import admin

from .models import ArticuloConocimiento


@admin.register(ArticuloConocimiento)
class ArticuloConocimientoAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "titulo",
        "categoria",
        "estado",
        "version",
        "autor",
        "revisado_por",
        "fecha_modificacion",
    )
    list_filter = ("estado", "categoria", "tipo_activo")
    search_fields = (
        "codigo",
        "titulo",
        "resumen",
        "diagnostico",
        "procedimiento_solucion",
        "palabras_clave",
        "tickets_relacionados__codigo",
    )
    autocomplete_fields = (
        "categoria",
        "subcategoria",
        "tipo_activo",
        "tickets_relacionados",
        "autor",
        "revisado_por",
    )
    filter_horizontal = ("tickets_relacionados",)
    readonly_fields = (
        "id",
        "codigo",
        "autor",
        "revisado_por",
        "fecha_publicacion",
        "version",
        "fecha_creacion",
        "fecha_modificacion",
    )
