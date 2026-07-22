from django.db import migrations, models


def convertir_cerrados_a_resueltos(apps, schema_editor):
    Ticket = apps.get_model("operacion", "Ticket")
    Ticket.objects.filter(estado="CERRADO").update(estado="RESUELTO")


class Migration(migrations.Migration):
    dependencies = [("operacion", "0002_alter_historialticket_tipo_movimiento_adjuntoticket_and_more")]

    operations = [
        migrations.RunPython(convertir_cerrados_a_resueltos, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="ticket",
            name="estado",
            field=models.CharField(
                choices=[
                    ("NUEVO", "Nuevo"),
                    ("ASIGNADO", "Asignado"),
                    ("EN_PROCESO", "En proceso"),
                    ("ESPERANDO_USUARIO", "Esperando usuario"),
                    ("ESPERANDO_PROVEEDOR", "Esperando proveedor"),
                    ("ESPERANDO_OTRA_AREA", "Esperando otra área"),
                    ("EN_PRUEBAS", "En pruebas"),
                    ("RESUELTO", "Resuelto"),
                    ("CANCELADO", "Cancelado"),
                ],
                default="NUEVO",
                max_length=30,
            ),
        ),
    ]
