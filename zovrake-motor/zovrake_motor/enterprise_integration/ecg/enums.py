"""Enumeraciones del ERP Communication Gateway."""

from __future__ import annotations

from enum import Enum


class EcgMessageType(str, Enum):
    """Tipos de mensajes gestionados por el ECG."""

    REQUEST = "request"
    RESPONSE = "response"
    ERROR = "error"
    NOTIFICATION = "notification"
    STATE_CHANGE = "state_change"


class EcgChannelDirection(str, Enum):
    """Dirección del flujo de comunicación."""

    ERP_TO_MOTOR = "erp_to_motor"
    MOTOR_TO_ERP = "motor_to_erp"


class EcgContractVersion(str, Enum):
    """Versión del contrato ECG ↔ Centro de Evidencias."""

    V1 = "v1"
