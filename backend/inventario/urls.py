from rest_framework.routers import DefaultRouter

from .views import ActivoCatalogoViewSet, ActivoViewSet, CriticidadViewSet, TipoActivoViewSet

router = DefaultRouter()
router.register("configuracion/activos", ActivoViewSet, basename="activo-configuracion")
router.register("catalogos/tipos-activo", TipoActivoViewSet, basename="tipo-activo")
router.register("catalogos/criticidades", CriticidadViewSet, basename="criticidad")
router.register("catalogos/activos", ActivoCatalogoViewSet, basename="activo-catalogo")

urlpatterns = router.urls
