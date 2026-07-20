from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import TecnicoListView, UsuarioActualView, UsuarioAdminViewSet


router = DefaultRouter()
router.register("configuracion/usuarios", UsuarioAdminViewSet, basename="usuario-admin")


urlpatterns = [
    path("auth/me/", UsuarioActualView.as_view(), name="usuario-actual"),
    path("catalogos/tecnicos/", TecnicoListView.as_view(), name="tecnicos"),
] + router.urls
