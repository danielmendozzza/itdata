import django_filters

from .models import Ticket


class TicketFilter(django_filters.FilterSet):
    fecha_desde = django_filters.DateFilter(
        field_name="fecha_creacion", lookup_expr="date__gte"
    )
    fecha_hasta = django_filters.DateFilter(
        field_name="fecha_creacion", lookup_expr="date__lte"
    )

    class Meta:
        model = Ticket
        fields = (
            "estado",
            "prioridad_final",
            "responsable_actual",
            "origen",
            "categoria",
            "sucursal",
            "tecnico_asignado",
        )
