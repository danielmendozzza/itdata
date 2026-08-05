"""Excepciones específicas de la integración con Microsoft Graph."""

from typing import Any, Optional


class GraphConfigurationError(Exception):
    """Indica que falta o es inválida una opción de Microsoft Graph."""


class GraphAuthenticationError(Exception):
    """Indica que Microsoft no pudo emitir un token de acceso."""


class GraphRequestError(Exception):
    """Representa un error de transporte o una respuesta fallida de Graph."""

    def __init__(self, message: str, *, status_code: Optional[int] = None, response_body: Any = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body
