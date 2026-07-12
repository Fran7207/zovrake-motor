"""Adaptadores Documentales — integración con el Document Adapter Framework."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.comprehension.adapters.framework import DocumentAdapterFramework
from zovrake_motor.comprehension.components.base import ComprehensionComponentPort

if TYPE_CHECKING:
    from zovrake_motor.config.provider import ConfigurationProvider


class DocumentAdaptersManager(ComprehensionComponentPort):
    """
    Gestor del Document Adapter Framework dentro del módulo de Comprensión.

    Responsabilidad única: administrar el Framework de Adaptadores Documentales.
    """

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        framework: DocumentAdapterFramework | None = None,
    ) -> None:
        self._framework = framework or DocumentAdapterFramework(config_provider=config_provider)
        self._component_initialized = False

    @property
    def component_name(self) -> str:
        return "document_adapters"

    @property
    def component_label(self) -> str:
        return "Adaptadores Documentales"

    @property
    def framework(self) -> DocumentAdapterFramework:
        return self._framework

    def initialize(self) -> None:
        self._framework.initialize()
        self._component_initialized = True

    def is_ready(self) -> bool:
        return self._component_initialized and self._framework.is_ready()

    def snapshot(self) -> dict[str, Any]:
        base = super().snapshot()
        base["framework"] = self._framework.snapshot()
        return base
