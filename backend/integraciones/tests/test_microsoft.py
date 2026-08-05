"""Tests unitarios de la infraestructura Microsoft Graph."""

from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

from integraciones.microsoft.auth import GraphAuth
from integraciones.microsoft.exceptions import GraphAuthenticationError, GraphConfigurationError
from integraciones.microsoft.graph import GraphClient
from integraciones.microsoft.services import MicrosoftGraphConfiguration, create_graph_client


class GraphAuthTests(TestCase):
    """Verifica autenticación y caché sin contactar a Microsoft."""

    @patch("integraciones.microsoft.auth.msal.ConfidentialClientApplication")
    def test_get_access_token_uses_cached_token(self, application_class: Mock) -> None:
        application = application_class.return_value
        application.acquire_token_for_client.return_value = {
            "access_token": "token", "expires_in": 3600
        }
        auth = GraphAuth("tenant", "client", "secret")
        self.assertEqual(auth.get_access_token(), "token")
        self.assertEqual(auth.get_access_token(), "token")
        application.acquire_token_for_client.assert_called_once()

    @patch("integraciones.microsoft.auth.msal.ConfidentialClientApplication")
    def test_get_access_token_renews_expired_token(self, application_class: Mock) -> None:
        application = application_class.return_value
        application.acquire_token_for_client.side_effect = [
            {"access_token": "first", "expires_in": 120},
            {"access_token": "second", "expires_in": 120},
        ]
        current_time = [1000.0]
        auth = GraphAuth(
            "tenant", "client", "secret", time_provider=lambda: current_time[0]
        )

        self.assertEqual(auth.get_access_token(), "first")
        current_time[0] = 1061.0
        self.assertEqual(auth.get_access_token(), "second")
        self.assertEqual(application.acquire_token_for_client.call_count, 2)

    @patch("integraciones.microsoft.auth.msal.ConfidentialClientApplication")
    def test_authentication_error_is_translated(self, application_class: Mock) -> None:
        application_class.return_value.acquire_token_for_client.return_value = {
            "error": "invalid_client"
        }
        with self.assertRaises(GraphAuthenticationError):
            GraphAuth("tenant", "client", "secret").get_access_token()


class MicrosoftGraphConfigurationTests(TestCase):
    """Verifica la lectura y validación de settings."""

    def test_reads_django_settings_object(self) -> None:
        source = SimpleNamespace(
            MS_GRAPH_TENANT_ID="tenant", MS_GRAPH_CLIENT_ID="client",
            MS_GRAPH_CLIENT_SECRET="secret", MS_GRAPH_MAILBOX="support@example.com",
        )
        configuration = MicrosoftGraphConfiguration.from_django_settings(source)
        self.assertEqual(configuration.mailbox, "support@example.com")

    def test_rejects_missing_credentials(self) -> None:
        with self.assertRaises(GraphConfigurationError):
            MicrosoftGraphConfiguration.from_django_settings(SimpleNamespace())


class GraphClientTests(TestCase):
    """Verifica la creación y el transporte HTTP mockeado."""

    def test_client_uses_session_without_real_request(self) -> None:
        auth = Mock(spec=GraphAuth)
        auth.get_access_token.return_value = "token"
        session = Mock()
        session.request.return_value.raise_for_status.return_value = None
        client = GraphClient(auth=auth, session=session, timeout=12)
        response = client.get("users", params={"$top": 1})
        self.assertIs(response, session.request.return_value)
        session.request.assert_called_once_with(
            method="GET", url="https://graph.microsoft.com/v1.0/users",
            headers={"Accept": "application/json", "Authorization": "Bearer token"},
            timeout=12, params={"$top": 1},
        )

    @patch("integraciones.microsoft.services.GraphAuth")
    def test_factory_creates_client(self, auth_class: Mock) -> None:
        configuration = MicrosoftGraphConfiguration("tenant", "client", "secret")
        client = create_graph_client(configuration=configuration)
        self.assertIsInstance(client, GraphClient)
        auth_class.assert_called_once_with(
            tenant_id="tenant", client_id="client", client_secret="secret"
        )
