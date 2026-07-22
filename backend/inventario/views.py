from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Activo, Criticidad, TipoActivo
from .permissions import PuedeAdministrarActivos
from .serializers import ActivoCatalogoSerializer, ActivoSerializer, CriticidadSerializer, TipoActivoSerializer
from usuarios.models import Usuario


class CriticidadViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CriticidadSerializer
    permission_classes = (PuedeAdministrarActivos,)
    pagination_class = None

    def get_queryset(self):
        return Criticidad.objects.filter(activo=True)


class TipoActivoViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TipoActivoSerializer
    permission_classes = (PuedeAdministrarActivos,)
    pagination_class = None

    def get_queryset(self):
        return TipoActivo.objects.filter(activo=True)


class ActivoViewSet(viewsets.ModelViewSet):
    serializer_class = ActivoSerializer
    permission_classes = (PuedeAdministrarActivos,)
    search_fields = ("codigo", "nombre", "marca", "modelo", "numero_serie", "direccion_ip")
    filterset_fields = ("estado", "activo", "sucursal", "tipo_activo", "criticidad")
    ordering_fields = ("codigo", "nombre", "fecha_creacion", "fecha_modificacion")
    ordering = ("nombre",)

    def get_queryset(self):
        return Activo.objects.select_related("tipo_activo", "sucursal", "criticidad")

    def destroy(self, request, *args, **kwargs):
        activo = self.get_object()
        activo.activo = False
        activo.save(update_fields=("activo", "fecha_modificacion"))
        return Response(status=204)


class ActivoCatalogoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Activo.objects.none()
    serializer_class = ActivoCatalogoSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = None
    filterset_fields = ("sucursal",)
    search_fields = ("codigo", "nombre", "marca", "modelo", "numero_serie")

    def get_queryset(self):
        usuario = self.request.user
        queryset = Activo.objects.filter(activo=True).select_related("sucursal")
        if usuario.rol == Usuario.Rol.SUCURSAL:
            return queryset.filter(sucursal_id=usuario.sucursal_id)
        if usuario.rol == Usuario.Rol.JDISTRITO:
            return queryset.filter(sucursal__in=usuario.sucursales_asignadas.all())
        return queryset
