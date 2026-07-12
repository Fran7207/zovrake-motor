"""Registro extensible de componentes internos de Comprensión Documental."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.comprehension.components.adapters import DocumentAdaptersManager
from zovrake_motor.comprehension.components.base import ComprehensionComponentPort
from zovrake_motor.comprehension.components.context_manager import DocumentContextManager
from zovrake_motor.comprehension.components.context_manager import DocumentContextManager
from zovrake_motor.comprehension.components.document_index import DocumentIndex
from zovrake_motor.comprehension.components.extractors import ExtractorsRegistry
from zovrake_motor.comprehension.components.format_identifier import FormatIdentifier
from zovrake_motor.comprehension.components.model_builder import InternalModelBuilder
from zovrake_motor.comprehension.components.normalizer import ContentNormalizer
from zovrake_motor.comprehension.components.quality_manager import DocumentQualityManager
from zovrake_motor.comprehension.components.traceability_manager import DocumentTraceabilityManager
from zovrake_motor.comprehension.components.validator import DocumentValidator

if TYPE_CHECKING:
    from zovrake_motor.comprehension.components.document_coordinator import DocumentCoordinator
    from zovrake_motor.config.provider import ConfigurationProvider


class ComponentRegistry:
    """
    Registro de componentes del módulo de Comprensión Documental.

    Permite incorporar nuevos componentes mediante extensión sin modificar el núcleo.
    """

    def __init__(self) -> None:
        self._components: dict[str, ComprehensionComponentPort] = {}

    def register(self, component: ComprehensionComponentPort) -> None:
        self._components[component.component_name] = component

    def register_defaults(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
    ) -> DocumentCoordinator:
        """Registra la estructura base de componentes preparada para PM4."""
        from zovrake_motor.comprehension.components.document_coordinator import DocumentCoordinator

        components: tuple[ComprehensionComponentPort, ...] = (
            DocumentValidator(config_provider=config_provider),
            DocumentAdaptersManager(config_provider=config_provider),
            FormatIdentifier(config_provider=config_provider),
            ExtractorsRegistry(config_provider=config_provider),
            ContentNormalizer(config_provider=config_provider),
            InternalModelBuilder(config_provider=config_provider),
            DocumentIndex(config_provider=config_provider),
            DocumentContextManager(config_provider=config_provider),
            DocumentQualityManager(),
            DocumentTraceabilityManager(),
        )

        for component in components:
            self.register(component)

        coordinator = DocumentCoordinator(self)
        self.register(coordinator)
        return coordinator

    def get(self, name: str) -> ComprehensionComponentPort | None:
        return self._components.get(name)

    def all_components(self) -> tuple[ComprehensionComponentPort, ...]:
        return tuple(self._components.values())

    def count(self) -> int:
        return len(self._components)

    def ready_count(self) -> int:
        return sum(1 for component in self._components.values() if component.is_ready())

    def snapshot(self) -> list[dict[str, Any]]:
        return [component.snapshot() for component in self._components.values()]
