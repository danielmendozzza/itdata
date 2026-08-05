"""Composición de servicios para Microsoft Graph."""

from dataclasses import dataclass
from typing import Any, Optional

import requests
from django.conf import settings as django_settings

from .auth import GraphAuth
from .exceptions import GraphConfigurationError
from .graph import GraphClient


@dataclass(frozen=True)
class MicrosoftGraphConfiguration:
    """Agrupa la configuración necesaria para los servicios Microsoft 365."""

    tenant_id: str
    client_id: str
    client_secret: str
    mailbox: str = ""

    @classmethod
    def from_django_settings(
        cls, settings_object: Optional[Any] = None
    ) -> "MicrosoftGraphConfiguration":
        """Lee la configuración expuesta por Django y valida credenciales."""
        source = settings_object or django_settings
        configuration = cls(
            tenant_id=str(getattr(source, "MS_GRAPH_TENANT_ID", "")),
            client_id=str(getattr(source, "MS_GRAPH_CLIENT_ID", "")),
            client_secret=str(getattr(source, "MS_GRAPH_CLIENT_SECRET", "")),
            mailbox=str(getattr(source, "MS_GRAPH_MAILBOX", "")),
        )
        configuration.validate()
        return configuration

    def validate(self) -> None:
        """Comprueba las credenciales sin exigir aún un buzón de correo."""
        missing = [name for name, value in (
            ("MS_GRAPH_TENANT_ID", self.tenant_id),
            ("MS_GRAPH_CLIENT_ID", self.client_id),
            ("MS_GRAPH_CLIENT_SECRET", self.client_secret),
        ) if not value.strip()]
        if missing:
            raise GraphConfigurationError(
                f"Faltan variables de Microsoft Graph: {', '.join(missing)}"
            )


def create_graph_client(
    *,
    configuration: Optional[MicrosoftGraphConfiguration] = None,
    session: Optional[requests.Session] = None,
    timeout: float = 30.0,
) -> GraphClient:
    """Construye un cliente Graph con dependencias reemplazables para tests."""
    selected = configuration or MicrosoftGraphConfiguration.from_django_settings()
    selected.validate()
    auth = GraphAuth(
        tenant_id=selected.tenant_id,
        client_id=selected.client_id,
        client_secret=selected.client_secret,
    )
    return GraphClient(auth=auth, session=session, timeout=timeout)
