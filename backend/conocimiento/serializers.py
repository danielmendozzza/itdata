from rest_framework import serializers

from .models import ArticuloConocimiento


class ArticuloListSerializer(serializers.ModelSerializer):
    categoria = serializers.StringRelatedField()
    autor = serializers.StringRelatedField()

    class Meta:
        model = ArticuloConocimiento
        fields = (
            "id",
            "codigo",
            "titulo",
            "resumen",
            "categoria",
            "estado",
            "version",
            "autor",
            "fecha_modificacion",
            "fecha_publicacion",
        )


class ArticuloDetailSerializer(serializers.ModelSerializer):
    autor = serializers.StringRelatedField(read_only=True)
    revisado_por = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = ArticuloConocimiento
        fields = "__all__"
        read_only_fields = (
            "id",
            "codigo",
            "autor",
            "revisado_por",
            "estado",
            "fecha_publicacion",
            "version",
            "fecha_creacion",
            "fecha_modificacion",
            "tickets_relacionados",
        )

    def validate(self, attrs):
        categoria = attrs.get("categoria", getattr(self.instance, "categoria", None))
        subcategoria = attrs.get(
            "subcategoria", getattr(self.instance, "subcategoria", None)
        )
        if subcategoria and subcategoria.categoria_id != categoria.pk:
            raise serializers.ValidationError(
                {"subcategoria": "La subcategoría no pertenece a la categoría."}
            )
        return attrs


class CrearArticuloDesdeTicketSerializer(serializers.Serializer):
    ticket = serializers.UUIDField()


class MensajeEditorialSerializer(serializers.Serializer):
    detalle = serializers.CharField(read_only=True)
