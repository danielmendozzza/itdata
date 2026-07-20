from rest_framework.routers import DefaultRouter
from django.urls import path

from .views import (
    CategoriaViewSet,
    DashboardGeneralView,
    DashboardPersonalView,
    ReporteTicketsView,
    TicketViewSet,
    SubcategoriaViewSet,
)

router = DefaultRouter()
router.register(r"tickets", TicketViewSet, basename="ticket")
router.register(r"catalogos/categorias", CategoriaViewSet, basename="categoria")
router.register(r"catalogos/subcategorias", SubcategoriaViewSet, basename="subcategoria")

urlpatterns = [
    path("reportes/tickets/", ReporteTicketsView.as_view(), name="reporte-tickets"),
    path("dashboard/general/", DashboardGeneralView.as_view(), name="dashboard-general"),
    path("dashboard/mio/", DashboardPersonalView.as_view(), name="dashboard-personal"),
] + router.urls
