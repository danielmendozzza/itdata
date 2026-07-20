from django.db.models import Q

from usuarios.models import Usuario

from .models import ArticuloConocimiento


def obtener_articulos_visibles_para_usuario(usuario):
    if not usuario or not usuario.is_authenticated:
        return ArticuloConocimiento.objects.none()
    if not usuario.activo_operativamente:
        return ArticuloConocimiento.objects.none()
    if usuario.rol in (Usuario.Rol.ADMINISTRADOR, Usuario.Rol.SUPERVISOR):
        return ArticuloConocimiento.objects.all()
    if usuario.rol == Usuario.Rol.TECNICO:
        return ArticuloConocimiento.objects.filter(
            Q(estado=ArticuloConocimiento.Estado.PUBLICADO) | Q(autor=usuario)
        ).distinct()
    return ArticuloConocimiento.objects.filter(
        estado=ArticuloConocimiento.Estado.PUBLICADO
    )
