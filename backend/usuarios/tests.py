from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient


class UsuarioApiTests(TestCase):
    def setUp(self):
        Usuario = get_user_model()
        self.usuario = Usuario.objects.create_user(
            username="usuario_me",
            password="p",
            first_name="Daniel",
            rol=Usuario.Rol.SUPERVISOR,
        )
        self.tecnico = Usuario.objects.create_user(
            username="tecnico_activo",
            password="p",
            rol=Usuario.Rol.TECNICO,
        )
        Usuario.objects.create_user(
            username="tecnico_inactivo",
            password="p",
            rol=Usuario.Rol.TECNICO,
            activo_operativamente=False,
        )
        self.client = APIClient()

    def test_me_devuelve_identidad_y_rol(self):
        self.client.force_authenticate(self.usuario)
        response = self.client.get("/api/v1/auth/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["username"], "usuario_me")
        self.assertEqual(response.data["nombre_completo"], "Daniel")
        self.assertEqual(response.data["rol"], "SUPERVISOR")

    def test_catalogo_tecnicos_solo_incluye_activos(self):
        self.client.force_authenticate(self.usuario)
        response = self.client.get("/api/v1/catalogos/tecnicos/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], str(self.tecnico.pk))


class AdministracionUsuariosApiTests(TestCase):
    def setUp(self):
        Usuario = get_user_model()
        self.admin = Usuario.objects.create_user(
            username="admin_usuarios",
            password="password123",
            rol=Usuario.Rol.ADMINISTRADOR,
        )
        self.supervisor = Usuario.objects.create_user(
            username="supervisor_usuarios",
            password="password123",
            rol=Usuario.Rol.SUPERVISOR,
        )
        self.tecnico = Usuario.objects.create_user(
            username="tecnico_usuarios",
            password="password123",
            rol=Usuario.Rol.TECNICO,
        )
        self.client = APIClient()

    def payload(self, username, rol):
        return {
            "username": username,
            "password": "password123",
            "first_name": "Usuario",
            "last_name": "Prueba",
            "email": f"{username}@example.com",
            "rol": rol,
            "activo_operativamente": True,
            "is_active": True,
        }

    def test_admin_puede_crear_supervisor(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            "/api/v1/configuracion/usuarios/",
            self.payload("nuevo_supervisor", "SUPERVISOR"),
        )
        self.assertEqual(response.status_code, 201)
        usuario = get_user_model().objects.get(username="nuevo_supervisor")
        self.assertEqual(usuario.rol, "SUPERVISOR")
        self.assertTrue(usuario.check_password("password123"))

    def test_supervisor_no_puede_crear_supervisor_ni_admin(self):
        self.client.force_authenticate(self.supervisor)
        for rol in ("SUPERVISOR", "ADMINISTRADOR"):
            response = self.client.post(
                "/api/v1/configuracion/usuarios/",
                self.payload(f"prohibido_{rol.lower()}", rol),
            )
            self.assertEqual(response.status_code, 400)

    def test_supervisor_puede_crear_tecnico(self):
        self.client.force_authenticate(self.supervisor)
        response = self.client.post(
            "/api/v1/configuracion/usuarios/",
            self.payload("tecnico_nuevo", "TECNICO"),
        )
        self.assertEqual(response.status_code, 201)

    def test_supervisor_no_lista_usuarios_privilegiados(self):
        self.client.force_authenticate(self.supervisor)
        response = self.client.get("/api/v1/configuracion/usuarios/")
        self.assertEqual(response.status_code, 200)
        roles = {item["rol"] for item in response.data["results"]}
        self.assertNotIn("ADMINISTRADOR", roles)
        self.assertNotIn("SUPERVISOR", roles)
        self.assertIn("TECNICO", roles)

    def test_borrar_usuario_lo_desactiva_sin_eliminar_historial(self):
        self.client.force_authenticate(self.admin)
        response = self.client.delete(
            f"/api/v1/configuracion/usuarios/{self.tecnico.pk}/"
        )
        self.assertEqual(response.status_code, 204)
        self.tecnico.refresh_from_db()
        self.assertFalse(self.tecnico.is_active)
        self.assertFalse(self.tecnico.activo_operativamente)
