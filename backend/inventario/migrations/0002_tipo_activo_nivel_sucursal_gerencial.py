from django.db import migrations


def agregar_tipo_activo(apps, schema_editor):
    TipoActivo = apps.get_model("inventario", "TipoActivo")
    tipo, _ = TipoActivo.objects.get_or_create(
        nombre="Nivel Sucursal-Gerencial",
        defaults={"activo": True},
    )
    if not tipo.activo:
        tipo.activo = True
        tipo.save(update_fields=("activo", "fecha_modificacion"))


def quitar_tipo_activo(apps, schema_editor):
    TipoActivo = apps.get_model("inventario", "TipoActivo")
    TipoActivo.objects.filter(nombre="Nivel Sucursal-Gerencial").delete()


class Migration(migrations.Migration):
    dependencies = [("inventario", "0001_initial")]

    operations = [
        migrations.RunPython(agregar_tipo_activo, quitar_tipo_activo),
    ]
