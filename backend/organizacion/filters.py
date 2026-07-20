import django_filters

from .models import Sucursal


class SucursalFilter(django_filters.FilterSet):
    codigo = django_filters.CharFilter(
        field_name="codigo",
        lookup_expr="iexact"
    )

    nombre = django_filters.CharFilter(
        field_name="nombre",
        lookup_expr="icontains"
    )

    activo = django_filters.BooleanFilter(
        field_name="activo"
    )

    class Meta:
        model = Sucursal
        fields = [
            "codigo",
            "nombre",
            "activo",
        ]