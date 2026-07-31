from rest_framework import serializers

from .models import Activo, Criticidad, TipoActivo


class CriticidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Criticidad
        fields = ("id", "nombre", "nivel")


class TipoActivoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoActivo
        fields = ("id", "nombre", "descripcion", "activo")

    def validate_nombre(self, value):
        nombre = value.strip()
        queryset = TipoActivo.objects.filter(nombre__iexact=nombre)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError(
                "Ya existe un tipo de activo con este nombre."
            )
        return nombre


class ActivoSerializer(serializers.ModelSerializer):
    tipo_activo_nombre = serializers.CharField(
        source="tipo_activo.nombre", read_only=True
    )
    sucursal_nombre = serializers.CharField(
        source="sucursal.nombre", read_only=True, allow_null=True
    )
    criticidad_nombre = serializers.CharField(
        source="criticidad.nombre", read_only=True
    )

    class Meta:
        model = Activo
        fields = (
            "id",
            "codigo",
            "nombre",
            "tipo_activo",
            "tipo_activo_nombre",
            "sucursal",
            "sucursal_nombre",
            "criticidad",
            "criticidad_nombre",
            "marca",
            "modelo",
            "numero_serie",
            "direccion_ip",
            "estado",
            "activo",
            "fecha_creacion",
            "fecha_modificacion",
        )
        read_only_fields = ("id", "fecha_creacion", "fecha_modificacion")

    def validate_codigo(self, value):
        codigo = value.strip().upper()
        queryset = Activo.objects.filter(codigo__iexact=codigo)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("Ya existe un activo con este código.")
        return codigo


class ActivoCatalogoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Activo
        fields = ("id", "codigo", "nombre", "sucursal", "estado")
