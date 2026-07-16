import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class ModeloBase(models.Model):
    """
    Modelo abstracto que contiene campos comunes
    para las entidades principales de ITDATA.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
    )

    fecha_modificacion = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        abstract = True


class NumeradorDocumento(ModeloBase):
    """
    Controla la numeración visible de los documentos de ITDATA.

    Ejemplo:
    ITD-000001
    ITD-000002
    """

    clave = models.CharField(
        max_length=30,
        unique=True,
        help_text="Identificador interno. Ejemplo: TICKET",
    )

    nombre = models.CharField(
        max_length=100,
        help_text="Nombre descriptivo. Ejemplo: Tickets",
    )

    prefijo = models.CharField(
        max_length=20,
        default="ITD",
        help_text="Texto que aparecerá antes del número.",
    )

    ultimo_numero = models.PositiveBigIntegerField(
        default=0,
    )

    longitud = models.PositiveSmallIntegerField(
        default=6,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(12),
        ],
        help_text="Cantidad de dígitos. Ejemplo: 6 genera 000001.",
    )

    activo = models.BooleanField(
        default=True,
    )

    class Meta:
        verbose_name = "Numerador de documento"
        verbose_name_plural = "Numeradores de documentos"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.prefijo})"

    def formar_codigo(self, numero):
        """
        Forma el código visible sin modificar el numerador.

        Ejemplo:
        prefijo = ITD
        numero = 25
        longitud = 6

        Resultado:
        ITD-000025
        """

        numero_formateado = str(numero).zfill(self.longitud)
        return f"{self.prefijo}-{numero_formateado}"