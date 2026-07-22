from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from operacion.selectors import obtener_tickets_visibles_para_usuario
from usuarios.models import Usuario

from . import selectors
from .models import ArticuloConocimiento
from .permissions import ArticuloConocimientoPermission
from .serializers import (
    ArticuloDetailSerializer,
    ArticuloListSerializer,
    CrearArticuloDesdeTicketSerializer,
)
from .services import (
    OperacionConocimientoError,
    archivar_articulo,
    crear_borrador_desde_ticket,
    enviar_articulo_a_revision,
    publicar_articulo,
)


class ArticuloConocimientoViewSet(viewsets.ModelViewSet):
    queryset = ArticuloConocimiento.objects.all()
    permission_classes = (IsAuthenticated, ArticuloConocimientoPermission)
    filterset_fields = ("estado", "categoria", "subcategoria", "tipo_activo", "autor")
    search_fields = (
        "titulo",
        "resumen",
        "tickets_relacionados__titulo",
        "tickets_relacionados__descripcion",
    )
    ordering_fields = ("titulo", "fecha_creacion", "fecha_modificacion", "fecha_publicacion")
    ordering = ("-fecha_modificacion",)

    def get_queryset(self):
        return selectors.obtener_articulos_visibles_para_usuario(
            self.request.user
        ).select_related("categoria", "subcategoria", "tipo_activo", "autor")

    def get_serializer_class(self):
        if self.action == "list":
            return ArticuloListSerializer
        return ArticuloDetailSerializer

    def perform_create(self, serializer):
        serializer.save(autor=self.request.user)

    def _operacion_editorial(self, operacion):
        try:
            articulo = operacion(self.get_object(), self.request.user)
        except OperacionConocimientoError as error:
            raise ValidationError({"detail": str(error)}) from error
        return Response(ArticuloDetailSerializer(articulo).data)

    @extend_schema(request=None, responses=ArticuloDetailSerializer)
    @action(detail=True, methods=("post",), url_path="enviar-a-revision")
    def enviar_revision(self, request, pk=None):
        return self._operacion_editorial(enviar_articulo_a_revision)

    @extend_schema(request=None, responses=ArticuloDetailSerializer)
    @action(detail=True, methods=("post",))
    def publicar(self, request, pk=None):
        return self._operacion_editorial(publicar_articulo)

    @extend_schema(request=None, responses=ArticuloDetailSerializer)
    @action(detail=True, methods=("post",))
    def archivar(self, request, pk=None):
        return self._operacion_editorial(archivar_articulo)


class CrearArticuloDesdeTicketView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        request=CrearArticuloDesdeTicketSerializer,
        responses={201: ArticuloDetailSerializer},
    )
    def post(self, request):
        if not request.user.activo_operativamente or request.user.rol not in (
            Usuario.Rol.ADMINISTRADOR,
            Usuario.Rol.SUPERVISOR,
            Usuario.Rol.TECNICO,
        ):
            raise PermissionDenied(
                "Tu rol no puede generar artículos de conocimiento."
            )
        serializer = CrearArticuloDesdeTicketSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ticket = get_object_or_404(
            obtener_tickets_visibles_para_usuario(request.user),
            pk=serializer.validated_data["ticket"],
        )
        try:
            articulo = crear_borrador_desde_ticket(ticket, request.user)
        except OperacionConocimientoError as error:
            raise ValidationError({"detail": str(error)}) from error
        return Response(ArticuloDetailSerializer(articulo).data, status=201)
