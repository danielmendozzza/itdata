"""Cliente HTTP común para Microsoft Graph."""

import logging
from typing import Any, Mapping, Optional

import requests

from .auth import GraphAuth
from .exceptions import GraphRequestError

logger = logging.getLogger(__name__)


class GraphClient:
    """Centraliza solicitudes autenticadas a la API de Microsoft Graph."""

    DEFAULT_BASE_URL = "https://graph.microsoft.com/v1.0"

    def __init__(
        self,
        auth: GraphAuth,
        *,
        session: Optional[requests.Session] = None,
        timeout: float = 30.0,
        base_url: str = DEFAULT_BASE_URL,
    ) -> None:
        """Configura autenticación, sesión reutilizable y timeout HTTP."""
        if timeout <= 0:
            raise ValueError("El timeout debe ser mayor que cero.")
        self._auth = auth
        self._session = session or requests.Session()
        self._timeout = timeout
        self._base_url = base_url.rstrip("/")

    def get(self, path: str, **kwargs: Any) -> requests.Response:
        """Realiza una solicitud GET autenticada."""
        return self._request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> requests.Response:
        """Realiza una solicitud POST autenticada."""
        return self._request("POST", path, **kwargs)

    def patch(self, path: str, **kwargs: Any) -> requests.Response:
        """Realiza una solicitud PATCH autenticada."""
        return self._request("PATCH", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> requests.Response:
        """Realiza una solicitud DELETE autenticada."""
        return self._request("DELETE", path, **kwargs)

    def _request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        headers: dict[str, str] = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self._auth.get_access_token()}",
        }
        supplied_headers = kwargs.pop("headers", None)
        if isinstance(supplied_headers, Mapping):
            headers.update({str(key): str(value) for key, value in supplied_headers.items()})

        url = f"{self._base_url}/{path.lstrip('/')}"
        try:
            response = self._session.request(
                method=method,
                url=url,
                headers=headers,
                timeout=kwargs.pop("timeout", self._timeout),
                **kwargs,
            )
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            response = exc.response
            status_code = response.status_code if response is not None else None
            response_body = self._response_body(response)
            logger.exception(
                "Error al llamar Microsoft Graph (%s %s, status=%s)",
                method,
                url,
                status_code,
            )
            raise GraphRequestError(
                f"Falló la solicitud {method} a Microsoft Graph.",
                status_code=status_code,
                response_body=response_body,
            ) from exc

    @staticmethod
    def _response_body(response: Optional[requests.Response]) -> Any:
        """Extrae una respuesta de error sin ocultar fallos de decodificación."""
        if response is None:
            return None
        try:
            return response.json()
        except ValueError:
            return response.text
