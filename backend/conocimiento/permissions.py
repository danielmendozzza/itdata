from rest_framework.permissions import SAFE_METHODS, BasePermission

from usuarios.models import Usuario

from .models import ArticuloConocimiento


class ArticuloConocimientoPermission(BasePermission):
    message = "No tenés permisos para realizar esta acción."

    def has_permission(self, request, view):
        usuario = request.user
        if not usuario or not usuario.is_authenticated:
            return False
        if not usuario.activo_operativamente:
            return False
        if request.method in SAFE_METHODS:
            return True
        if view.action == "create":
            return usuario.rol in (
                Usuario.Rol.ADMINISTRADOR,
                Usuario.Rol.SUPERVISOR,
                Usuario.Rol.TECNICO,
            )
        return True

    def has_object_permission(self, request, view, articulo):
        usuario = request.user
        if request.method in SAFE_METHODS:
            return (
                articulo.estado == ArticuloConocimiento.Estado.PUBLICADO
                or usuario.rol in (Usuario.Rol.ADMINISTRADOR, Usuario.Rol.SUPERVISOR)
                or articulo.autor_id == usuario.pk
            )

        if view.action in ("publicar", "archivar"):
            return usuario.rol in (
                Usuario.Rol.ADMINISTRADOR,
                Usuario.Rol.SUPERVISOR,
            )
        if view.action == "destroy":
            return (
                usuario.rol == Usuario.Rol.ADMINISTRADOR
                and articulo.estado == ArticuloConocimiento.Estado.BORRADOR
            )
        if usuario.rol in (Usuario.Rol.ADMINISTRADOR, Usuario.Rol.SUPERVISOR):
            return True
        return (
            usuario.rol == Usuario.Rol.TECNICO
            and articulo.autor_id == usuario.pk
            and articulo.estado == ArticuloConocimiento.Estado.BORRADOR
        )
