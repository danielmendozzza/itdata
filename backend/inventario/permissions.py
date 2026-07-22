from rest_framework.permissions import BasePermission

from usuarios.models import Usuario


class PuedeAdministrarActivos(BasePermission):
    message = "Solo Administradores y Supervisores pueden administrar activos."

    def has_permission(self, request, view):
        usuario = request.user
        return bool(
            usuario
            and usuario.is_authenticated
            and usuario.is_active
            and usuario.activo_operativamente
            and usuario.rol
            in (Usuario.Rol.ADMINISTRADOR, Usuario.Rol.SUPERVISOR)
        )
