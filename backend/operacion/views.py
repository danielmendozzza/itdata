from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Avg, Count, DurationField, ExpressionWrapper, F
from django.db.models.functions import TruncDate
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from usuarios.models import Usuario

from .models import Categoria, Subcategoria, Ticket
from . import selectors
from .serializers import (
	TicketListSerializer,
	TicketDetailSerializer,
	TicketCreateSerializer,
	TicketUpdateSerializer,
	AsignarTicketSerializer,
	AdjuntoTicketSerializer,
	AperturaCreateSerializer,
	CambiarEstadoAperturaSerializer,
	CambiarEstadoTicketSerializer,
	ComentarioTicketSerializer,
	DashboardGeneralResponseSerializer,
	DashboardPersonalResponseSerializer,
	ReporteTicketsResponseSerializer,
	ResolverTicketSerializer,
	CategoriaSerializer,
	SubcategoriaSerializer,
)
from .filters import TicketFilter
from .permissions import (
	PuedeAdministrarCatalogos,
	PuedeGestionarAperturas,
	PuedeVerReportes,
	TicketPermission,
)
from .services import (
	TransicionTicketError,
	agregar_adjunto_ticket,
	agregar_comentario_ticket,
	asignar_ticket,
	cambiar_estado_apertura,
	cambiar_estado_ticket,
	crear_movimiento_historial,
	resolver_ticket,
	tomar_ticket,
)
from .models import HistorialTicket
from .models import AdjuntoTicket


class CategoriaViewSet(viewsets.ModelViewSet):
	serializer_class = CategoriaSerializer
	permission_classes = (PuedeAdministrarCatalogos,)
	pagination_class = None
	search_fields = ("nombre", "descripcion")
	ordering = ("nombre",)

	def get_queryset(self):
		queryset = Categoria.objects.all()
		if self.request.query_params.get("todos") != "true":
			queryset = queryset.filter(activo=True)
		return queryset

	def destroy(self, request, *args, **kwargs):
		categoria = self.get_object()
		categoria.activo = False
		categoria.save(update_fields=("activo", "fecha_modificacion"))
		return Response(status=204)


class SubcategoriaViewSet(viewsets.ModelViewSet):
	serializer_class = SubcategoriaSerializer
	permission_classes = (PuedeAdministrarCatalogos,)
	pagination_class = None
	filterset_fields = ("categoria",)
	search_fields = ("nombre", "descripcion")
	ordering = ("categoria__nombre", "nombre")

	def get_queryset(self):
		queryset = Subcategoria.objects.select_related("categoria")
		if self.request.query_params.get("todos") != "true":
			queryset = queryset.filter(activo=True, categoria__activo=True)
		return queryset

	def destroy(self, request, *args, **kwargs):
		subcategoria = self.get_object()
		subcategoria.activo = False
		subcategoria.save(update_fields=("activo", "fecha_modificacion"))
		return Response(status=204)


class TicketViewSet(viewsets.ModelViewSet):
	queryset = Ticket.objects.all()
	permission_classes = (IsAuthenticated, TicketPermission)
	filterset_class = TicketFilter
	search_fields = (
		"codigo",
		"titulo",
		"descripcion",
		"sucursal__nombre",
		"activo__nombre",
		"activo__codigo",
	)
	ordering_fields = ("numero", "fecha_creacion")

	def get_queryset(self):
		return selectors.obtener_tickets_visibles_para_usuario(self.request.user)

	def get_serializer_class(self):
		if self.action == "list":
			return TicketListSerializer
		if self.action == "retrieve":
			return TicketDetailSerializer
		if self.action == "create":
			return TicketCreateSerializer
		if self.action in ("update", "partial_update"):
			return TicketUpdateSerializer
		if self.action == "asignar":
			return AsignarTicketSerializer
		if self.action == "resolver":
			return ResolverTicketSerializer
		if self.action == "cambiar_estado":
			return CambiarEstadoTicketSerializer

		return TicketDetailSerializer

	# Creation permission is handled inside TicketPermission.has_permission

	def perform_create(self, serializer):
		ticket = serializer.save()
		crear_movimiento_historial(
			ticket=ticket,
			usuario=self.request.user,
			tipo_movimiento=HistorialTicket.TipoMovimiento.CREACION,
			comentario="Ticket creado.",
			estado_nuevo=ticket.estado,
			prioridad_nueva=ticket.prioridad_final,
			responsable_nuevo=ticket.responsable_actual,
		)
		from conocimiento.services import crear_borrador_desde_ticket
		crear_borrador_desde_ticket(ticket, self.request.user, exigir_permiso=False)

	def perform_update(self, serializer):
		# Capture previous values
		instancia = self.get_object()
		estado_anterior = instancia.estado
		prioridad_anterior = instancia.prioridad_final
		responsable_anterior = instancia.responsable_actual

		ticket = serializer.save()

		if estado_anterior != ticket.estado:
			crear_movimiento_historial(
				ticket=ticket,
				usuario=self.request.user,
				tipo_movimiento=HistorialTicket.TipoMovimiento.CAMBIO_ESTADO,
				comentario=(
					f"Estado cambiado de {estado_anterior} a {ticket.estado}."
				),
				estado_anterior=estado_anterior,
				estado_nuevo=ticket.estado,
			)

		if prioridad_anterior != ticket.prioridad_final:
			crear_movimiento_historial(
				ticket=ticket,
				usuario=self.request.user,
				tipo_movimiento=HistorialTicket.TipoMovimiento.CAMBIO_PRIORIDAD,
				comentario=(ticket.motivo_cambio_prioridad or "Prioridad modificada."),
				prioridad_anterior=prioridad_anterior,
				prioridad_nueva=ticket.prioridad_final,
			)

		if responsable_anterior != ticket.responsable_actual:
			crear_movimiento_historial(
				ticket=ticket,
				usuario=self.request.user,
				tipo_movimiento=HistorialTicket.TipoMovimiento.CAMBIO_RESPONSABLE,
				comentario=(
					f"Responsable cambiado de {responsable_anterior} a {ticket.responsable_actual}."
				),
				responsable_anterior=responsable_anterior,
				responsable_nuevo=ticket.responsable_actual,
			)

	def _ejecutar_transicion(self, operacion, **kwargs):
		try:
			ticket = operacion(
				ticket=self.get_object(), usuario=self.request.user, **kwargs
			)
		except TransicionTicketError as error:
			raise ValidationError({"detail": str(error)}) from error
		return Response(TicketDetailSerializer(ticket).data)

	@extend_schema(
		request=AsignarTicketSerializer,
		responses=TicketDetailSerializer,
	)
	@action(detail=True, methods=("post",))
	def asignar(self, request, pk=None):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		return self._ejecutar_transicion(
			asignar_ticket, tecnico=serializer.validated_data["tecnico"]
		)

	@extend_schema(request=None, responses=TicketDetailSerializer)
	@action(detail=True, methods=("post",))
	def tomar(self, request, pk=None):
		return self._ejecutar_transicion(tomar_ticket)

	@extend_schema(
		request=ResolverTicketSerializer,
		responses=TicketDetailSerializer,
	)
	@action(detail=True, methods=("post",))
	def resolver(self, request, pk=None):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		return self._ejecutar_transicion(
			resolver_ticket, solucion=serializer.validated_data["solucion"]
		)

	@extend_schema(
		request=CambiarEstadoTicketSerializer,
		responses=TicketDetailSerializer,
	)
	@action(detail=True, methods=("post",), url_path="cambiar-estado")
	def cambiar_estado(self, request, pk=None):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		return self._ejecutar_transicion(
			cambiar_estado_ticket,
			estado=serializer.validated_data["estado"],
			comentario=serializer.validated_data.get("comentario", ""),
		)

	@extend_schema(
		request=ComentarioTicketSerializer,
		responses=ComentarioTicketSerializer(many=True),
	)
	@action(detail=True, methods=("get", "post"))
	def comentarios(self, request, pk=None):
		ticket = self.get_object()
		if request.method == "GET":
			return Response(
				ComentarioTicketSerializer(ticket.comentarios.all(), many=True).data
			)

		serializer = ComentarioTicketSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		comentario = agregar_comentario_ticket(
			ticket=ticket,
			usuario=request.user,
			tipo=serializer.validated_data["tipo"],
			texto=serializer.validated_data["texto"],
		)
		return Response(ComentarioTicketSerializer(comentario).data, status=201)

	@extend_schema(
		request=AdjuntoTicketSerializer,
		responses=AdjuntoTicketSerializer(many=True),
	)
	@action(
		detail=True,
		methods=("get", "post"),
		parser_classes=(MultiPartParser, FormParser),
	)
	def adjuntos(self, request, pk=None):
		ticket = self.get_object()
		if request.method == "GET":
			return Response(
				AdjuntoTicketSerializer(
					ticket.adjuntos.all(), many=True, context={"request": request}
				).data
			)

		serializer = AdjuntoTicketSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		adjunto = agregar_adjunto_ticket(
			ticket=ticket,
			usuario=request.user,
			archivo=serializer.validated_data["archivo"],
			descripcion=serializer.validated_data.get("descripcion", ""),
		)
		return Response(
			AdjuntoTicketSerializer(adjunto, context={"request": request}).data,
			status=201,
		)

	@extend_schema(
		parameters=[
			OpenApiParameter(
				"adjunto_id", OpenApiTypes.UUID, OpenApiParameter.PATH
			)
		],
		request=None,
		responses={204: None},
	)
	@action(
		detail=True,
		methods=("delete",),
		url_path=r"adjuntos/(?P<adjunto_id>[^/.]+)",
		url_name="eliminar-adjunto",
	)
	def eliminar_adjunto(self, request, pk=None, adjunto_id=None):
		ticket = self.get_object()
		try:
			adjunto = ticket.adjuntos.get(pk=adjunto_id)
		except AdjuntoTicket.DoesNotExist as error:
			raise ValidationError({"detail": "El adjunto no existe."}) from error
		if not (
			request.user.es_admin
			or request.user.es_supervisor
			or adjunto.subido_por_id == request.user.pk
		):
			raise PermissionDenied(
				"Solo quien subió el archivo puede eliminarlo."
			)
		archivo = adjunto.archivo
		crear_movimiento_historial(
			ticket=ticket,
			usuario=request.user,
			tipo_movimiento=HistorialTicket.TipoMovimiento.ADJUNTO,
			comentario=f"Archivo adjunto eliminado: {adjunto.nombre_original}.",
		)
		adjunto.delete()
		archivo.delete(save=False)
		return Response(status=204)


class AperturaViewSet(viewsets.ModelViewSet):
	queryset = Ticket.objects.filter(tipo=Ticket.Tipo.APERTURA)
	permission_classes = (PuedeGestionarAperturas,)
	http_method_names = ("get", "post", "head", "options")
	search_fields = ("codigo", "titulo")
	filterset_fields = ("estado",)
	ordering_fields = ("numero", "fecha_creacion")
	ordering = ("-numero",)

	def get_queryset(self):
		return (
			Ticket.objects.filter(tipo=Ticket.Tipo.APERTURA)
			.select_related("creado_por", "resuelto_por")
			.prefetch_related("historial", "comentarios")
		)

	def get_serializer_class(self):
		if self.action == "create":
			return AperturaCreateSerializer
		if self.action == "cambiar_estado":
			return CambiarEstadoAperturaSerializer
		if self.action == "comentarios":
			return ComentarioTicketSerializer
		if self.action == "list":
			return TicketListSerializer
		return TicketDetailSerializer

	def perform_create(self, serializer):
		apertura = serializer.save()
		crear_movimiento_historial(
			ticket=apertura,
			usuario=self.request.user,
			tipo_movimiento=HistorialTicket.TipoMovimiento.CREACION,
			comentario="Apertura creada.",
			estado_nuevo=apertura.estado,
		)

	def _detalle(self, apertura):
		return Response(TicketDetailSerializer(apertura).data)

	@action(detail=True, methods=("post",), url_path="cambiar-estado")
	def cambiar_estado(self, request, pk=None):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		try:
			apertura = cambiar_estado_apertura(
				self.get_object(),
				serializer.validated_data["estado"],
				request.user,
				serializer.validated_data.get("comentario", ""),
			)
		except TransicionTicketError as error:
			raise ValidationError({"detail": str(error)}) from error
		return self._detalle(apertura)

	@action(detail=True, methods=("get", "post"))
	def comentarios(self, request, pk=None):
		apertura = self.get_object()
		if request.method == "GET":
			return Response(
				ComentarioTicketSerializer(apertura.comentarios.all(), many=True).data
			)
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		comentario = agregar_comentario_ticket(
			ticket=apertura,
			usuario=request.user,
			tipo=serializer.validated_data["tipo"],
			texto=serializer.validated_data["texto"],
		)
		return Response(ComentarioTicketSerializer(comentario).data, status=201)


def _queryset_filtrado(request):
	queryset = selectors.obtener_tickets_visibles_para_usuario(request.user)
	filtro = TicketFilter(request.query_params, queryset=queryset)
	if not filtro.is_valid():
		return None, filtro.errors
	return filtro.qs, None


def _conteos(queryset, campo, etiqueta=None):
	etiqueta = etiqueta or campo
	return list(
		queryset.values(etiqueta)
		.annotate(total=Count("id"))
		.order_by("-total", etiqueta)
	)


class ReporteTicketsView(APIView):
	permission_classes = (IsAuthenticated, PuedeVerReportes)

	@extend_schema(
		parameters=[
			OpenApiParameter("fecha_desde", str, description="Fecha inicial YYYY-MM-DD"),
			OpenApiParameter("fecha_hasta", str, description="Fecha final YYYY-MM-DD"),
			OpenApiParameter("estado", str),
			OpenApiParameter("prioridad_final", str),
			OpenApiParameter("responsable_actual", str),
			OpenApiParameter("origen", str),
			OpenApiParameter("categoria", str, description="UUID"),
			OpenApiParameter("sucursal", str, description="UUID"),
			OpenApiParameter("tecnico_asignado", str, description="UUID"),
		],
		responses=ReporteTicketsResponseSerializer,
	)
	def get(self, request):
		queryset, errores = _queryset_filtrado(request)
		if errores:
			return Response(errores, status=400)

		duracion = ExpressionWrapper(
			F("fecha_resolucion") - F("fecha_creacion"),
			output_field=DurationField(),
		)
		promedio = queryset.filter(fecha_resolucion__isnull=False).aggregate(
			valor=Avg(duracion)
		)["valor"]

		return Response(
			{
				"total": queryset.count(),
				"por_estado": _conteos(queryset, "estado"),
				"por_prioridad": _conteos(queryset, "prioridad_final"),
				"por_responsable": _conteos(queryset, "responsable_actual"),
				"por_sucursal": _conteos(queryset, "sucursal__nombre"),
				"por_categoria": _conteos(queryset, "categoria__nombre"),
				"por_tecnico": _conteos(queryset, "tecnico_asignado__username"),
				"tiempo_promedio_resolucion_segundos": (
					promedio.total_seconds() if promedio else None
				),
			}
		)


class DashboardGeneralView(APIView):
	permission_classes = (IsAuthenticated, PuedeVerReportes)

	@extend_schema(
		parameters=[
			OpenApiParameter("fecha_desde", str, description="Fecha inicial YYYY-MM-DD"),
			OpenApiParameter("fecha_hasta", str, description="Fecha final YYYY-MM-DD"),
			OpenApiParameter("estado", str),
			OpenApiParameter("sucursal", str, description="UUID"),
		],
		responses=DashboardGeneralResponseSerializer,
	)
	def get(self, request):
		queryset, errores = _queryset_filtrado(request)
		if errores:
			return Response(errores, status=400)

		cerrados = (Ticket.Estado.RESUELTO, Ticket.Estado.CANCELADO)
		creados = list(
			queryset.annotate(fecha=TruncDate("fecha_creacion"))
			.values("fecha")
			.annotate(creados=Count("id"))
			.order_by("fecha")
		)
		resueltos = list(
			queryset.filter(fecha_resolucion__isnull=False)
			.annotate(fecha=TruncDate("fecha_resolucion"))
			.values("fecha")
			.annotate(resueltos=Count("id"))
			.order_by("fecha")
		)
		evolucion_por_fecha = {
			item["fecha"]: {
				"fecha": item["fecha"],
				"creados": item["creados"],
				"resueltos": 0,
			}
			for item in creados
		}
		for item in resueltos:
			evolucion_por_fecha.setdefault(
				item["fecha"],
				{"fecha": item["fecha"], "creados": 0, "resueltos": 0},
			)["resueltos"] = item["resueltos"]

		duracion = ExpressionWrapper(
			F("fecha_resolucion") - F("fecha_creacion"),
			output_field=DurationField(),
		)
		promedio = queryset.filter(fecha_resolucion__isnull=False).aggregate(
			valor=Avg(duracion)
		)["valor"]
		abiertos = queryset.exclude(estado__in=cerrados)
		aperturas = Ticket.objects.filter(tipo=Ticket.Tipo.APERTURA)
		estados_terceros = (
			Ticket.Estado.ESPERANDO_PROVEEDOR,
			Ticket.Estado.ESPERANDO_OTRA_AREA,
			Ticket.Estado.ESPERANDO_USUARIO,
		)
		return Response(
			{
				"tickets_total": queryset.count(),
				"tickets_abiertos": abiertos.count(),
				"tickets_en_proceso": queryset.filter(
					estado=Ticket.Estado.EN_PROCESO
				).count(),
				"tickets_resueltos": queryset.filter(
					estado=Ticket.Estado.RESUELTO
				).count(),
				"tickets_criticos_abiertos": abiertos.filter(
					prioridad_final=Ticket.Prioridad.CRITICA
				).count(),
				"esperando_terceros": abiertos.filter(
					estado__in=estados_terceros
				).count(),
				"aperturas_pendientes": aperturas.exclude(
					estado=Ticket.Estado.REALIZADO
				).count(),
				"aperturas_concretadas": aperturas.filter(
					estado=Ticket.Estado.REALIZADO
				).count(),
				"tiempo_promedio_resolucion_segundos": (
					promedio.total_seconds() if promedio else None
				),
				"por_estado": _conteos(queryset, "estado"),
				"evolucion_diaria": [
					evolucion_por_fecha[fecha]
					for fecha in sorted(evolucion_por_fecha)
				],
			}
		)


class DashboardPersonalView(APIView):
	permission_classes = (IsAuthenticated,)

	@extend_schema(responses=DashboardPersonalResponseSerializer)
	def get(self, request):
		if not request.user.activo_operativamente:
			return Response({"detail": "Usuario inactivo."}, status=403)
		queryset = selectors.obtener_tickets_propios_para_dashboard(request.user)
		finalizados = (Ticket.Estado.RESUELTO,)
		no_activos = finalizados + (Ticket.Estado.CANCELADO,)
		puede_ver_aperturas = request.user.rol in (
			Usuario.Rol.ADMINISTRADOR,
			Usuario.Rol.SUPERVISOR,
			Usuario.Rol.TECNICO,
		)
		aperturas = (
			Ticket.objects.filter(tipo=Ticket.Tipo.APERTURA)
			if puede_ver_aperturas
			else Ticket.objects.none()
		)
		return Response(
			{
				"tickets_activos": queryset.exclude(estado__in=no_activos).count(),
				"tickets_resueltos": queryset.filter(estado__in=finalizados).count(),
				"aperturas_pendientes": aperturas.exclude(
					estado=Ticket.Estado.REALIZADO
				).count(),
				"aperturas_concretadas": aperturas.filter(
					estado=Ticket.Estado.REALIZADO
				).count(),
				"por_estado": _conteos(queryset, "estado"),
			}
		)
