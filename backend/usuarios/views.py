from rest_framework import status, viewsets
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Usuario
from .permissions import PuedeAdministrarUsuarios
from .serializers import (
    TecnicoListSerializer,
    UsuarioActualSerializer,
    UsuarioAdminListSerializer,
    UsuarioAdminWriteSerializer,
)


class UsuarioActualView(RetrieveAPIView):
    serializer_class = UsuarioActualSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user


class TecnicoListView(ListAPIView):
    serializer_class = TecnicoListSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = None

    def get_queryset(self):
        return Usuario.objects.filter(
            rol=Usuario.Rol.TECNICO,
            is_active=True,
            activo_operativamente=True,
        ).order_by("first_name", "last_name", "username")


class UsuarioAdminViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    permission_classes = (IsAuthenticated, PuedeAdministrarUsuarios)
    filterset_fields = ("rol", "is_active", "activo_operativamente", "sucursal")
    search_fields = ("username", "first_name", "last_name", "email")
    ordering_fields = ("username", "first_name", "last_name", "rol")
    ordering = ("first_name", "last_name", "username")

    def get_queryset(self):
        queryset = Usuario.objects.select_related("sucursal").prefetch_related(
            "sucursales_asignadas"
        )
        if self.request.user.rol == Usuario.Rol.SUPERVISOR:
            queryset = queryset.exclude(
                rol__in=(Usuario.Rol.ADMINISTRADOR, Usuario.Rol.SUPERVISOR)
            )
        return queryset

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return UsuarioAdminListSerializer
        return UsuarioAdminWriteSerializer

    def destroy(self, request, *args, **kwargs):
        usuario = self.get_object()
        if usuario.pk == request.user.pk:
            return Response(
                {"detail": "No podés desactivar tu propio usuario."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        usuario.is_active = False
        usuario.activo_operativamente = False
        usuario.save(update_fields=("is_active", "activo_operativamente"))
        return Response(status=status.HTTP_204_NO_CONTENT)
