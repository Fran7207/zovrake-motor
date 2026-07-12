"""Módulo de Comunicación Motor ↔ ERP."""

from zovrake_motor.communication.models import OutboundMessage
from zovrake_motor.communication.port import CommunicationPort
from zovrake_motor.communication.service import CommunicationService

__all__ = [
    "CommunicationPort",
    "CommunicationService",
    "OutboundMessage",
]
