"""Configuración de comportamiento del Motor Inteligente."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BehaviorSettings:
    """Comportamiento operativo — estructura preparada para extensiones futuras."""

    coordinator_enabled: bool = True
    strict_module_validation: bool = True

    @classmethod
    def default(cls) -> BehaviorSettings:
        return cls()
