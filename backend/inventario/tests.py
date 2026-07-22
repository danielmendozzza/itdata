from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from organizacion.models import Sucursal
from .models import Activo, Criticidad, TipoActivo


class AdministracionActivosApiTests(TestCase):
    def setUp(self):
        Usuario = get_user_model()
        self.admin = Usuario.objects.create_user(
            username="admin_activos", rol=Usuario.Rol.ADMINISTRADOR
        )
        self.supervisor = Usuario.objects.create_user(
            username="supervisor_activos", rol=Usuario.Rol.SUPERVISOR
        )
        self.tecnico = Usuario.objects.create_user(
            username="tecnico_activos", rol=Usuario.Rol.TECNICO
        )
        self.sucursal = Sucursal.objects.create(codigo="ACT1", nombre="Sucursal activos")
        self.tipo = TipoActivo.objects.create(nombre="Notebook")
        self.criticidad = Criticidad.objects.create(nombre="Alta", nivel=3)
        self.client = APIClient()
        self.payload = {
            "codigo": "nb-001",
            "nombre": "Notebook soporte",
            "tipo_activo": str(self.tipo.pk),
            "sucursal": str(self.sucursal.pk),
            "criticidad": str(self.criticidad.pk),
            "estado": Activo.Estado.OPERATIVO,
            "activo": True,
        }

    def test_admin_puede_crear_activo_y_normaliza_codigo(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post("/api/v1/configuracion/activos/", self.payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Activo.objects.get().codigo, "NB-001")

    def test_supervisor_puede_editar_activo(self):
        activo = Activo.objects.create(
            codigo="NB-002", nombre="Equipo", tipo_activo=self.tipo,
            criticidad=self.criticidad,
        )
        self.client.force_authenticate(self.supervisor)
        response = self.client.patch(
            f"/api/v1/configuracion/activos/{activo.pk}/",
            {"estado": Activo.Estado.EN_REPARACION},
        )
        self.assertEqual(response.status_code, 200)
        activo.refresh_from_db()
        self.assertEqual(activo.estado, Activo.Estado.EN_REPARACION)

    def test_tecnico_no_puede_administrar_activos(self):
        self.client.force_authenticate(self.tecnico)
        response = self.client.post("/api/v1/configuracion/activos/", self.payload)
        self.assertEqual(response.status_code, 403)

    def test_eliminar_desactiva_sin_borrar_historial(self):
        activo = Activo.objects.create(
            codigo="NB-003", nombre="Equipo", tipo_activo=self.tipo,
            criticidad=self.criticidad,
        )
        self.client.force_authenticate(self.admin)
        response = self.client.delete(f"/api/v1/configuracion/activos/{activo.pk}/")
        self.assertEqual(response.status_code, 204)
        activo.refresh_from_db()
        self.assertFalse(activo.activo)

    def test_catalogo_de_activos_solo_devuelve_activos_de_la_sucursal(self):
        usuario = get_user_model().objects.create_user(
            username="sucursal_activos",
            rol=get_user_model().Rol.SUCURSAL,
            sucursal=self.sucursal,
        )
        visible = Activo.objects.create(
            codigo="NB-004", nombre="Visible", tipo_activo=self.tipo,
            criticidad=self.criticidad, sucursal=self.sucursal,
        )
        otra = Sucursal.objects.create(codigo="ACT2", nombre="Otra")
        Activo.objects.create(
            codigo="NB-005", nombre="Oculto", tipo_activo=self.tipo,
            criticidad=self.criticidad, sucursal=otra,
        )
        self.client.force_authenticate(usuario)
        response = self.client.get("/api/v1/catalogos/activos/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.data], [str(visible.pk)])
