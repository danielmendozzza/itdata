"""Contrato inicial para operaciones de correo en Microsoft Graph."""

from typing import Any, NoReturn

from .graph import GraphClient


class MailService:
    """Reserva la interfaz de correo sin implementar acceso a mensajes aún."""

    def __init__(self, client: GraphClient, mailbox: str) -> None:
        """Recibe sus dependencias sin acceder a Microsoft Graph."""
        self._client = client
        self._mailbox = mailbox

    def list_messages(self, *args: Any, **kwargs: Any) -> NoReturn:
        """Listará mensajes en una implementación futura."""
        raise NotImplementedError

    def get_message(self, *args: Any, **kwargs: Any) -> NoReturn:
        """Obtendrá un mensaje en una implementación futura."""
        raise NotImplementedError

    def send_mail(self, *args: Any, **kwargs: Any) -> NoReturn:
        """Enviará correo en una implementación futura."""
        raise NotImplementedError

    def download_attachment(self, *args: Any, **kwargs: Any) -> NoReturn:
        """Descargará un adjunto en una implementación futura."""
        raise NotImplementedError

    def move_message(self, *args: Any, **kwargs: Any) -> NoReturn:
        """Moverá un mensaje en una implementación futura."""
        raise NotImplementedError
