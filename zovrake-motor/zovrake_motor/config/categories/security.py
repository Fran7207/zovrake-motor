"""Configuración de seguridad del Motor Inteligente."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SecuritySettings:
    """Seguridad — estructura preparada para políticas futuras."""

    enabled: bool = True
    require_module_validation: bool = True

    @classmethod
    def default(cls) -> SecuritySettings:
        return cls()
