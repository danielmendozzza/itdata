from pathlib import Path

from django.db import transaction
from django.utils import timezone

from usuarios.models import Usuario


ROLES_CON_ACCESO_TOTAL_SUCURSALES = (
    Usuario.Rol.ADMINISTRADOR,
    Usuario.Rol.SUPERVISOR,
    Usuario.Rol.TECNICO,
)


def usuario_puede_generar_ticket_para_sucursal(usuario, sucursal):
    """
    Determina si un usuario puede generar un ticket
    asociado a una sucursal determinada.
    """

    if not usuario or not usuario.is_authenticated:
        return False

    if not usuario.activo_operativamente:
        return False

    if usuario.rol in ROLES_CON_ACCESO_TOTAL_SUCURSALES:
        return True

    if usuario.rol == Usuario.Rol.JDISTRITO:
        return usuario.sucursales_asignadas.filter(
            pk=sucursal.pk
        ).exists()

    if usuario.rol == Usuario.Rol.SUCURSAL:
        return usuario.sucursal_id == sucursal.pk

    return False


def crear_movimiento_historial(
    ticket,
    usuario,
    tipo_movimiento,
    comentario="",
    estado_anterior=None,
    estado_nuevo=None,
    prioridad_anterior=None,
    prioridad_nueva=None,
    responsable_anterior=None,
    responsable_nuevo=None,
):
    """
    Crea un registro en `HistorialTicket` centralizando la lógica para
    Admin y API.
    """
    from .models import HistorialTicket

    HistorialTicket.objects.create(
        ticket=ticket,
        usuario=usuario,
        tipo_movimiento=tipo_movimiento,
        comentario=comentario or "",
        estado_anterior=estado_anterior or "",
        estado_nuevo=estado_nuevo or "",
        prioridad_anterior=prioridad_anterior or "",
        prioridad_nueva=prioridad_nueva or "",
        responsable_anterior=responsable_anterior or "",
        responsable_nuevo=responsable_nuevo or "",
    )


class TransicionTicketError(Exception):
    pass


ESTADOS_TERMINALES = (
    "RESUELTO",
    "CERRADO",
    "CANCELADO",
)


@transaction.atomic
def asignar_ticket(ticket, tecnico, usuario):
    from .models import HistorialTicket, Ticket

    ticket = Ticket.objects.select_for_update().get(pk=ticket.pk)
    if ticket.estado in ESTADOS_TERMINALES:
        raise TransicionTicketError(
            "No se puede asignar un ticket resuelto, cerrado o cancelado."
        )

    estado_anterior = ticket.estado
    tecnico_anterior = ticket.tecnico_asignado
    ticket.tecnico_asignado = tecnico
    if ticket.estado == Ticket.Estado.NUEVO:
        ticket.estado = Ticket.Estado.ASIGNADO
    ticket.save(
        update_fields=("tecnico_asignado", "estado", "fecha_modificacion")
    )
    crear_movimiento_historial(
        ticket=ticket,
        usuario=usuario,
        tipo_movimiento=HistorialTicket.TipoMovimiento.ASIGNACION,
        comentario=(
            f"Ticket asignado a {tecnico}."
            if tecnico_anterior is None
            else f"Ticket reasignado de {tecnico_anterior} a {tecnico}."
        ),
        estado_anterior=estado_anterior,
        estado_nuevo=ticket.estado,
    )
    return ticket


@transaction.atomic
def tomar_ticket(ticket, usuario):
    from .models import HistorialTicket, Ticket

    ticket = Ticket.objects.select_for_update().get(pk=ticket.pk)
    if ticket.estado in ESTADOS_TERMINALES:
        raise TransicionTicketError(
            "No se puede tomar un ticket resuelto, cerrado o cancelado."
        )
    if ticket.tecnico_asignado_id not in (None, usuario.pk):
        raise TransicionTicketError("El ticket está asignado a otro técnico.")

    estado_anterior = ticket.estado
    ticket.tecnico_asignado = usuario
    ticket.tomado_por = usuario
    ticket.fecha_toma = timezone.now()
    ticket.estado = Ticket.Estado.EN_PROCESO
    ticket.save(
        update_fields=(
            "tecnico_asignado",
            "tomado_por",
            "fecha_toma",
            "estado",
            "fecha_modificacion",
        )
    )
    crear_movimiento_historial(
        ticket=ticket,
        usuario=usuario,
        tipo_movimiento=HistorialTicket.TipoMovimiento.CAMBIO_ESTADO,
        comentario=f"Ticket tomado por {usuario}.",
        estado_anterior=estado_anterior,
        estado_nuevo=ticket.estado,
    )
    return ticket


@transaction.atomic
def resolver_ticket(ticket, usuario, solucion):
    from .models import HistorialTicket, Ticket

    ticket = Ticket.objects.select_for_update().get(pk=ticket.pk)
    if ticket.estado in ESTADOS_TERMINALES:
        raise TransicionTicketError(
            "El ticket ya está resuelto, cerrado o cancelado."
        )

    estado_anterior = ticket.estado
    ticket.estado = Ticket.Estado.RESUELTO
    ticket.solucion = solucion
    ticket.resuelto_por = usuario
    ticket.fecha_resolucion = timezone.now()
    ticket.save(
        update_fields=(
            "estado",
            "solucion",
            "resuelto_por",
            "fecha_resolucion",
            "fecha_modificacion",
        )
    )
    crear_movimiento_historial(
        ticket=ticket,
        usuario=usuario,
        tipo_movimiento=HistorialTicket.TipoMovimiento.RESOLUCION,
        comentario=solucion,
        estado_anterior=estado_anterior,
        estado_nuevo=ticket.estado,
    )
    return ticket


@transaction.atomic
def cerrar_ticket(ticket, usuario, comentario=""):
    from .models import HistorialTicket, Ticket

    ticket = Ticket.objects.select_for_update().get(pk=ticket.pk)
    if ticket.estado != Ticket.Estado.RESUELTO:
        raise TransicionTicketError(
            "Solo se puede cerrar un ticket que esté resuelto."
        )

    estado_anterior = ticket.estado
    ticket.estado = Ticket.Estado.CERRADO
    ticket.cerrado_por = usuario
    ticket.fecha_cierre = timezone.now()
    ticket.save(
        update_fields=(
            "estado",
            "cerrado_por",
            "fecha_cierre",
            "fecha_modificacion",
        )
    )
    crear_movimiento_historial(
        ticket=ticket,
        usuario=usuario,
        tipo_movimiento=HistorialTicket.TipoMovimiento.CIERRE,
        comentario=comentario or "Ticket cerrado.",
        estado_anterior=estado_anterior,
        estado_nuevo=ticket.estado,
    )
    return ticket


@transaction.atomic
def agregar_comentario_ticket(ticket, usuario, tipo, texto):
    from .models import ComentarioTicket, HistorialTicket

    comentario = ComentarioTicket.objects.create(
        ticket=ticket,
        autor=usuario,
        tipo=tipo,
        texto=texto,
    )
    crear_movimiento_historial(
        ticket=ticket,
        usuario=usuario,
        tipo_movimiento=HistorialTicket.TipoMovimiento.COMENTARIO,
        comentario=f"{comentario.get_tipo_display()}: {texto}",
    )
    return comentario


@transaction.atomic
def agregar_adjunto_ticket(ticket, usuario, archivo, descripcion=""):
    from .models import AdjuntoTicket, HistorialTicket

    adjunto = AdjuntoTicket(
        ticket=ticket,
        subido_por=usuario,
        archivo=archivo,
        nombre_original=Path(archivo.name).name,
        descripcion=descripcion,
    )
    adjunto.full_clean()
    adjunto.save()
    crear_movimiento_historial(
        ticket=ticket,
        usuario=usuario,
        tipo_movimiento=HistorialTicket.TipoMovimiento.ADJUNTO,
        comentario=f"Archivo adjunto agregado: {adjunto.nombre_original}.",
    )
    return adjunto

