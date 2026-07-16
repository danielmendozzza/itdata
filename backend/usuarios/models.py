import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):

    class Rol(models.TextChoices):
        ADMINISTRADOR = "ADMINISTRADOR", "Administrador"
        SUPERVISOR = "SUPERVISOR", "Supervisor"
        TECNICO = "TECNICO", "Técnico"
        SUCURSAL = "SUCURSAL", "Sucursal"
        GERENCIA = "GERENCIA", "Gerencia"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    rol = models.CharField(
        max_length=20,
        choices=Rol.choices,
        default=Rol.SUCURSAL,
    )

    telefono = models.CharField(
        max_length=30,
        blank=True,
    )

    activo_operativamente = models.BooleanField(
        default=True,
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return self.username

# Create your models here.
