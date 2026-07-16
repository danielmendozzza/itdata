from django.db import transaction

from .models import NumeradorDocumento


class NumeradorNoEncontradoError(Exception):
    """
    Se produce cuando no existe un numerador
    activo con la clave solicitada.
    """

    pass


@transaction.atomic
def obtener_siguiente_numero(clave):
    """
    Incrementa un numerador de manera segura y devuelve:

    numero: valor numérico generado.
    codigo: código visible generado.

    Ejemplo:
    numero = 1
    codigo = ITD-000001
    """

    try:
        numerador = (
            NumeradorDocumento.objects
            .select_for_update()
            .get(
                clave=clave,
                activo=True,
            )
        )

    except NumeradorDocumento.DoesNotExist as error:
        raise NumeradorNoEncontradoError(
            f"No existe un numerador activo con la clave '{clave}'."
        ) from error

    numerador.ultimo_numero += 1

    numerador.save(
        update_fields=[
            "ultimo_numero",
            "fecha_modificacion",
        ]
    )

    codigo = numerador.formar_codigo(
        numerador.ultimo_numero
    )

    return numerador.ultimo_numero, codigo