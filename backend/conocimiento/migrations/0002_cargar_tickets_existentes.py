import uuid

from django.db import migrations


def cargar_tickets_existentes(apps, schema_editor):
    Ticket = apps.get_model("operacion", "Ticket")
    Articulo = apps.get_model("conocimiento", "ArticuloConocimiento")
    Comentario = apps.get_model("operacion", "ComentarioTicket")

    for ticket in Ticket.objects.select_related("activo__tipo_activo").iterator():
        if Articulo.objects.filter(tickets_relacionados=ticket).exists():
            continue
        diagnostico = "\n\n".join(
            comentario.texto
            for comentario in Comentario.objects.filter(
                ticket=ticket, tipo="DIAGNOSTICO"
            ).order_by("fecha_creacion")
        )
        acciones = "\n\n".join(
            comentario.texto
            for comentario in Comentario.objects.filter(
                ticket=ticket, tipo="ACCION_REALIZADA"
            ).order_by("fecha_creacion")
        )
        articulo = Articulo.objects.create(
            codigo=f"KB-{uuid.uuid4().hex[:10].upper()}",
            titulo=ticket.titulo,
            resumen=ticket.descripcion,
            sintomas=ticket.descripcion,
            diagnostico=diagnostico,
            procedimiento_solucion=(ticket.solucion or "").strip() or acciones,
            categoria_id=ticket.categoria_id,
            subcategoria_id=ticket.subcategoria_id,
            tipo_activo_id=(ticket.activo.tipo_activo_id if ticket.activo_id else None),
            autor_id=ticket.creado_por_id,
        )
        articulo.tickets_relacionados.add(ticket)


class Migration(migrations.Migration):
    dependencies = [
        ("operacion", "0003_resuelto_como_estado_final"),
        ("conocimiento", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(cargar_tickets_existentes, migrations.RunPython.noop),
    ]
