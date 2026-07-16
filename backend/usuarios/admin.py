from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = (
        "username",
        "first_name",
        "last_name",
        "email",
        "rol",
        "activo_operativamente",
        "is_staff",
    )

    list_filter = (
        "rol",
        "activo_operativamente",
        "is_staff",
        "is_active",
    )

    search_fields = (
        "username",
        "first_name",
        "last_name",
        "email",
    )

    fieldsets = UserAdmin.fieldsets + (
        (
            "Información de ITDATA",
            {
                "fields": (
                    "rol",
                    "telefono",
                    "activo_operativamente",
                    "fecha_creacion",
                )
            },
        ),
    )

    readonly_fields = (
        "fecha_creacion",
        "last_login",
        "date_joined",
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Información de ITDATA",
            {
                "fields": (
                    "rol",
                    "telefono",
                    "activo_operativamente",
                )
            },
        ),
    )