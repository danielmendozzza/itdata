"""Infraestructura base para integraciones con Microsoft Graph."""

from .auth import GraphAuth
from .graph import GraphClient
from .mail import MailService

__all__ = ["GraphAuth", "GraphClient", "MailService"]
