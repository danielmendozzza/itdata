from rest_framework.permissions import BasePermission

from organizacion.models import Sucursal
from .services import usuario_puede_generar_ticket_para_sucursal
from usuarios.models import Usuario


class PuedeVerReportes(BasePermission):
    message = "No tenés permisos para consultar reportes y dashboard."

    def has_permission(self, request, view):
        usuario = request.user
        return bool(
            usuario
            and usuario.is_authenticated
            and usuario.activo_operativamente
            and usuario.rol
            in (
                Usuario.Rol.ADMINISTRADOR,
                Usuario.Rol.SUPERVISOR,
                Usuario.Rol.CONSULTOR,
            )
        )


class PuedeAdministrarCatalogos(BasePermission):
    message = "Solo Administradores y Supervisores pueden modificar categorías."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return request.user.activo_operativamente
        return request.user.activo_operativamente and (
            request.user.es_admin or request.user.es_supervisor
        )


class PuedeCrearTicket(BasePermission):
    message = "No tenés permisos para crear un ticket en esa sucursal."

    def has_permission(self, request, view):
        # Allow non-POST methods to pass through (other permissions may apply)
        if request.method != "POST":
            return True

        sucursal_id = request.data.get("sucursal")

        if not sucursal_id:
            return False

        try:
            sucursal = Sucursal.objects.get(pk=sucursal_id)
        except Exception:
            return False

        return usuario_puede_generar_ticket_para_sucursal(
            request.user, sucursal
        )


class TicketPermission(BasePermission):
    """Permission class that enforces role-based rules for Tickets.

    Rules implemented:
    - Administrador y Supervisor: pueden hacer todo.
    - Tecnico: puede crear tickets para cualquier sucursal; puede modificar
      tickets que le estén asignados o que haya creado.
    - Jefe de Distrito: puede crear/editar tickets en sus sucursales.
    - Sucursal: puede crear/editar tickets solo en su sucursal.
    - Consultor: solo lectura.
    """

    def has_permission(self, request, view):
        # All authenticated users can list/retrieve; creation is validated
        # by `usuario_puede_generar_ticket_para_sucursal` below.
        if not request.user or not request.user.is_authenticated:
            return False

        if view.action == "create":
            sucursal_id = request.data.get("sucursal")
            if not sucursal_id:
                return False
            try:
                sucursal = Sucursal.objects.get(pk=sucursal_id)
            except Exception:
                return False

            return usuario_puede_generar_ticket_para_sucursal(
                request.user, sucursal
            )

        # For other non-object actions, allow and rely on object permissions
        return True

    def has_object_permission(self, request, view, obj):
        # SAFE methods: visible tickets are handled by queryset filtering
        from .selectors import obtener_tickets_visibles_para_usuario

        if request.method in ("GET", "HEAD", "OPTIONS"):
            visible = obtener_tickets_visibles_para_usuario(request.user)
            return visible.filter(pk=obj.pk).exists()

        action = getattr(view, "action", None)

        if action == "asignar":
            return request.user.es_admin or request.user.es_supervisor

        if action == "cambiar_estado":
            if request.user.es_admin or request.user.es_supervisor:
                return True
            return (
                request.user.es_tecnico
                and obj.tecnico_asignado_id == request.user.id
            )

        if action == "tomar":
            return request.user.es_tecnico and (
                obj.tecnico_asignado_id in (None, request.user.id)
            )

        if action == "resolver":
            if request.user.es_admin or request.user.es_supervisor:
                return True
            return request.user.es_tecnico and request.user.id in (
                obj.tecnico_asignado_id,
                obj.tomado_por_id,
            )

        # Admins and supervisors can do everything
        if request.user.es_admin or request.user.es_supervisor:
            return True

        # Consultor: read-only
        if request.user.es_consultor:
            return False

        # Tecnico: can modify if assigned or creator
        if request.user.es_tecnico:
            if obj.tecnico_asignado_id == request.user.id:
                return True
            if obj.creado_por_id == request.user.id:
                return True

        # Jefe de distrito: can act on tickets in assigned sucursales
        if request.user.es_jdistrito:
            return obj.sucursal_id in list(request.user.sucursales_asignadas.values_list("pk", flat=True))

        # Sucursal: can act on tickets of their own sucursal
        if request.user.es_sucursal:
            return obj.sucursal_id == request.user.sucursal_id

        # Default deny
        return False
