from django.db.models import Q

from operacion.selectors import obtener_tickets_visibles_para_usuario
from usuarios.models import Usuario

from .models import ArticuloConocimiento


def obtener_articulos_visibles_para_usuario(usuario):
    if not usuario or not usuario.is_authenticated:
        return ArticuloConocimiento.objects.none()
    if not usuario.activo_operativamente:
        return ArticuloConocimiento.objects.none()
    if usuario.rol in (Usuario.Rol.ADMINISTRADOR, Usuario.Rol.SUPERVISOR):
        return ArticuloConocimiento.objects.all()
    tickets_visibles = obtener_tickets_visibles_para_usuario(usuario)
    return ArticuloConocimiento.objects.filter(
        Q(tickets_relacionados__in=tickets_visibles)
        | Q(estado=ArticuloConocimiento.Estado.PUBLICADO)
    ).distinct()
