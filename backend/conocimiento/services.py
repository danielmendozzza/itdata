from django.db import transaction
from django.utils import timezone

from operacion.models import ComentarioTicket, Ticket
from usuarios.models import Usuario

from .models import ArticuloConocimiento


class OperacionConocimientoError(Exception):
    pass


def usuario_puede_documentar_ticket(usuario, ticket):
    if usuario.rol in (Usuario.Rol.ADMINISTRADOR, Usuario.Rol.SUPERVISOR):
        return True
    return usuario.rol == Usuario.Rol.TECNICO and usuario.pk in (
        ticket.tecnico_asignado_id,
        ticket.tomado_por_id,
        ticket.resuelto_por_id,
    )


def _unir_comentarios(ticket, tipo):
    return "\n\n".join(
        f"[{comentario.fecha_creacion:%Y-%m-%d %H:%M}] {comentario.texto}"
        for comentario in ticket.comentarios.filter(tipo=tipo).select_related("autor")
    )


@transaction.atomic
def crear_borrador_desde_ticket(ticket, usuario):
    ticket = Ticket.objects.select_for_update().select_related(
        "categoria", "subcategoria", "activo__tipo_activo"
    ).get(pk=ticket.pk)
    if ticket.estado not in (Ticket.Estado.RESUELTO, Ticket.Estado.CERRADO):
        raise OperacionConocimientoError(
            "Solo se puede documentar conocimiento desde tickets resueltos o cerrados."
        )
    if not usuario_puede_documentar_ticket(usuario, ticket):
        raise OperacionConocimientoError(
            "No sos responsable técnico de este ticket."
        )
    if ticket.articulos_conocimiento.exists():
        raise OperacionConocimientoError(
            "El ticket ya está relacionado con un artículo de conocimiento."
        )

    diagnostico = _unir_comentarios(ticket, ComentarioTicket.Tipo.DIAGNOSTICO)
    acciones = _unir_comentarios(ticket, ComentarioTicket.Tipo.ACCION_REALIZADA)
    procedimiento = ticket.solucion.strip() or acciones
    articulo = ArticuloConocimiento.objects.create(
        titulo=ticket.titulo,
        resumen=ticket.descripcion,
        sintomas=ticket.descripcion,
        diagnostico=diagnostico,
        procedimiento_solucion=procedimiento,
        categoria=ticket.categoria,
        subcategoria=ticket.subcategoria,
        tipo_activo=(ticket.activo.tipo_activo if ticket.activo else None),
        autor=usuario,
    )
    articulo.tickets_relacionados.add(ticket)
    return articulo


@transaction.atomic
def enviar_articulo_a_revision(articulo, usuario):
    articulo = ArticuloConocimiento.objects.select_for_update().get(pk=articulo.pk)
    if articulo.estado != ArticuloConocimiento.Estado.BORRADOR:
        raise OperacionConocimientoError("Solo un borrador puede enviarse a revisión.")
    if not articulo.procedimiento_solucion.strip():
        raise OperacionConocimientoError(
            "Debe documentarse el procedimiento de solución antes de enviar a revisión."
        )
    articulo.estado = ArticuloConocimiento.Estado.EN_REVISION
    articulo.save(update_fields=("estado", "fecha_modificacion"))
    return articulo


@transaction.atomic
def publicar_articulo(articulo, usuario):
    articulo = ArticuloConocimiento.objects.select_for_update().get(pk=articulo.pk)
    if articulo.estado not in (
        ArticuloConocimiento.Estado.BORRADOR,
        ArticuloConocimiento.Estado.EN_REVISION,
    ):
        raise OperacionConocimientoError("El artículo no está disponible para publicar.")
    articulo.estado = ArticuloConocimiento.Estado.PUBLICADO
    articulo.revisado_por = usuario
    articulo.fecha_publicacion = timezone.now()
    articulo.save(
        update_fields=(
            "estado",
            "revisado_por",
            "fecha_publicacion",
            "fecha_modificacion",
        )
    )
    return articulo


@transaction.atomic
def archivar_articulo(articulo, usuario):
    articulo = ArticuloConocimiento.objects.select_for_update().get(pk=articulo.pk)
    if articulo.estado != ArticuloConocimiento.Estado.PUBLICADO:
        raise OperacionConocimientoError("Solo un artículo publicado puede archivarse.")
    articulo.estado = ArticuloConocimiento.Estado.ARCHIVADO
    articulo.revisado_por = usuario
    articulo.save(
        update_fields=("estado", "revisado_por", "fecha_modificacion")
    )
    return articulo
