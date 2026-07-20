from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import ArticuloConocimientoViewSet, CrearArticuloDesdeTicketView


router = DefaultRouter()
router.register("conocimiento/articulos", ArticuloConocimientoViewSet, basename="articulo-conocimiento")

urlpatterns = [
    path(
        "conocimiento/articulos/desde-ticket/",
        CrearArticuloDesdeTicketView.as_view(),
        name="articulo-desde-ticket",
    ),
] + router.urls
