"""Motor central del Comparative Structure Engine (CSE)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.comparative_tables.comparative_structure_engine.catalog import (
    ComparativeTableStructureCatalogStore,
)
from zovrake_motor.comparative_tables.comparative_structure_engine.executor import (
    ComparativeStructureBuildExecutor,
)
from zovrake_motor.comparative_tables.comparative_structure_engine.gateway import (
    DomainModelCatalogGateway,
)
from zovrake_motor.comparative_tables.comparative_structure_engine.integration_hooks import (
    DynamicColumnBuilderIntegrationPoint,
    DynamicRowBuilderIntegrationPoint,
)
from zovrake_motor.comparative_tables.comparative_structure_engine.models import (
    ComparativeStructureBuildRequest,
    ComparativeStructureBuildResult,
)
from zovrake_motor.comparative_tables.comparative_structure_engine.port import (
    ComparativeStructureBuilderPort,
)
from zovrake_motor.comparative_tables.comparative_structure_engine.registry import (
    StructureBuilderRegistry,
)
from zovrake_motor.config.categories.comparative_tables import ComparativeStructureEngineSettings

if TYPE_CHECKING:
    from zovrake_motor.config.provider import ConfigurationProvider


class ComparativeStructureBuilderEngine:
    """
    Comparative Structure Engine (CSE).

    Construye la estructura base de cada Cuadro Comparativo a partir del
    Modelo Comparativo de Dominio. Ningún otro componente construye esta estructura.
    """

    EXPECTED_BUILDER_COUNT = 1

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        registry: StructureBuilderRegistry | None = None,
        gateway: DomainModelCatalogGateway | None = None,
        catalog_store: ComparativeTableStructureCatalogStore | None = None,
    ) -> None:
        self._config_provider = config_provider
        self._registry = registry or StructureBuilderRegistry()
        self._gateway = gateway or DomainModelCatalogGateway()
        self._catalog_store = catalog_store or ComparativeTableStructureCatalogStore()
        self._executor: ComparativeStructureBuildExecutor | None = None
        self._column_hook: DynamicColumnBuilderIntegrationPoint | None = None
        self._row_hook: DynamicRowBuilderIntegrationPoint | None = None
        self._initialized = False

    @property
    def registry(self) -> StructureBuilderRegistry:
        return self._registry

    @property
    def catalog_store(self) -> ComparativeTableStructureCatalogStore:
        return self._catalog_store

    @property
    def executor(self) -> ComparativeStructureBuildExecutor:
        if self._executor is None:
            self._executor = ComparativeStructureBuildExecutor(self._registry)
        return self._executor

    @property
    def dynamic_column_integration(self) -> DynamicColumnBuilderIntegrationPoint:
        if self._column_hook is None:
            self._column_hook = DynamicColumnBuilderIntegrationPoint(
                settings=self._structure_engine_settings(),
            )
        return self._column_hook

    @property
    def dynamic_row_integration(self) -> DynamicRowBuilderIntegrationPoint:
        if self._row_hook is None:
            self._row_hook = DynamicRowBuilderIntegrationPoint(
                settings=self._structure_engine_settings(),
            )
        return self._row_hook

    def is_ready(self) -> bool:
        return self._initialized and self._registry.count() >= self.EXPECTED_BUILDER_COUNT

    def initialize(self) -> None:
        settings = self._structure_engine_settings()
        if not self._registry.count():
            self._registry.register_defaults(settings=settings)
        self._executor = ComparativeStructureBuildExecutor(self._registry)
        self._column_hook = DynamicColumnBuilderIntegrationPoint(settings=settings)
        self._row_hook = DynamicRowBuilderIntegrationPoint(settings=settings)
        self._initialized = True

    def build(self, request: ComparativeStructureBuildRequest) -> ComparativeStructureBuildResult:
        settings = self._structure_engine_settings()
        catalog_view = self._gateway.validate(request.domain_model_catalog)
        result = self.executor.execute(catalog_view, settings=settings)
        self._catalog_store.save(result.catalog)

        column_status = self.dynamic_column_integration.prepare_for_future_columns(result.catalog)
        row_status = self.dynamic_row_integration.prepare_for_future_rows(result.catalog)

        observations = (
            *result.technical_observations,
            f"dynamic_column_builder_status={column_status['status']}",
            f"dynamic_row_builder_status={row_status['status']}",
        )
        return ComparativeStructureBuildResult(
            process_id=result.process_id,
            document_id=result.document_id,
            model_id=result.model_id,
            catalog=result.catalog,
            status=result.status,
            incidents=result.incidents,
            domain_model_preserved=result.domain_model_preserved,
            builders_executed=result.builders_executed,
            technical_observations=observations,
        )

    def extend(self, builder: ComparativeStructureBuilderPort) -> None:
        """Incorpora un nuevo constructor mediante extensión sin modificar el núcleo."""
        self._registry.register(builder)

    def _structure_engine_settings(self) -> ComparativeStructureEngineSettings:
        if self._config_provider is not None:
            return self._config_provider.comparative_tables().comparative_structure_engine
        return ComparativeStructureEngineSettings.default()

    def snapshot(self) -> dict[str, Any]:
        settings = self._structure_engine_settings()
        return {
            "initialized": self._initialized,
            "builders_count": self._registry.count(),
            "builders": self._registry.snapshot(),
            "catalog_entries_count": self._catalog_store.count(),
            "gateway": self._gateway.snapshot(),
            "dynamic_column_integration": self.dynamic_column_integration.snapshot(),
            "dynamic_row_integration": self.dynamic_row_integration.snapshot(),
            "configuration": {
                "enabled": settings.enabled,
                "preserve_catalog_immutability": settings.preserve_catalog_immutability,
                "domain_model_group_structure_builder_enabled": (
                    settings.domain_model_group_structure_builder_enabled
                ),
                "structure_id_prefix": settings.structure_id_prefix,
                "structure_id_padding": settings.structure_id_padding,
                "structure_id_immutable": settings.structure_id_immutable,
                "dynamic_column_builder_prepared": settings.dynamic_column_builder_prepared,
                "dynamic_row_builder_prepared": settings.dynamic_row_builder_prepared,
            },
        }
