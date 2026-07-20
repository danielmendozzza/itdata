from django.test import TestCase

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from django.test import override_settings
from rest_framework.test import APIClient
from datetime import timedelta
import tempfile

from core.models import NumeradorDocumento
from organizacion.models import Sucursal
from operacion.models import Ticket, HistorialTicket, Categoria
from operacion.services import crear_movimiento_historial


class ServiciosHistorialTests(TestCase):
	def setUp(self):
		NumeradorDocumento.objects.create(
			clave="TICKET", nombre="Tickets", prefijo="ITD"
		)
		User = get_user_model()
		self.user = User.objects.create_user(username="u1", password="p")
		self.sucursal = Sucursal.objects.create(nombre="S1", codigo="S1", activo=True)
		self.categoria = Categoria.objects.create(nombre="Cat1", activo=True)

	def test_crear_movimiento_historial_crea_registro(self):
		ticket = Ticket.objects.create(
			titulo="T1",
			descripcion="D",
			sucursal=self.sucursal,
			categoria=self.categoria,
			creado_por=self.user,
		)

		crear_movimiento_historial(
			ticket=ticket,
			usuario=self.user,
			tipo_movimiento=HistorialTicket.TipoMovimiento.CREACION,
			comentario="Prueba",
			estado_nuevo=ticket.estado,
		)

		movimientos = HistorialTicket.objects.filter(ticket=ticket)
		self.assertEqual(movimientos.count(), 1)
		mov = movimientos.first()
		self.assertEqual(mov.comentario, "Prueba")


class PermisosTicketsTests(TestCase):
	def setUp(self):
		NumeradorDocumento.objects.create(
			clave="TICKET", nombre="Tickets", prefijo="ITD"
		)
		User = get_user_model()
		self.admin = User.objects.create_user(username="admin", password="p", rol=User.Rol.ADMINISTRADOR)
		self.tecnico = User.objects.create_user(username="tec", password="p", rol=User.Rol.TECNICO)
		self.sucursal_user = User.objects.create_user(username="suc", password="p", rol=User.Rol.SUCURSAL)

		self.s1 = Sucursal.objects.create(nombre="S1", codigo="S1", activo=True)
		self.s2 = Sucursal.objects.create(nombre="S2", codigo="S2", activo=True)
		self.categoria = Categoria.objects.create(nombre="Cat1", activo=True)

		# assign sucursal to sucursal_user
		self.sucursal_user.sucursal = self.s1
		self.sucursal_user.save()

	def test_tecnico_puede_crear_en_cualquier_sucursal(self):
		from operacion.services import usuario_puede_generar_ticket_para_sucursal

		can = usuario_puede_generar_ticket_para_sucursal(self.tecnico, self.s2)
		self.assertTrue(can)

	def test_sucursal_no_puede_crear_en_otra(self):
		from operacion.services import usuario_puede_generar_ticket_para_sucursal

		can = usuario_puede_generar_ticket_para_sucursal(self.sucursal_user, self.s2)
		self.assertFalse(can)


class TicketPermissionObjectTests(TestCase):
	def setUp(self):
		NumeradorDocumento.objects.create(
			clave="TICKET", nombre="Tickets", prefijo="ITD"
		)
		User = get_user_model()
		self.admin = User.objects.create_user(username="admin", password="p", rol=User.Rol.ADMINISTRADOR)
		self.supervisor = User.objects.create_user(username="sup", password="p", rol=User.Rol.SUPERVISOR)
		self.tecnico = User.objects.create_user(username="tec", password="p", rol=User.Rol.TECNICO)
		self.jdistrito = User.objects.create_user(username="jd", password="p", rol=User.Rol.JDISTRITO)
		self.sucursal_user = User.objects.create_user(username="suc", password="p", rol=User.Rol.SUCURSAL)
		self.consultor = User.objects.create_user(username="con", password="p", rol=User.Rol.CONSULTOR)

		self.s1 = Sucursal.objects.create(nombre="S1", codigo="S1", activo=True)
		self.s2 = Sucursal.objects.create(nombre="S2", codigo="S2", activo=True)
		self.categoria = Categoria.objects.create(nombre="Cat1", activo=True)

		# assign sucursal and jdistrito mapping
		self.sucursal_user.sucursal = self.s1
		self.sucursal_user.save()

		self.jdistrito.sucursales_asignadas.add(self.s1)

		# Ticket in s1
		self.ticket = Ticket.objects.create(
			titulo="T1",
			descripcion="D",
			sucursal=self.s1,
			categoria=self.categoria,
			creado_por=self.admin,
			tecnico_asignado=self.tecnico,
		)

	def make_req(self, user, method="PUT"):
		from types import SimpleNamespace
		return SimpleNamespace(user=user, method=method)

	def test_admin_can_modify(self):
		from operacion.permissions import TicketPermission
		perm = TicketPermission()
		req = self.make_req(self.admin)
		self.assertTrue(perm.has_object_permission(req, None, self.ticket))

	def test_supervisor_can_modify(self):
		from operacion.permissions import TicketPermission
		perm = TicketPermission()
		req = self.make_req(self.supervisor)
		self.assertTrue(perm.has_object_permission(req, None, self.ticket))

	def test_consultor_cannot_modify(self):
		from operacion.permissions import TicketPermission
		perm = TicketPermission()
		req = self.make_req(self.consultor)
		self.assertFalse(perm.has_object_permission(req, None, self.ticket))

	def test_tecnico_can_modify_assigned_or_created(self):
		from operacion.permissions import TicketPermission
		perm = TicketPermission()
		req = self.make_req(self.tecnico)
		self.assertTrue(perm.has_object_permission(req, None, self.ticket))

	def test_jdistrito_can_modify_assigned_sucursal(self):
		from operacion.permissions import TicketPermission
		perm = TicketPermission()
		req = self.make_req(self.jdistrito)
		self.assertTrue(perm.has_object_permission(req, None, self.ticket))

	def test_sucursal_user_can_modify_own_sucursal(self):
		from operacion.permissions import TicketPermission
		perm = TicketPermission()
		req = self.make_req(self.sucursal_user)
		self.assertTrue(perm.has_object_permission(req, None, self.ticket))


class TicketApiTests(TestCase):
	def setUp(self):
		self.directorio_media = tempfile.TemporaryDirectory()
		self.configuracion_media = override_settings(
			MEDIA_ROOT=self.directorio_media.name
		)
		self.configuracion_media.enable()
		self.addCleanup(self.configuracion_media.disable)
		self.addCleanup(self.directorio_media.cleanup)
		NumeradorDocumento.objects.create(
			clave="TICKET", nombre="Tickets", prefijo="ITD"
		)
		Usuario = get_user_model()
		self.admin = Usuario.objects.create_user(
			username="admin_api", password="p", rol=Usuario.Rol.ADMINISTRADOR
		)
		self.consultor = Usuario.objects.create_user(
			username="consultor_api", password="p", rol=Usuario.Rol.CONSULTOR
		)
		self.supervisor = Usuario.objects.create_user(
			username="supervisor_api", password="p", rol=Usuario.Rol.SUPERVISOR
		)
		self.tecnico = Usuario.objects.create_user(
			username="tecnico_api", password="p", rol=Usuario.Rol.TECNICO
		)
		self.usuario_sucursal = Usuario.objects.create_user(
			username="sucursal_api", password="p", rol=Usuario.Rol.SUCURSAL
		)
		self.s1 = Sucursal.objects.create(codigo="API1", nombre="API 1")
		self.s2 = Sucursal.objects.create(codigo="API2", nombre="API 2")
		self.usuario_sucursal.sucursal = self.s1
		self.usuario_sucursal.save(update_fields=["sucursal"])
		self.categoria = Categoria.objects.create(nombre="Categoría API")
		self.client = APIClient()

	def payload(self, sucursal):
		return {
			"titulo": "Ticket API",
			"descripcion": "Prueba",
			"sucursal": str(sucursal.pk),
			"categoria": str(self.categoria.pk),
			"origen": Ticket.Origen.LLAMADA,
		}

	def test_sucursal_no_puede_crear_ticket_para_otra_sucursal(self):
		self.client.force_authenticate(self.usuario_sucursal)
		response = self.client.post("/api/v1/tickets/", self.payload(self.s2))
		self.assertEqual(response.status_code, 403)
		self.assertEqual(Ticket.objects.count(), 0)

	def test_creacion_api_genera_historial(self):
		self.client.force_authenticate(self.admin)
		response = self.client.post("/api/v1/tickets/", self.payload(self.s2))
		self.assertEqual(response.status_code, 201)
		ticket = Ticket.objects.get()
		self.assertEqual(ticket.creado_por, self.admin)
		self.assertEqual(ticket.historial.count(), 1)

	def test_consultor_no_puede_modificar_ticket(self):
		ticket = Ticket.objects.create(
			titulo="Solo lectura",
			descripcion="Prueba",
			sucursal=self.s1,
			categoria=self.categoria,
			creado_por=self.admin,
		)
		self.client.force_authenticate(self.consultor)
		response = self.client.patch(
			f"/api/v1/tickets/{ticket.pk}/", {"estado": Ticket.Estado.CERRADO}
		)
		self.assertEqual(response.status_code, 403)

	def test_update_no_expone_campos_de_auditoria(self):
		ticket = Ticket.objects.create(
			titulo="Auditoría",
			descripcion="Prueba",
			sucursal=self.s1,
			categoria=self.categoria,
			creado_por=self.admin,
		)
		self.client.force_authenticate(self.admin)
		response = self.client.patch(
			f"/api/v1/tickets/{ticket.pk}/",
			{"codigo": "MANIPULADO", "creado_por": str(self.consultor.pk)},
		)
		self.assertEqual(response.status_code, 200)
		ticket.refresh_from_db()
		self.assertNotEqual(ticket.codigo, "MANIPULADO")
		self.assertEqual(ticket.creado_por, self.admin)

	def crear_ticket_reporte(self, estado=Ticket.Estado.NUEVO):
		return Ticket.objects.create(
			titulo=f"Reporte {estado}",
			descripcion="Prueba",
			sucursal=self.s1,
			categoria=self.categoria,
			creado_por=self.admin,
			estado=estado,
		)

	def test_reporte_filtra_por_rango_de_fechas(self):
		antiguo = self.crear_ticket_reporte()
		reciente = self.crear_ticket_reporte(Ticket.Estado.CERRADO)
		Ticket.objects.filter(pk=antiguo.pk).update(
			fecha_creacion=timezone.now() - timedelta(days=10)
		)
		hoy = timezone.localdate().isoformat()

		self.client.force_authenticate(self.consultor)
		response = self.client.get(
			f"/api/v1/reportes/tickets/?fecha_desde={hoy}&fecha_hasta={hoy}"
		)
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["total"], 1)
		self.assertEqual(response.data["por_estado"][0]["estado"], reciente.estado)

	def test_dashboard_calcula_resumen(self):
		self.crear_ticket_reporte(Ticket.Estado.NUEVO)
		self.crear_ticket_reporte(Ticket.Estado.EN_PROCESO)
		self.crear_ticket_reporte(Ticket.Estado.CERRADO)

		self.client.force_authenticate(self.supervisor)
		response = self.client.get("/api/v1/dashboard/general/")
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["tickets_total"], 3)
		self.assertEqual(response.data["tickets_abiertos"], 2)
		self.assertEqual(response.data["tickets_en_proceso"], 1)
		self.assertEqual(response.data["tickets_cerrados"], 1)

	def test_tecnico_no_puede_ver_dashboard_general(self):
		self.client.force_authenticate(self.tecnico)
		response = self.client.get("/api/v1/dashboard/general/")
		self.assertEqual(response.status_code, 403)

	def test_filtro_fecha_invalida_devuelve_400(self):
		self.client.force_authenticate(self.admin)
		response = self.client.get(
			"/api/v1/reportes/tickets/?fecha_desde=no-es-una-fecha"
		)
		self.assertEqual(response.status_code, 400)

	def test_ciclo_operativo_completo_registra_auditoria(self):
		ticket = self.crear_ticket_reporte()
		base_url = f"/api/v1/tickets/{ticket.pk}"

		self.client.force_authenticate(self.admin)
		response = self.client.post(
			f"{base_url}/asignar/", {"tecnico": str(self.tecnico.pk)}
		)
		self.assertEqual(response.status_code, 200)
		ticket.refresh_from_db()
		self.assertEqual(ticket.estado, Ticket.Estado.ASIGNADO)
		self.assertEqual(ticket.tecnico_asignado, self.tecnico)

		self.client.force_authenticate(self.tecnico)
		response = self.client.post(f"{base_url}/tomar/", {})
		self.assertEqual(response.status_code, 200)
		ticket.refresh_from_db()
		self.assertEqual(ticket.estado, Ticket.Estado.EN_PROCESO)
		self.assertEqual(ticket.tomado_por, self.tecnico)
		self.assertIsNotNone(ticket.fecha_toma)

		response = self.client.post(
			f"{base_url}/resolver/", {"solucion": "Se reemplazó el equipo."}
		)
		self.assertEqual(response.status_code, 200)
		ticket.refresh_from_db()
		self.assertEqual(ticket.estado, Ticket.Estado.RESUELTO)
		self.assertEqual(ticket.resuelto_por, self.tecnico)
		self.assertIsNotNone(ticket.fecha_resolucion)

		self.client.force_authenticate(self.admin)
		response = self.client.post(
			f"{base_url}/cerrar/", {"comentario": "Validado por soporte."}
		)
		self.assertEqual(response.status_code, 200)
		ticket.refresh_from_db()
		self.assertEqual(ticket.estado, Ticket.Estado.CERRADO)
		self.assertEqual(ticket.cerrado_por, self.admin)
		self.assertIsNotNone(ticket.fecha_cierre)
		self.assertEqual(ticket.historial.count(), 4)
		self.assertEqual(
			list(ticket.historial.values_list("tipo_movimiento", flat=True)),
			[
				HistorialTicket.TipoMovimiento.ASIGNACION,
				HistorialTicket.TipoMovimiento.CAMBIO_ESTADO,
				HistorialTicket.TipoMovimiento.RESOLUCION,
				HistorialTicket.TipoMovimiento.CIERRE,
			],
		)

	def test_no_se_puede_cerrar_un_ticket_sin_resolver(self):
		ticket = self.crear_ticket_reporte()
		self.client.force_authenticate(self.admin)
		response = self.client.post(
			f"/api/v1/tickets/{ticket.pk}/cerrar/", {}
		)
		self.assertEqual(response.status_code, 400)
		ticket.refresh_from_db()
		self.assertEqual(ticket.estado, Ticket.Estado.NUEVO)
		self.assertEqual(ticket.historial.count(), 0)

	def test_tecnico_no_puede_asignar_tickets(self):
		ticket = self.crear_ticket_reporte()
		self.client.force_authenticate(self.tecnico)
		response = self.client.post(
			f"/api/v1/tickets/{ticket.pk}/asignar/",
			{"tecnico": str(self.tecnico.pk)},
		)
		self.assertEqual(response.status_code, 403)

	def test_estado_no_se_puede_cambiar_con_patch_generico(self):
		ticket = self.crear_ticket_reporte()
		self.client.force_authenticate(self.admin)
		response = self.client.patch(
			f"/api/v1/tickets/{ticket.pk}/",
			{"estado": Ticket.Estado.CERRADO},
		)
		self.assertEqual(response.status_code, 200)
		ticket.refresh_from_db()
		self.assertEqual(ticket.estado, Ticket.Estado.NUEVO)

	def test_tecnico_documenta_diagnostico_en_ticket_asignado(self):
		ticket = self.crear_ticket_reporte()
		ticket.tecnico_asignado = self.tecnico
		ticket.save(update_fields=("tecnico_asignado", "fecha_modificacion"))
		self.client.force_authenticate(self.tecnico)
		response = self.client.post(
			f"/api/v1/tickets/{ticket.pk}/comentarios/",
			{
				"tipo": "DIAGNOSTICO",
				"texto": "La fuente no entrega voltaje estable.",
			},
		)
		self.assertEqual(response.status_code, 201)
		self.assertEqual(ticket.comentarios.count(), 1)
		self.assertEqual(ticket.comentarios.get().autor, self.tecnico)
		self.assertEqual(
			ticket.historial.get().tipo_movimiento,
			HistorialTicket.TipoMovimiento.COMENTARIO,
		)

	def test_consultor_puede_leer_pero_no_documentar(self):
		ticket = self.crear_ticket_reporte()
		self.client.force_authenticate(self.consultor)
		url = f"/api/v1/tickets/{ticket.pk}/comentarios/"
		self.assertEqual(self.client.get(url).status_code, 200)
		response = self.client.post(
			url, {"tipo": "NOTA", "texto": "No debería guardarse."}
		)
		self.assertEqual(response.status_code, 403)
		self.assertEqual(ticket.comentarios.count(), 0)

	def test_adjunto_valido_se_guarda_y_genera_historial(self):
		ticket = self.crear_ticket_reporte()
		ticket.tecnico_asignado = self.tecnico
		ticket.save(update_fields=("tecnico_asignado", "fecha_modificacion"))
		self.client.force_authenticate(self.tecnico)
		archivo = SimpleUploadedFile(
			"evidencia.png", b"contenido de prueba", content_type="image/png"
		)
		response = self.client.post(
			f"/api/v1/tickets/{ticket.pk}/adjuntos/",
			{"archivo": archivo, "descripcion": "Captura del error."},
			format="multipart",
		)
		self.assertEqual(response.status_code, 201)
		self.assertEqual(ticket.adjuntos.count(), 1)
		self.assertEqual(ticket.adjuntos.get().nombre_original, "evidencia.png")
		self.assertEqual(
			ticket.historial.get().tipo_movimiento,
			HistorialTicket.TipoMovimiento.ADJUNTO,
		)

	def test_adjunto_ejecutable_es_rechazado(self):
		ticket = self.crear_ticket_reporte()
		self.client.force_authenticate(self.admin)
		archivo = SimpleUploadedFile(
			"programa.exe", b"archivo no permitido"
		)
		response = self.client.post(
			f"/api/v1/tickets/{ticket.pk}/adjuntos/",
			{"archivo": archivo},
			format="multipart",
		)
		self.assertEqual(response.status_code, 400)
		self.assertEqual(ticket.adjuntos.count(), 0)

	def test_dashboard_personal_tecnico_solo_cuenta_asignados(self):
		activo = self.crear_ticket_reporte(Ticket.Estado.EN_PROCESO)
		activo.tecnico_asignado = self.tecnico
		activo.save(update_fields=("tecnico_asignado", "fecha_modificacion"))
		resuelto = self.crear_ticket_reporte(Ticket.Estado.RESUELTO)
		resuelto.tecnico_asignado = self.tecnico
		resuelto.save(update_fields=("tecnico_asignado", "fecha_modificacion"))
		self.crear_ticket_reporte(Ticket.Estado.NUEVO)

		self.client.force_authenticate(self.tecnico)
		response = self.client.get("/api/v1/dashboard/mio/")
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["tickets_activos"], 1)
		self.assertEqual(response.data["tickets_resueltos"], 1)
