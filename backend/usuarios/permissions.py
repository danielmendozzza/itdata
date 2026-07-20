from rest_framework.permissions import BasePermission

from .models import Usuario


class PuedeAdministrarUsuarios(BasePermission):
    message = "No tenés permisos para administrar usuarios."

    def has_permission(self, request, view):
        usuario = request.user
        return bool(
            usuario
            and usuario.is_authenticated
            and usuario.activo_operativamente
            and usuario.rol
            in (Usuario.Rol.ADMINISTRADOR, Usuario.Rol.SUPERVISOR)
        )

    def has_object_permission(self, request, view, usuario_objetivo):
        if request.user.rol == Usuario.Rol.ADMINISTRADOR:
            return True
        return usuario_objetivo.rol not in (
            Usuario.Rol.ADMINISTRADOR,
            Usuario.Rol.SUPERVISOR,
        )
