from usuarios.models import Usuario

from .models import Sucursal


def obtener_sucursales_visibles_para_usuario(usuario):
    if not usuario or not usuario.is_authenticated:
        return Sucursal.objects.none()
    if not usuario.activo_operativamente:
        return Sucursal.objects.none()

    if usuario.rol == Usuario.Rol.ADMINISTRADOR:
        return Sucursal.objects.all()
    if usuario.rol in (
        Usuario.Rol.SUPERVISOR,
        Usuario.Rol.TECNICO,
        Usuario.Rol.CONSULTOR,
    ):
        return Sucursal.objects.filter(activo=True)
    if usuario.rol == Usuario.Rol.JDISTRITO:
        return Sucursal.objects.filter(
            activo=True,
            pk__in=usuario.sucursales_asignadas.values("pk"),
        )
    if usuario.rol == Usuario.Rol.SUCURSAL:
        return Sucursal.objects.filter(activo=True, pk=usuario.sucursal_id)
    return Sucursal.objects.none()
