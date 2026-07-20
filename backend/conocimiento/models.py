import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from core.models import ModeloBase


class ArticuloConocimiento(ModeloBase):
    class Estado(models.TextChoices):
        BORRADOR = "BORRADOR", "Borrador"
        EN_REVISION = "EN_REVISION", "En revisión"
        PUBLICADO = "PUBLICADO", "Publicado"
        ARCHIVADO = "ARCHIVADO", "Archivado"

    codigo = models.CharField(max_length=20, unique=True, editable=False)
    titulo = models.CharField(max_length=180)
    resumen = models.TextField()
    sintomas = models.TextField(blank=True)
    diagnostico = models.TextField(blank=True)
    causa = models.TextField(blank=True)
    procedimiento_solucion = models.TextField(blank=True)
    palabras_clave = models.CharField(
        max_length=250,
        blank=True,
        help_text="Palabras separadas por coma para facilitar la búsqueda.",
    )
    categoria = models.ForeignKey(
        "operacion.Categoria",
        on_delete=models.PROTECT,
        related_name="articulos_conocimiento",
    )
    subcategoria = models.ForeignKey(
        "operacion.Subcategoria",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="articulos_conocimiento",
    )
    tipo_activo = models.ForeignKey(
        "inventario.TipoActivo",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="articulos_conocimiento",
    )
    tickets_relacionados = models.ManyToManyField(
        "operacion.Ticket",
        blank=True,
        related_name="articulos_conocimiento",
    )
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="articulos_conocimiento_creados",
    )
    revisado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="articulos_conocimiento_revisados",
    )
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.BORRADOR,
    )
    fecha_publicacion = models.DateTimeField(null=True, blank=True)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "Artículo de conocimiento"
        verbose_name_plural = "Artículos de conocimiento"
        ordering = ("-fecha_modificacion",)

    def __str__(self):
        return f"{self.codigo} - {self.titulo}"

    def clean(self):
        errores = {}
        if self.subcategoria and self.subcategoria.categoria_id != self.categoria_id:
            errores["subcategoria"] = (
                "La subcategoría no pertenece a la categoría seleccionada."
            )
        if self.estado == self.Estado.PUBLICADO and not self.procedimiento_solucion.strip():
            errores["procedimiento_solucion"] = (
                "Un artículo publicado debe incluir un procedimiento de solución."
            )
        if errores:
            raise ValidationError(errores)

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = f"KB-{uuid.uuid4().hex[:10].upper()}"
        self.full_clean(exclude=("tickets_relacionados",))
        super().save(*args, **kwargs)
