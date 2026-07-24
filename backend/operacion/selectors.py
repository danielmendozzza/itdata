from organizacion.models import Sucursal
from usuarios.models import Usuario
from django.db.models import Q


def obtener_sucursales_disponibles_para_usuario(usuario):
    """
    Devuelve las sucursales que el usuario puede seleccionar
    al momento de crear un ticket.
    """

    queryset = Sucursal.objects.filter(activo=True)

    if not usuario or not usuario.is_authenticated:
        return queryset.none()

    if not usuario.activo_operativamente:
        return queryset.none()

    if usuario.rol in (
        Usuario.Rol.ADMINISTRADOR,
        Usuario.Rol.SUPERVISOR,
        Usuario.Rol.TECNICO,
    ):
        return queryset

    if usuario.rol == Usuario.Rol.JDISTRITO:
        return queryset.filter(
            pk__in=usuario.sucursales_asignadas.values("pk")
        )

    if usuario.rol == Usuario.Rol.SUCURSAL:
        return queryset.filter(
            pk=usuario.sucursal_id
        )

    return queryset.none()


def obtener_tickets_visibles_para_usuario(usuario):
    """
    Devuelve un queryset de `Ticket` que el usuario puede ver.
    """
    from .models import Ticket
    base = Ticket.objects.filter(tipo=Ticket.Tipo.INCIDENCIA)

    if not usuario or not usuario.is_authenticated:
        return base.none()

    if not usuario.activo_operativamente:
        return base.none()

    if usuario.rol in (
        Usuario.Rol.ADMINISTRADOR,
        Usuario.Rol.SUPERVISOR,
        Usuario.Rol.TECNICO,
    ):
        return base

    if usuario.rol == Usuario.Rol.JDISTRITO:
        return base.filter(
            sucursal__in=usuario.sucursales_asignadas.all()
        )

    if usuario.rol == Usuario.Rol.SUCURSAL:
        return base.filter(sucursal_id=usuario.sucursal_id)

    if usuario.rol == Usuario.Rol.CONSULTOR:
        return base

    return base.none()


def obtener_tickets_propios_para_dashboard(usuario):
    queryset = obtener_tickets_visibles_para_usuario(usuario)
    if not usuario or not usuario.is_authenticated:
        return queryset.none()
    if usuario.rol == Usuario.Rol.TECNICO:
        return queryset.filter(
            Q(tecnico_asignado=usuario) | Q(tomado_por=usuario)
        ).distinct()
    return queryset
