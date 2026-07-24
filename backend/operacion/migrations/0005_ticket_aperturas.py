from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("operacion", "0004_ticket_estado_pendiente")]

    operations = [
        migrations.AddField(
            model_name="ticket",
            name="tipo",
            field=models.CharField(
                choices=[("INCIDENCIA", "Incidencia"), ("APERTURA", "Apertura")],
                default="INCIDENCIA",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="ticket",
            name="descripcion",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="ticket",
            name="sucursal",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="tickets",
                to="organizacion.sucursal",
            ),
        ),
        migrations.AlterField(
            model_name="ticket",
            name="categoria",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="tickets",
                to="operacion.categoria",
            ),
        ),
        migrations.AlterField(
            model_name="ticket",
            name="estado",
            field=models.CharField(
                choices=[
                    ("NUEVO", "Nuevo"),
                    ("ASIGNADO", "Asignado"),
                    ("EN_PROCESO", "En proceso"),
                    ("PENDIENTE", "Pendiente"),
                    ("ESPERANDO_USUARIO", "Esperando usuario"),
                    ("ESPERANDO_PROVEEDOR", "Esperando proveedor"),
                    ("ESPERANDO_OTRA_AREA", "Esperando otra área"),
                    ("EN_PRUEBAS", "En pruebas"),
                    ("REALIZADO", "Realizado"),
                    ("RESUELTO", "Resuelto"),
                    ("CANCELADO", "Cancelado"),
                ],
                default="NUEVO",
                max_length=30,
            ),
        ),
    ]
