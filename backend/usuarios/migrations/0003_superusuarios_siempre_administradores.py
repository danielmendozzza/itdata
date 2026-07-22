from django.db import migrations, models


def corregir_superusuarios(apps, schema_editor):
    Usuario = apps.get_model("usuarios", "Usuario")
    Usuario.objects.filter(is_superuser=True).update(
        rol="ADMINISTRADOR",
        sucursal=None,
    )


class Migration(migrations.Migration):
    dependencies = [("usuarios", "0002_usuario_sucursal_usuario_sucursales_asignadas_and_more")]

    operations = [
        migrations.RunPython(corregir_superusuarios, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="usuario",
            name="rol",
            field=models.CharField(
                choices=[
                    ("ADMINISTRADOR", "Administrador"),
                    ("SUPERVISOR", "Supervisor"),
                    ("TECNICO", "Técnico"),
                    ("JDISTRITO", "Jefe de Distrito"),
                    ("SUCURSAL", "Sucursal"),
                    ("CONSULTOR", "Consultor"),
                ],
                default="CONSULTOR",
                max_length=20,
            ),
        ),
    ]
