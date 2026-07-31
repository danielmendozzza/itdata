from rest_framework.permissions import SAFE_METHODS, BasePermission

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


class PuedeAdministrarTiposActivo(BasePermission):
    message = "Solo los Administradores pueden modificar tipos de activo."

    def has_permission(self, request, view):
        usuario = request.user
        if not (
            usuario
            and usuario.is_authenticated
            and usuario.is_active
            and usuario.activo_operativamente
        ):
            return False
        if request.method in SAFE_METHODS:
            return usuario.rol in (
                Usuario.Rol.ADMINISTRADOR,
                Usuario.Rol.SUPERVISOR,
            )
        return usuario.rol == Usuario.Rol.ADMINISTRADOR
