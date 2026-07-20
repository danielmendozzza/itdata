from rest_framework.permissions import SAFE_METHODS, BasePermission

from usuarios.models import Usuario


class SucursalPermission(BasePermission):
    """Protege el maestro de sucursales según el rol funcional."""

    message = "No tenés permisos para modificar sucursales."

    def has_permission(self, request, view):
        usuario = request.user
        if not usuario or not usuario.is_authenticated:
            return False
        if not usuario.activo_operativamente:
            return False
        if request.method in SAFE_METHODS:
            return True
        return usuario.rol == Usuario.Rol.ADMINISTRADOR

    def has_object_permission(self, request, view, obj):
        if request.method not in SAFE_METHODS:
            return request.user.rol == Usuario.Rol.ADMINISTRADOR

        usuario = request.user
        if usuario.rol == Usuario.Rol.JDISTRITO:
            return usuario.sucursales_asignadas.filter(pk=obj.pk).exists()
        if usuario.rol == Usuario.Rol.SUCURSAL:
            return usuario.sucursal_id == obj.pk
        return True
