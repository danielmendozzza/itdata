from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import (
    AdjuntoTicket,
    Categoria,
    ComentarioTicket,
    HistorialTicket,
    Subcategoria,
    Ticket,
)


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ("id", "nombre", "descripcion", "activo")


class SubcategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subcategoria
        fields = ("id", "categoria", "nombre", "descripcion", "activo")


class HistorialTicketSerializer(serializers.ModelSerializer):
    usuario = serializers.StringRelatedField()

    class Meta:
        model = HistorialTicket
        fields = (
            "id",
            "fecha_creacion",
            "usuario",
            "tipo_movimiento",
            "comentario",
        )


class ComentarioTicketSerializer(serializers.ModelSerializer):
    autor = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = ComentarioTicket
        fields = ("id", "tipo", "texto", "autor", "fecha_creacion")
        read_only_fields = ("id", "autor", "fecha_creacion")


class AdjuntoTicketSerializer(serializers.ModelSerializer):
    subido_por = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = AdjuntoTicket
        fields = (
            "id",
            "archivo",
            "nombre_original",
            "descripcion",
            "subido_por",
            "fecha_creacion",
        )
        read_only_fields = (
            "id",
            "nombre_original",
            "subido_por",
            "fecha_creacion",
        )


class TicketListSerializer(serializers.ModelSerializer):
    sucursal = serializers.StringRelatedField()
    activo = serializers.StringRelatedField()
    creado_por = serializers.StringRelatedField()
    responsable_actual_nombre = serializers.SerializerMethodField()

    def get_responsable_actual_nombre(self, ticket):
        if (
            ticket.responsable_actual == Ticket.ResponsableActual.TI
            and ticket.tecnico_asignado_id
        ):
            return str(ticket.tecnico_asignado)
        return ticket.get_responsable_actual_display()

    class Meta:
        model = Ticket
        fields = (
            "id",
            "codigo",
            "titulo",
            "sucursal",
            "activo",
            "prioridad_final",
            "estado",
            "tecnico_asignado",
            "responsable_actual",
            "responsable_actual_nombre",
            "creado_por",
            "fecha_creacion",
        )


class TicketDetailSerializer(serializers.ModelSerializer):
    creado_por = serializers.StringRelatedField()
    sucursal_nombre = serializers.CharField(source="sucursal.nombre", read_only=True)
    activo_nombre = serializers.StringRelatedField(source="activo", read_only=True)
    tecnico_asignado_nombre = serializers.StringRelatedField(
        source="tecnico_asignado", read_only=True
    )
    responsable_actual_nombre = serializers.SerializerMethodField()
    historial = HistorialTicketSerializer(many=True, read_only=True)
    comentarios = ComentarioTicketSerializer(many=True, read_only=True)
    adjuntos = AdjuntoTicketSerializer(many=True, read_only=True)

    def get_responsable_actual_nombre(self, ticket):
        if (
            ticket.responsable_actual == Ticket.ResponsableActual.TI
            and ticket.tecnico_asignado_id
        ):
            return str(ticket.tecnico_asignado)
        return ticket.get_responsable_actual_display()

    class Meta:
        model = Ticket
        fields = "__all__"
        read_only_fields = (
            "id",
            "numero",
            "codigo",
            "creado_por",
            "prioridad_sugerida",
            "fecha_creacion",
            "fecha_modificacion",
        )


class TicketCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = (
            "id",
            "numero",
            "codigo",
            "titulo",
            "descripcion",
            "sucursal",
            "activo",
            "categoria",
            "subcategoria",
            "origen",
            "estado",
            "prioridad_sugerida",
            "prioridad_final",
            "fecha_creacion",
        )
        read_only_fields = (
            "id",
            "numero",
            "codigo",
            "estado",
            "prioridad_sugerida",
            "prioridad_final",
            "fecha_creacion",
        )

    def create(self, validated_data):
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            validated_data["creado_por"] = request.user

        ticket = Ticket.objects.create(**validated_data)
        return ticket

    def validate_sucursal(self, sucursal):
        from .services import usuario_puede_generar_ticket_para_sucursal

        request = self.context.get("request")
        usuario = getattr(request, "user", None)
        if not usuario_puede_generar_ticket_para_sucursal(usuario, sucursal):
            raise serializers.ValidationError(
                "No tenés permisos para crear un ticket en esa sucursal."
            )
        return sucursal


class TicketUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = (
            "titulo",
            "descripcion",
            "activo",
            "categoria",
            "subcategoria",
            "prioridad_final",
            "motivo_cambio_prioridad",
            "responsable_actual",
        )


class AsignarTicketSerializer(serializers.Serializer):
    tecnico = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.all()
    )

    def validate_tecnico(self, tecnico):
        Usuario = get_user_model()
        if tecnico.rol != Usuario.Rol.TECNICO:
            raise serializers.ValidationError(
                "El usuario seleccionado no tiene rol Técnico."
            )
        if not tecnico.is_active or not tecnico.activo_operativamente:
            raise serializers.ValidationError(
                "El técnico seleccionado no está activo."
            )
        return tecnico


class ResolverTicketSerializer(serializers.Serializer):
    solucion = serializers.CharField(allow_blank=False, trim_whitespace=True)


class CambiarEstadoTicketSerializer(serializers.Serializer):
    estado = serializers.ChoiceField(
        choices=(
            Ticket.Estado.EN_PROCESO,
            Ticket.Estado.PENDIENTE,
            Ticket.Estado.ESPERANDO_USUARIO,
            Ticket.Estado.ESPERANDO_PROVEEDOR,
            Ticket.Estado.ESPERANDO_OTRA_AREA,
            Ticket.Estado.EN_PRUEBAS,
        )
    )
    comentario = serializers.CharField(
        required=False, allow_blank=True, trim_whitespace=True
    )


class ReporteTicketsResponseSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    por_estado = serializers.ListField(child=serializers.DictField())
    por_prioridad = serializers.ListField(child=serializers.DictField())
    por_responsable = serializers.ListField(child=serializers.DictField())
    por_sucursal = serializers.ListField(child=serializers.DictField())
    por_categoria = serializers.ListField(child=serializers.DictField())
    por_tecnico = serializers.ListField(child=serializers.DictField())
    tiempo_promedio_resolucion_segundos = serializers.FloatField(
        allow_null=True
    )


class DashboardGeneralResponseSerializer(serializers.Serializer):
    tickets_total = serializers.IntegerField()
    tickets_abiertos = serializers.IntegerField()
    tickets_en_proceso = serializers.IntegerField()
    tickets_resueltos = serializers.IntegerField()
    por_estado = serializers.ListField(child=serializers.DictField())
    evolucion_diaria = serializers.ListField(child=serializers.DictField())


class DashboardPersonalResponseSerializer(serializers.Serializer):
    tickets_activos = serializers.IntegerField()
    tickets_resueltos = serializers.IntegerField()
    por_estado = serializers.ListField(child=serializers.DictField())
