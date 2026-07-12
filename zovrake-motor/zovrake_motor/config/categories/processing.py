"""Configuración de procesamiento del Motor Inteligente."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProcessingSettings:
    """Procesamiento documental — estructura preparada para etapas futuras."""

    enabled: bool = False
    max_concurrent_processes: int = 1

    @classmethod
    def default(cls) -> ProcessingSettings:
        return cls()
