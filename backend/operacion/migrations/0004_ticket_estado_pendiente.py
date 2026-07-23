from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("operacion", "0003_resuelto_como_estado_final")]

    operations = [
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
                    ("RESUELTO", "Resuelto"),
                    ("CANCELADO", "Cancelado"),
                ],
                default="NUEVO",
                max_length=30,
            ),
        ),
    ]
