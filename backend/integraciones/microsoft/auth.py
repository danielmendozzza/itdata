"""Autenticación OAuth2 para Microsoft Graph."""

import threading
import time
from typing import Any, Callable, Mapping, Optional, Sequence

import msal

from .exceptions import GraphAuthenticationError, GraphConfigurationError


class GraphAuth:
    """Obtiene y conserva tokens OAuth2 mediante Client Credentials.

    La instancia mantiene el token hasta poco antes de su vencimiento. MSAL
    recibe además su propio ``TokenCache`` para aislar su caché.
    """

    DEFAULT_SCOPES: tuple[str, ...] = ("https://graph.microsoft.com/.default",)
    _EXPIRY_MARGIN_SECONDS = 60

    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        *,
        scopes: Optional[Sequence[str]] = None,
        token_cache: Optional[msal.TokenCache] = None,
        time_provider: Callable[[], float] = time.monotonic,
    ) -> None:
        """Inicializa el cliente confidencial y valida sus credenciales."""
        missing = [
            name
            for name, value in (
                ("MS_GRAPH_TENANT_ID", tenant_id),
                ("MS_GRAPH_CLIENT_ID", client_id),
                ("MS_GRAPH_CLIENT_SECRET", client_secret),
            )
            if not value.strip()
        ]
        if missing:
            raise GraphConfigurationError(
                f"Faltan variables de Microsoft Graph: {', '.join(missing)}"
            )

        self._scopes = tuple(scopes or self.DEFAULT_SCOPES)
        self._time_provider = time_provider
        self._cached_token: Optional[str] = None
        self._expires_at = 0.0
        self._lock = threading.Lock()
        self._application = msal.ConfidentialClientApplication(
            client_id=client_id,
            authority=f"https://login.microsoftonline.com/{tenant_id}",
            client_credential=client_secret,
            token_cache=token_cache or msal.TokenCache(),
        )

    def get_access_token(self) -> str:
        """Devuelve un token vigente y lo renueva automáticamente al expirar."""
        with self._lock:
            now = self._time_provider()
            if self._cached_token and now < self._expires_at:
                return self._cached_token

            result: Mapping[str, Any] = self._application.acquire_token_for_client(
                scopes=list(self._scopes)
            )
            access_token = result.get("access_token")
            if not isinstance(access_token, str) or not access_token:
                detail = result.get("error_description") or result.get("error")
                raise GraphAuthenticationError(
                    "No fue posible autenticar con Microsoft Graph: "
                    f"{detail or 'respuesta sin token'}"
                )

            expires_in = result.get("expires_in", 0)
            lifetime = float(expires_in) if isinstance(expires_in, (int, float)) else 0.0
            self._cached_token = access_token
            self._expires_at = now + max(0.0, lifetime - self._EXPIRY_MARGIN_SECONDS)
            return access_token
