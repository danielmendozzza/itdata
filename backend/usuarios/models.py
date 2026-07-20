import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):

    class Rol(models.TextChoices):
        ADMINISTRADOR = "ADMINISTRADOR", "Administrador"
        SUPERVISOR = "SUPERVISOR", "Supervisor"
        TECNICO = "TECNICO", "Técnico"
        JDISTRITO = "JDISTRITO", "Jefe de Distrito"
        SUCURSAL = "SUCURSAL", "Sucursal"
        CONSULTOR = "CONSULTOR", "Consultor"

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

    sucursal = models.ForeignKey(
        "organizacion.Sucursal",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="usuarios",
        help_text="Sucursal propia del usuario con rol Sucursal.",
    )

    sucursales_asignadas = models.ManyToManyField(
        "organizacion.Sucursal",
        blank=True,
        related_name="jefes_distrito",
        help_text=(
            "Sucursales que puede gestionar un usuario con rol "
            "Jefe de Distrito."
        ),
    )

    def __str__(self):
        return self.username

    @property
    def es_admin(self):
        return self.rol == self.Rol.ADMINISTRADOR

    @property
    def es_supervisor(self):
        return self.rol == self.Rol.SUPERVISOR

    @property
    def es_tecnico(self):
        return self.rol == self.Rol.TECNICO

    @property
    def es_jdistrito(self):
        return self.rol == self.Rol.JDISTRITO

    @property
    def es_sucursal(self):
        return self.rol == self.Rol.SUCURSAL

    @property
    def es_consultor(self):
        return self.rol == self.Rol.CONSULTOR
