from rest_framework.viewsets import ModelViewSet

from .filters import SucursalFilter
from .models import Sucursal
from .permissions import SucursalPermission
from .selectors import obtener_sucursales_visibles_para_usuario
from .serializers import (
    SucursalCreateSerializer,
    SucursalDetailSerializer,
    SucursalListSerializer,
    SucursalUpdateSerializer,
)


class SucursalViewSet(ModelViewSet):
    queryset = Sucursal.objects.all()
    permission_classes = [SucursalPermission]

    filterset_class = SucursalFilter

    search_fields = [
        "codigo",
        "nombre",
        "direccion",
        "telefono",
        "encargado",
    ]

    ordering_fields = [
        "codigo",
        "nombre",
        "fecha_creacion",
        "fecha_modificacion",
    ]

    ordering = ["nombre"]

    def get_serializer_class(self):
        if self.action == "list":
            return SucursalListSerializer

        if self.action == "retrieve":
            return SucursalDetailSerializer

        if self.action == "create":
            return SucursalCreateSerializer

        if self.action in ["update", "partial_update"]:
            return SucursalUpdateSerializer

        return SucursalDetailSerializer

    def get_queryset(self):
        return obtener_sucursales_visibles_para_usuario(self.request.user)
