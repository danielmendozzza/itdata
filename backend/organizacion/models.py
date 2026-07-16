import uuid

from django.db import models


class Sucursal(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    codigo = models.CharField(
        max_length=20,
        unique=True,
    )

    nombre = models.CharField(
        max_length=150,
    )

    direccion = models.CharField(
        max_length=250,
        blank=True,
    )

    telefono = models.CharField(
        max_length=30,
        blank=True,
    )

    encargado = models.CharField(
        max_length=150,
        blank=True,
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
        verbose_name = "Sucursal"
        verbose_name_plural = "Sucursales"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"