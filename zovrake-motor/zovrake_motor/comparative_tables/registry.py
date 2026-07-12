"""Registro extensible de componentes internos de Generación de Cuadros Comparativos."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.comparative_tables.components.base import ComparativeTablesComponentPort
from zovrake_motor.comparative_tables.components.comparative_model_builder import ComparativeModelBuilder
from zovrake_motor.comparative_tables.components.comparative_quality_framework import (
    ComparativeQualityFramework,
)
from zovrake_motor.comparative_tables.components.comparative_structure_engine import (
    ComparativeStructureEngine,
)
from zovrake_motor.comparative_tables.components.comparative_validation_framework import (
    ComparativeValidationFramework,
)
from zovrake_motor.comparative_tables.components.dynamic_column_builder import DynamicColumnBuilder
from zovrake_motor.comparative_tables.components.dynamic_row_builder import DynamicRowBuilder
from zovrake_motor.comparative_tables.components.group_integrity_engine import GroupIntegrityEngine
from zovrake_motor.comparative_tables.components.provider_organization_engine import (
    ProviderOrganizationEngine,
)
from zovrake_motor.comparative_tables.components.traceability_metadata_engine import (
    TraceabilityMetadataEngine,
)

if TYPE_CHECKING:
    from zovrake_motor.comparative_tables.components.comparative_tables_coordinator import (
        ComparativeTablesCoordinator,
    )
    from zovrake_motor.config.provider import ConfigurationProvider


class ComponentRegistry:
    """
    Registro de componentes del módulo de Generación de Cuadros Comparativos.

    Permite incorporar nuevos constructores y validadores mediante extensión
    sin modificar el núcleo.
    """

    def __init__(self) -> None:
        self._components: dict[str, ComparativeTablesComponentPort] = {}

    def register(self, component: ComparativeTablesComponentPort) -> None:
        self._components[component.component_name] = component

    def register_defaults(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
    ) -> ComparativeTablesCoordinator:
        """Registra la estructura base de componentes preparada para PM6."""
        from zovrake_motor.comparative_tables.components.comparative_tables_coordinator import (
            ComparativeTablesCoordinator,
        )

        components: tuple[ComparativeTablesComponentPort, ...] = (
            ComparativeStructureEngine(config_provider=config_provider),
            DynamicColumnBuilder(config_provider=config_provider),
            DynamicRowBuilder(config_provider=config_provider),
            ProviderOrganizationEngine(config_provider=config_provider),
            GroupIntegrityEngine(config_provider=config_provider),
            TraceabilityMetadataEngine(config_provider=config_provider),
            ComparativeModelBuilder(config_provider=config_provider),
            ComparativeValidationFramework(config_provider=config_provider),
            ComparativeQualityFramework(config_provider=config_provider),
        )

        for component in components:
            self.register(component)

        coordinator = ComparativeTablesCoordinator(self)
        self.register(coordinator)
        return coordinator

    def get(self, name: str) -> ComparativeTablesComponentPort | None:
        return self._components.get(name)

    def all_components(self) -> tuple[ComparativeTablesComponentPort, ...]:
        return tuple(self._components.values())

    def count(self) -> int:
        return len(self._components)

    def ready_count(self) -> int:
        return sum(1 for component in self._components.values() if component.is_ready())

    def snapshot(self) -> list[dict[str, Any]]:
        return [component.snapshot() for component in self._components.values()]
