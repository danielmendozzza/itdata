from pathlib import Path
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone

from core.models import ModeloBase
from core.services import obtener_siguiente_numero
from inventario.models import Activo
from organizacion.models import Sucursal


class Categoria(ModeloBase):
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

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Subcategoria(ModeloBase):
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="subcategorias",
    )

    nombre = models.CharField(
        max_length=100,
    )

    descripcion = models.CharField(
        max_length=250,
        blank=True,
    )

    activo = models.BooleanField(
        default=True,
    )

    class Meta:
        verbose_name = "Subcategoría"
        verbose_name_plural = "Subcategorías"
        ordering = ["categoria__nombre", "nombre"]

        constraints = [
            models.UniqueConstraint(
                fields=["categoria", "nombre"],
                name="operacion_subcategoria_unica_por_categoria",
            )
        ]

    def __str__(self):
        return f"{self.categoria.nombre} - {self.nombre}"


class Ticket(ModeloBase):

    class Estado(models.TextChoices):
        NUEVO = "NUEVO", "Nuevo"
        ASIGNADO = "ASIGNADO", "Asignado"
        EN_PROCESO = "EN_PROCESO", "En proceso"
        ESPERANDO_USUARIO = "ESPERANDO_USUARIO", "Esperando usuario"
        ESPERANDO_PROVEEDOR = "ESPERANDO_PROVEEDOR", "Esperando proveedor"
        ESPERANDO_OTRA_AREA = "ESPERANDO_OTRA_AREA", "Esperando otra área"
        EN_PRUEBAS = "EN_PRUEBAS", "En pruebas"
        RESUELTO = "RESUELTO", "Resuelto"
        CERRADO = "CERRADO", "Cerrado"
        CANCELADO = "CANCELADO", "Cancelado"

    class Prioridad(models.TextChoices):
        BAJA = "BAJA", "Baja"
        MEDIA = "MEDIA", "Media"
        ALTA = "ALTA", "Alta"
        CRITICA = "CRITICA", "Crítica"

    class Origen(models.TextChoices):
        PORTAL_SUCURSAL = "PORTAL_SUCURSAL", "Portal de sucursal"
        WHATSAPP = "WHATSAPP", "WhatsApp"
        LLAMADA = "LLAMADA", "Llamada"
        CORREO = "CORREO", "Correo"
        PRESENCIAL = "PRESENCIAL", "Presencial"
        TECNICO = "TECNICO", "Creado por técnico"
        MONITOREO = "MONITOREO", "Sistema de monitoreo"

    class ResponsableActual(models.TextChoices):
        TI = "TI", "Tecnología"
        SUCURSAL = "SUCURSAL", "Sucursal"
        USUARIO = "USUARIO", "Usuario"
        PROVEEDOR = "PROVEEDOR", "Proveedor"
        COMPRAS = "COMPRAS", "Compras"
        FINANZAS = "FINANZAS", "Finanzas"
        OTRA_AREA = "OTRA_AREA", "Otra área"

    numero = models.PositiveBigIntegerField(
        unique=True,
        editable=False,
    )

    codigo = models.CharField(
        max_length=30,
        unique=True,
        editable=False,
    )

    titulo = models.CharField(
        max_length=150,
    )

    descripcion = models.TextField()

    sucursal = models.ForeignKey(
        Sucursal,
        on_delete=models.PROTECT,
        related_name="tickets",
    )

    activo = models.ForeignKey(
        Activo,
        on_delete=models.PROTECT,
        related_name="tickets",
        null=True,
        blank=True,
    )

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="tickets",
    )

    subcategoria = models.ForeignKey(
        Subcategoria,
        on_delete=models.PROTECT,
        related_name="tickets",
        null=True,
        blank=True,
    )

    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="tickets_creados",
    )

    tecnico_asignado = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="tickets_asignados",
        null=True,
        blank=True,
    )

    tomado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="tickets_tomados",
        null=True,
        blank=True,
    )

    resuelto_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="tickets_resueltos",
        null=True,
        blank=True,
    )

    cerrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="tickets_cerrados",
        null=True,
        blank=True,
    )

    origen = models.CharField(
        max_length=30,
        choices=Origen.choices,
        default=Origen.PORTAL_SUCURSAL,
    )

    estado = models.CharField(
        max_length=30,
        choices=Estado.choices,
        default=Estado.NUEVO,
    )

    prioridad_sugerida = models.CharField(
        max_length=10,
        choices=Prioridad.choices,
        blank=True,
        editable=False,
    )

    prioridad_final = models.CharField(
        max_length=10,
        choices=Prioridad.choices,
        blank=True,
    )

    motivo_cambio_prioridad = models.TextField(
        blank=True,
    )

    responsable_actual = models.CharField(
        max_length=20,
        choices=ResponsableActual.choices,
        default=ResponsableActual.TI,
    )

    fecha_reporte = models.DateTimeField(
        default=timezone.now,
    )

    fecha_toma = models.DateTimeField(
        null=True,
        blank=True,
    )

    fecha_resolucion = models.DateTimeField(
        null=True,
        blank=True,
    )

    fecha_cierre = models.DateTimeField(
        null=True,
        blank=True,
    )

    solucion = models.TextField(
        blank=True,
    )

    class Meta:
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"
        ordering = ["-numero"]

    def __str__(self):
        return f"{self.codigo} - {self.titulo}"

    def clean(self):
        errores = {}

        if self.activo and self.activo.sucursal:
            if self.activo.sucursal_id != self.sucursal_id:
                errores["activo"] = (
                    "El activo seleccionado no pertenece a esta sucursal."
                )

        if self.subcategoria:
            if self.subcategoria.categoria_id != self.categoria_id:
                errores["subcategoria"] = (
                    "La subcategoría no pertenece a la categoría seleccionada."
                )

        if (
            self.prioridad_final
            and self.prioridad_sugerida
            and self.prioridad_final != self.prioridad_sugerida
            and not self.motivo_cambio_prioridad
        ):
            errores["motivo_cambio_prioridad"] = (
                "Debe indicar el motivo del cambio de prioridad."
            )

        if errores:
            raise ValidationError(errores)

    @staticmethod
    def prioridad_desde_nivel(nivel):
        if nivel >= 4:
            return Ticket.Prioridad.CRITICA

        if nivel == 3:
            return Ticket.Prioridad.ALTA

        if nivel == 2:
            return Ticket.Prioridad.MEDIA

        return Ticket.Prioridad.BAJA

    def save(self, *args, **kwargs):
        if not self.numero or not self.codigo:
            numero, codigo = obtener_siguiente_numero("TICKET")
            self.numero = numero
            self.codigo = codigo

        if self.activo and not self.prioridad_sugerida:
            self.prioridad_sugerida = self.prioridad_desde_nivel(
                self.activo.criticidad.nivel
            )

        if not self.prioridad_sugerida:
            self.prioridad_sugerida = self.Prioridad.MEDIA

        if not self.prioridad_final:
            self.prioridad_final = self.prioridad_sugerida

        self.full_clean()

        super().save(*args, **kwargs)


class HistorialTicket(ModeloBase):

    class TipoMovimiento(models.TextChoices):
        CREACION = "CREACION", "Creación"
        ASIGNACION = "ASIGNACION", "Asignación"
        CAMBIO_ESTADO = "CAMBIO_ESTADO", "Cambio de estado"
        CAMBIO_PRIORIDAD = "CAMBIO_PRIORIDAD", "Cambio de prioridad"
        CAMBIO_RESPONSABLE = "CAMBIO_RESPONSABLE", "Cambio de responsable"
        COMENTARIO = "COMENTARIO", "Comentario"
        ADJUNTO = "ADJUNTO", "Archivo adjunto"
        RESOLUCION = "RESOLUCION", "Resolución"
        CIERRE = "CIERRE", "Cierre"

    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name="historial",
    )

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="movimientos_tickets",
    )

    tipo_movimiento = models.CharField(
        max_length=30,
        choices=TipoMovimiento.choices,
    )

    comentario = models.TextField()

    estado_anterior = models.CharField(
        max_length=30,
        blank=True,
    )

    estado_nuevo = models.CharField(
        max_length=30,
        blank=True,
    )

    prioridad_anterior = models.CharField(
        max_length=10,
        blank=True,
    )

    prioridad_nueva = models.CharField(
        max_length=10,
        blank=True,
    )

    responsable_anterior = models.CharField(
        max_length=20,
        blank=True,
    )

    responsable_nuevo = models.CharField(
        max_length=20,
        blank=True,
    )

    class Meta:
        verbose_name = "Historial de ticket"
        verbose_name_plural = "Historial de tickets"
        ordering = ["fecha_creacion"]

    def __str__(self):
        return (
            f"{self.ticket.codigo} - "
            f"{self.get_tipo_movimiento_display()}"
        )


class ComentarioTicket(ModeloBase):
    class Tipo(models.TextChoices):
        NOTA = "NOTA", "Nota"
        DIAGNOSTICO = "DIAGNOSTICO", "Diagnóstico"
        ACCION_REALIZADA = "ACCION_REALIZADA", "Acción realizada"
        RESPUESTA_USUARIO = "RESPUESTA_USUARIO", "Respuesta del usuario"

    ticket = models.ForeignKey(
        Ticket, on_delete=models.CASCADE, related_name="comentarios"
    )
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="comentarios_tickets",
    )
    tipo = models.CharField(max_length=30, choices=Tipo.choices, default=Tipo.NOTA)
    texto = models.TextField()

    class Meta:
        verbose_name = "Comentario de ticket"
        verbose_name_plural = "Comentarios de tickets"
        ordering = ("fecha_creacion",)

    def __str__(self):
        return f"{self.ticket.codigo} - {self.get_tipo_display()}"


def validar_tamano_adjunto(archivo):
    limite = 10 * 1024 * 1024
    if archivo.size > limite:
        raise ValidationError("El archivo no puede superar los 10 MB.")


def ruta_adjunto_ticket(instancia, nombre_archivo):
    nombre_seguro = Path(nombre_archivo).name
    return (
        f"tickets/{instancia.ticket_id}/adjuntos/"
        f"{uuid.uuid4().hex}_{nombre_seguro}"
    )


class AdjuntoTicket(ModeloBase):
    EXTENSIONES_PERMITIDAS = (
        "pdf",
        "png",
        "jpg",
        "jpeg",
        "txt",
        "log",
        "csv",
        "docx",
        "xlsx",
    )

    ticket = models.ForeignKey(
        Ticket, on_delete=models.CASCADE, related_name="adjuntos"
    )
    subido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="adjuntos_tickets",
    )
    archivo = models.FileField(
        upload_to=ruta_adjunto_ticket,
        validators=(
            FileExtensionValidator(allowed_extensions=EXTENSIONES_PERMITIDAS),
            validar_tamano_adjunto,
        ),
    )
    nombre_original = models.CharField(max_length=255)
    descripcion = models.CharField(max_length=250, blank=True)

    class Meta:
        verbose_name = "Adjunto de ticket"
        verbose_name_plural = "Adjuntos de tickets"
        ordering = ("fecha_creacion",)

    def __str__(self):
        return f"{self.ticket.codigo} - {self.nombre_original}"
