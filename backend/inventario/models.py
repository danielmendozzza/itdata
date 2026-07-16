import uuid

from django.db import models

from organizacion.models import Sucursal


class Criticidad(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    nombre = models.CharField(
        max_length=50,
        unique=True,
    )

    nivel = models.PositiveSmallIntegerField(
        unique=True,
    )

    descripcion = models.CharField(
        max_length=250,
        blank=True,
    )

    activo = models.BooleanField(
        default=True,
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "Criticidad"
        verbose_name_plural = "Criticidades"
        ordering = ["-nivel"]

    def __str__(self):
        return f"{self.nombre} - Nivel {self.nivel}"


class TipoActivo(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    nombre = models.CharField(
        max_length=100,
        unique=True,
    )

    descripcion = models.CharField(
        max_length=250,
        blank=True,
    )

    activo = models.BooleanField(
        default=True,
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "Tipo de activo"
        verbose_name_plural = "Tipos de activo"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Activo(models.Model):

    class Estado(models.TextChoices):
        OPERATIVO = "OPERATIVO", "Operativo"
        EN_REPARACION = "EN_REPARACION", "En reparación"
        FUERA_SERVICIO = "FUERA_SERVICIO", "Fuera de servicio"
        BAJA = "BAJA", "Baja"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    codigo = models.CharField(
        max_length=30,
        unique=True,
    )

    nombre = models.CharField(
        max_length=150,
    )

    tipo_activo = models.ForeignKey(
        TipoActivo,
        on_delete=models.PROTECT,
        related_name="activos",
    )

    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.PROTECT,
        related_name="activos",
        null=True,
        blank=True,
    )

    criticidad = models.ForeignKey(
        Criticidad,
        on_delete=models.PROTECT,
        related_name="activos",
    )

    marca = models.CharField(
        max_length=100,
        blank=True,
    )

    modelo = models.CharField(
        max_length=100,
        blank=True,
    )

    numero_serie = models.CharField(
        max_length=100,
        blank=True,
    )

    direccion_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
    )

    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.OPERATIVO,
    )

    activo = models.BooleanField(
        default=True,
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
    )

    fecha_modificacion = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        verbose_name = "Activo"
        verbose_name_plural = "Activos"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"