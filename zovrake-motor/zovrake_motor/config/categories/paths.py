"""Configuración de rutas internas del Motor Inteligente."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PathsSettings:
    """Rutas internas — estructura preparada para uso futuro."""

    data_root: str = "data"
    temp_root: str = "tmp"
    logs_root: str = "logs"

    @classmethod
    def default(cls) -> PathsSettings:
        return cls()
