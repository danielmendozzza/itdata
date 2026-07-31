from rest_framework import serializers

from .models import Sucursal


class SucursalListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sucursal
        fields = [
            "id",
            "codigo",
            "nombre",
            "direccion",
            "telefono",
            "encargado",
            "activo",
        ]


class SucursalDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sucursal
        fields = [
            "id",
            "codigo",
            "nombre",
            "direccion",
            "telefono",
            "encargado",
            "activo",
            "fecha_creacion",
            "fecha_modificacion",
        ]


class SucursalCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sucursal
        fields = [
            "codigo",
            "nombre",
            "direccion",
            "telefono",
            "encargado",
            "activo",
        ]

    def validate_codigo(self, value):
        codigo = value.strip().upper()

        if Sucursal.objects.filter(codigo__iexact=codigo).exists():
            raise serializers.ValidationError(
                "Ya existe una sucursal con este código."
            )

        return codigo


class SucursalUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sucursal
        fields = [
            "codigo",
            "nombre",
            "direccion",
            "telefono",
            "encargado",
            "activo",
        ]

    def validate_codigo(self, value):
        codigo = value.strip().upper()

        existe = Sucursal.objects.filter(
            codigo__iexact=codigo
        ).exclude(
            pk=self.instance.pk
        ).exists()

        if existe:
            raise serializers.ValidationError(
                "Ya existe otra sucursal con este código."
            )

        return codigo
