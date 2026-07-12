"""Configuración de registro de eventos del Motor Inteligente."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EventsSettings:
    """Registro de eventos internos del Motor."""

    logging_enabled: bool = True
    max_events_in_memory: int = 10_000

    @classmethod
    def default(cls) -> EventsSettings:
        return cls()
