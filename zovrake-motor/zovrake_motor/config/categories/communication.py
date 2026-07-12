"""Configuración de comunicación del Motor Inteligente."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CommunicationSettings:
    """Comunicación Motor ↔ ERP — estructura sin integración activa."""

    enabled: bool = True
    protocol: str = "internal"

    @classmethod
    def default(cls) -> CommunicationSettings:
        return cls()
