from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Sucursal


class SucursalApiPermissionTests(TestCase):
    def setUp(self):
        Usuario = get_user_model()
        self.admin = Usuario.objects.create_user(
            username="admin_sucursales",
            password="p",
            rol=Usuario.Rol.ADMINISTRADOR,
        )
        self.tecnico = Usuario.objects.create_user(
            username="tecnico_sucursales",
            password="p",
            rol=Usuario.Rol.TECNICO,
        )
        self.usuario_sucursal = Usuario.objects.create_user(
            username="usuario_sucursal",
            password="p",
            rol=Usuario.Rol.SUCURSAL,
        )
        self.sucursal = Sucursal.objects.create(codigo="S1", nombre="S1")
        self.otra_sucursal = Sucursal.objects.create(codigo="S2", nombre="S2")
        self.usuario_sucursal.sucursal = self.sucursal
        self.usuario_sucursal.save(update_fields=["sucursal"])
        self.client = APIClient()

    def test_solo_admin_puede_crear_sucursal(self):
        self.client.force_authenticate(self.tecnico)
        response = self.client.post(
            "/api/v1/sucursales/", {"codigo": "S3", "nombre": "S3"}
        )
        self.assertEqual(response.status_code, 403)

        self.client.force_authenticate(self.admin)
        response = self.client.post(
            "/api/v1/sucursales/", {"codigo": "S3", "nombre": "S3"}
        )
        self.assertEqual(response.status_code, 201)

    def test_usuario_sucursal_solo_lista_su_sucursal(self):
        self.client.force_authenticate(self.usuario_sucursal)
        response = self.client.get("/api/v1/sucursales/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], str(self.sucursal.pk))
