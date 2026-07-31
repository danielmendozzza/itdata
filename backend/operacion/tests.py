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
			f"/api/v1/tickets/{ticket.pk}/", {"estado": Ticket.Estado.RESUELTO}
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
		reciente = self.crear_ticket_reporte(Ticket.Estado.RESUELTO)
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

	def test_reporte_calcula_comparativa_mensual_y_tiempos_operativos(self):
		ahora = timezone.now()
		ticket = self.crear_ticket_reporte(Ticket.Estado.RESUELTO)
		Ticket.objects.filter(pk=ticket.pk).update(
			tecnico_asignado=self.tecnico,
			fecha_toma=ahora - timedelta(hours=4),
			fecha_resolucion=ahora,
		)
		espera = HistorialTicket.objects.create(
			ticket=ticket,
			usuario=self.tecnico,
			tipo_movimiento=HistorialTicket.TipoMovimiento.CAMBIO_ESTADO,
			estado_anterior=Ticket.Estado.EN_PROCESO,
			estado_nuevo=Ticket.Estado.ESPERANDO_PROVEEDOR,
			comentario="Esperando repuesto",
		)
		resolucion = HistorialTicket.objects.create(
			ticket=ticket,
			usuario=self.tecnico,
			tipo_movimiento=HistorialTicket.TipoMovimiento.RESOLUCION,
			estado_anterior=Ticket.Estado.ESPERANDO_PROVEEDOR,
			estado_nuevo=Ticket.Estado.RESUELTO,
			comentario="Resuelto",
		)
		HistorialTicket.objects.filter(pk=espera.pk).update(
			fecha_creacion=ahora - timedelta(hours=2)
		)
		HistorialTicket.objects.filter(pk=resolucion.pk).update(fecha_creacion=ahora)

		self.client.force_authenticate(self.supervisor)
		response = self.client.get("/api/v1/reportes/tickets/?meses=3")
		self.assertEqual(response.status_code, 200)
		ultimo = response.data["comparativa_mensual"]["serie"][-1]
		self.assertEqual(ultimo["incidentes"], 1)
		self.assertAlmostEqual(ultimo["ti_mediana_segundos"], 7200, delta=2)
		self.assertAlmostEqual(
			ultimo["terceros_mediana_segundos"], 7200, delta=2
		)

	def test_dashboard_calcula_resumen(self):
		self.crear_ticket_reporte(Ticket.Estado.NUEVO)
		self.crear_ticket_reporte(Ticket.Estado.EN_PROCESO)
		self.crear_ticket_reporte(Ticket.Estado.RESUELTO)

		self.client.force_authenticate(self.supervisor)
		response = self.client.get("/api/v1/dashboard/general/")
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["tickets_total"], 3)
		self.assertEqual(response.data["tickets_abiertos"], 2)
		self.assertEqual(response.data["tickets_en_proceso"], 1)
		self.assertEqual(response.data["tickets_resueltos"], 1)


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

		self.assertEqual(ticket.historial.count(), 3)
		self.assertEqual(
			list(ticket.historial.values_list("tipo_movimiento", flat=True)),
			[
				HistorialTicket.TipoMovimiento.ASIGNACION,
				HistorialTicket.TipoMovimiento.CAMBIO_ESTADO,
				HistorialTicket.TipoMovimiento.RESOLUCION,
			],
		)

	def test_endpoint_cerrar_ya_no_existe(self):
		ticket = self.crear_ticket_reporte()
		self.client.force_authenticate(self.admin)
		response = self.client.post(
			f"/api/v1/tickets/{ticket.pk}/cerrar/", {}
		)
		self.assertEqual(response.status_code, 404)
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
			{"estado": Ticket.Estado.RESUELTO},
		)
		self.assertEqual(response.status_code, 200)
		ticket.refresh_from_db()
		self.assertEqual(ticket.estado, Ticket.Estado.NUEVO)

	def test_supervisor_cambia_estado_operativo_de_ticket_asignado(self):
		ticket = self.crear_ticket_reporte(Ticket.Estado.ASIGNADO)
		ticket.tecnico_asignado = self.tecnico
		ticket.save(update_fields=("tecnico_asignado", "fecha_modificacion"))
		self.client.force_authenticate(self.supervisor)
		response = self.client.post(
			f"/api/v1/tickets/{ticket.pk}/cambiar-estado/",
			{"estado": Ticket.Estado.ESPERANDO_PROVEEDOR, "comentario": "En garantía."},
		)
		self.assertEqual(response.status_code, 200)
		ticket.refresh_from_db()
		self.assertEqual(ticket.estado, Ticket.Estado.ESPERANDO_PROVEEDOR)
		self.assertEqual(ticket.historial.get().estado_nuevo, Ticket.Estado.ESPERANDO_PROVEEDOR)

	def test_tecnico_asignado_puede_cambiar_estado_operativo(self):
		ticket = self.crear_ticket_reporte(Ticket.Estado.EN_PROCESO)
		ticket.tecnico_asignado = self.tecnico
		ticket.save(update_fields=("tecnico_asignado", "fecha_modificacion"))
		self.client.force_authenticate(self.tecnico)
		response = self.client.post(
			f"/api/v1/tickets/{ticket.pk}/cambiar-estado/",
			{"estado": Ticket.Estado.EN_PRUEBAS},
		)
		self.assertEqual(response.status_code, 200)

	def test_ticket_sin_tecnico_no_puede_cambiar_estado_operativo(self):
		ticket = self.crear_ticket_reporte()
		self.client.force_authenticate(self.admin)
		response = self.client.post(
			f"/api/v1/tickets/{ticket.pk}/cambiar-estado/",
			{"estado": Ticket.Estado.EN_PROCESO},
		)
		self.assertEqual(response.status_code, 400)

	def test_tecnico_asignado_puede_dejar_ticket_pendiente(self):
		ticket = self.crear_ticket_reporte(Ticket.Estado.EN_PROCESO)
		ticket.tecnico_asignado = self.tecnico
		ticket.save(update_fields=("tecnico_asignado", "fecha_modificacion"))
		self.client.force_authenticate(self.tecnico)
		response = self.client.post(
			f"/api/v1/tickets/{ticket.pk}/cambiar-estado/",
			{"estado": Ticket.Estado.PENDIENTE, "comentario": "Atendiendo una prioridad."},
		)
		self.assertEqual(response.status_code, 200)
		ticket.refresh_from_db()
		self.assertEqual(ticket.estado, Ticket.Estado.PENDIENTE)

	def test_lista_muestra_al_tecnico_como_responsable_de_ti(self):
		ticket = self.crear_ticket_reporte(Ticket.Estado.EN_PROCESO)
		ticket.tecnico_asignado = self.tecnico
		ticket.save(update_fields=("tecnico_asignado", "fecha_modificacion"))
		self.client.force_authenticate(self.admin)
		response = self.client.get("/api/v1/tickets/")
		self.assertEqual(response.status_code, 200)
		item = next(
			item for item in response.data["results"]
			if item["id"] == str(ticket.pk)
		)
		self.assertEqual(item["responsable_actual_nombre"], str(self.tecnico))

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


class AperturasApiTests(TestCase):
	def setUp(self):
		NumeradorDocumento.objects.create(
			clave="TICKET", nombre="Tickets", prefijo="ITD"
		)
		Usuario = get_user_model()
		self.tecnico_uno = Usuario.objects.create_user(
			username="tecnico_apertura_1", rol=Usuario.Rol.TECNICO
		)
		self.tecnico_dos = Usuario.objects.create_user(
			username="tecnico_apertura_2", rol=Usuario.Rol.TECNICO
		)
		self.sucursal = Usuario.objects.create_user(
			username="sucursal_apertura", rol=Usuario.Rol.SUCURSAL
		)
		self.client = APIClient()

	def test_crea_apertura_solo_con_titulo_y_en_proceso(self):
		self.client.force_authenticate(self.tecnico_uno)
		response = self.client.post(
			"/api/v1/aperturas/", {"titulo": "Apertura nuevo local"}
		)
		self.assertEqual(response.status_code, 201)
		apertura = Ticket.objects.get(pk=response.data["id"])
		self.assertEqual(apertura.tipo, Ticket.Tipo.APERTURA)
		self.assertEqual(apertura.estado, Ticket.Estado.EN_PROCESO)
		self.assertIsNone(apertura.tecnico_asignado_id)
		self.assertIsNone(apertura.sucursal_id)
		self.assertEqual(apertura.historial.count(), 1)

	def test_cualquier_tecnico_puede_gestionar_la_apertura(self):
		apertura = Ticket.objects.create(
			titulo="Apertura compartida",
			tipo=Ticket.Tipo.APERTURA,
			descripcion="",
			estado=Ticket.Estado.EN_PROCESO,
			creado_por=self.tecnico_uno,
		)
		self.client.force_authenticate(self.tecnico_dos)
		response = self.client.post(
			f"/api/v1/aperturas/{apertura.pk}/cambiar-estado/",
			{"estado": Ticket.Estado.EN_PRUEBAS, "comentario": "Equipos instalados."},
		)
		self.assertEqual(response.status_code, 200)
		apertura.refresh_from_db()
		self.assertEqual(apertura.estado, Ticket.Estado.EN_PRUEBAS)

	def test_realizado_es_final_y_registra_responsable(self):
		apertura = Ticket.objects.create(
			titulo="Apertura final",
			tipo=Ticket.Tipo.APERTURA,
			descripcion="",
			estado=Ticket.Estado.EN_PRUEBAS,
			creado_por=self.tecnico_uno,
		)
		self.client.force_authenticate(self.tecnico_dos)
		response = self.client.post(
			f"/api/v1/aperturas/{apertura.pk}/cambiar-estado/",
			{"estado": Ticket.Estado.REALIZADO},
		)
		self.assertEqual(response.status_code, 200)
		apertura.refresh_from_db()
		self.assertEqual(apertura.resuelto_por, self.tecnico_dos)
		self.assertIsNotNone(apertura.fecha_resolucion)
		response = self.client.post(
			f"/api/v1/aperturas/{apertura.pk}/cambiar-estado/",
			{"estado": Ticket.Estado.EN_PROCESO},
		)
		self.assertEqual(response.status_code, 400)

	def test_sucursal_no_puede_acceder_a_aperturas(self):
		self.client.force_authenticate(self.sucursal)
		response = self.client.get("/api/v1/aperturas/")
		self.assertEqual(response.status_code, 403)


class CatalogosConfiguracionApiTests(TestCase):
	def setUp(self):
		Usuario = get_user_model()
		self.admin = Usuario.objects.create_user(username="admin_catalogos", password="password123", rol=Usuario.Rol.ADMINISTRADOR)
		self.consultor = Usuario.objects.create_user(username="consultor_catalogos", password="password123", rol=Usuario.Rol.CONSULTOR)
		self.client = APIClient()

	def test_admin_crea_categoria_y_subcategoria(self):
		self.client.force_authenticate(self.admin)
		response = self.client.post("/api/v1/catalogos/categorias/", {"nombre": "Redes", "descripcion": "Conectividad", "activo": True})
		self.assertEqual(response.status_code, 201)
		response = self.client.post("/api/v1/catalogos/subcategorias/", {"categoria": response.data["id"], "nombre": "WiFi", "activo": True})
		self.assertEqual(response.status_code, 201)

	def test_consultor_puede_leer_pero_no_modificar_catalogos(self):
		self.client.force_authenticate(self.consultor)
		self.assertEqual(self.client.get("/api/v1/catalogos/categorias/").status_code, 200)
		response = self.client.post("/api/v1/catalogos/categorias/", {"nombre": "Prohibida"})
		self.assertEqual(response.status_code, 403)
