from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import NumeradorDocumento
from operacion.models import Categoria, ComentarioTicket, Ticket
from organizacion.models import Sucursal

from .models import ArticuloConocimiento


class BaseConocimientoApiTests(TestCase):
    def setUp(self):
        NumeradorDocumento.objects.create(
            clave="TICKET", nombre="Tickets", prefijo="ITD"
        )
        Usuario = get_user_model()
        self.admin = Usuario.objects.create_user(
            username="admin_kb", password="p", rol=Usuario.Rol.ADMINISTRADOR
        )
        self.supervisor = Usuario.objects.create_user(
            username="supervisor_kb", password="p", rol=Usuario.Rol.SUPERVISOR
        )
        self.tecnico = Usuario.objects.create_user(
            username="tecnico_kb", password="p", rol=Usuario.Rol.TECNICO
        )
        self.otro_tecnico = Usuario.objects.create_user(
            username="otro_tecnico_kb", password="p", rol=Usuario.Rol.TECNICO
        )
        self.consultor = Usuario.objects.create_user(
            username="consultor_kb", password="p", rol=Usuario.Rol.CONSULTOR
        )
        self.usuario_sucursal = Usuario.objects.create_user(
            username="sucursal_kb", password="p", rol=Usuario.Rol.SUCURSAL
        )
        self.sucursal = Sucursal.objects.create(codigo="KB1", nombre="Sucursal KB")
        self.usuario_sucursal.sucursal = self.sucursal
        self.usuario_sucursal.save(update_fields=("sucursal",))
        self.categoria = Categoria.objects.create(nombre="Categoría KB")
        self.ticket = Ticket.objects.create(
            titulo="POS no inicia",
            descripcion="El POS queda detenido en la pantalla de carga.",
            sucursal=self.sucursal,
            categoria=self.categoria,
            creado_por=self.admin,
            tecnico_asignado=self.tecnico,
            resuelto_por=self.tecnico,
            estado=Ticket.Estado.RESUELTO,
            solucion="Reiniciar el servicio SQL y configurar el inicio automático.",
        )
        ComentarioTicket.objects.create(
            ticket=self.ticket,
            autor=self.tecnico,
            tipo=ComentarioTicket.Tipo.DIAGNOSTICO,
            texto="El servicio SQL estaba detenido.",
        )
        ComentarioTicket.objects.create(
            ticket=self.ticket,
            autor=self.tecnico,
            tipo=ComentarioTicket.Tipo.ACCION_REALIZADA,
            texto="Se inició el servicio y se validó el POS.",
        )
        self.client = APIClient()

    def crear_borrador(self):
        self.client.force_authenticate(self.tecnico)
        response = self.client.post(
            "/api/v1/conocimiento/articulos/desde-ticket/",
            {"ticket": str(self.ticket.pk)},
        )
        self.assertEqual(response.status_code, 201)
        return ArticuloConocimiento.objects.get()

    def test_tecnico_genera_borrador_documentado_desde_ticket(self):
        articulo = self.crear_borrador()
        self.assertEqual(articulo.autor, self.tecnico)
        self.assertEqual(articulo.estado, ArticuloConocimiento.Estado.BORRADOR)
        self.assertIn("servicio SQL estaba detenido", articulo.diagnostico)
        self.assertIn("Reiniciar el servicio SQL", articulo.procedimiento_solucion)
        self.assertEqual(list(articulo.tickets_relacionados.all()), [self.ticket])

    def test_genera_y_actualiza_borrador_desde_ticket_sin_resolver(self):
        self.ticket.estado = Ticket.Estado.EN_PROCESO
        self.ticket.save(update_fields=("estado", "fecha_modificacion"))
        self.client.force_authenticate(self.tecnico)
        response = self.client.post(
            "/api/v1/conocimiento/articulos/desde-ticket/",
            {"ticket": str(self.ticket.pk)},
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(ArticuloConocimiento.objects.count(), 1)
        response = self.client.post(
            "/api/v1/conocimiento/articulos/desde-ticket/",
            {"ticket": str(self.ticket.pk)},
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(ArticuloConocimiento.objects.count(), 1)

    def test_tecnico_no_responsable_no_puede_documentar_ticket(self):
        self.client.force_authenticate(self.otro_tecnico)
        response = self.client.post(
            "/api/v1/conocimiento/articulos/desde-ticket/",
            {"ticket": str(self.ticket.pk)},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(ArticuloConocimiento.objects.count(), 0)

    def test_flujo_revision_y_publicacion(self):
        articulo = self.crear_borrador()
        response = self.client.post(
            f"/api/v1/conocimiento/articulos/{articulo.pk}/enviar-a-revision/"
        )
        self.assertEqual(response.status_code, 200)
        articulo.refresh_from_db()
        self.assertEqual(articulo.estado, ArticuloConocimiento.Estado.EN_REVISION)

        response = self.client.post(
            f"/api/v1/conocimiento/articulos/{articulo.pk}/publicar/"
        )
        self.assertEqual(response.status_code, 403)

        self.client.force_authenticate(self.supervisor)
        response = self.client.post(
            f"/api/v1/conocimiento/articulos/{articulo.pk}/publicar/"
        )
        self.assertEqual(response.status_code, 200)
        articulo.refresh_from_db()
        self.assertEqual(articulo.estado, ArticuloConocimiento.Estado.PUBLICADO)
        self.assertEqual(articulo.revisado_por, self.supervisor)
        self.assertIsNotNone(articulo.fecha_publicacion)

    def test_consultor_solo_visualiza_publicados(self):
        articulo = self.crear_borrador()
        self.client.force_authenticate(self.consultor)
        response = self.client.get("/api/v1/conocimiento/articulos/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)

        articulo.estado = ArticuloConocimiento.Estado.PUBLICADO
        articulo.save(update_fields=("estado", "fecha_modificacion"))
        response = self.client.get("/api/v1/conocimiento/articulos/")
        self.assertEqual(response.data["count"], 1)
        response = self.client.post(
            "/api/v1/conocimiento/articulos/",
            {
                "titulo": "No permitido",
                "resumen": "No permitido",
                "procedimiento_solucion": "No permitido",
                "categoria": str(self.categoria.pk),
            },
        )
        self.assertEqual(response.status_code, 403)

    def test_busqueda_encuentra_titulo_o_descripcion_del_ticket(self):
        articulo = self.crear_borrador()
        articulo.estado = ArticuloConocimiento.Estado.PUBLICADO
        articulo.save(update_fields=("estado", "fecha_modificacion"))
        self.client.force_authenticate(self.usuario_sucursal)
        response = self.client.get(
            "/api/v1/conocimiento/articulos/?search=POS+no+inicia"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], str(articulo.pk))
