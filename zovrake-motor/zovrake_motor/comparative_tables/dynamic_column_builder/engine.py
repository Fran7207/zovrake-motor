"""Motor central del Dynamic Column Builder (DCB)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.comparative_tables.dynamic_column_builder.catalog import (
    ComparativeTableColumnCatalogStore,
)
from zovrake_motor.comparative_tables.dynamic_column_builder.executor import DynamicColumnBuildExecutor
from zovrake_motor.comparative_tables.dynamic_column_builder.gateway import StructureCatalogGateway
from zovrake_motor.comparative_tables.dynamic_column_builder.integration_hooks import (
    DynamicRowBuilderIntegrationPoint,
)
from zovrake_motor.comparative_tables.dynamic_column_builder.models import (
    ComparativeColumnBuildRequest,
    ComparativeColumnBuildResult,
)
from zovrake_motor.comparative_tables.dynamic_column_builder.port import DynamicColumnBuilderPort
from zovrake_motor.comparative_tables.dynamic_column_builder.registry import ColumnBuilderRegistry
from zovrake_motor.config.categories.comparative_tables import DynamicColumnBuilderSettings

if TYPE_CHECKING:
    from zovrake_motor.config.provider import ConfigurationProvider


class DynamicColumnBuilderEngine:
    """
    Dynamic Column Builder (DCB).

    Construye columnas dinámicas a partir de las estructuras del CSE.
    Ningún otro componente crea columnas directamente.
    """

    EXPECTED_BUILDER_COUNT = 1

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        registry: ColumnBuilderRegistry | None = None,
        gateway: StructureCatalogGateway | None = None,
        catalog_store: ComparativeTableColumnCatalogStore | None = None,
    ) -> None:
        self._config_provider = config_provider
        self._registry = registry or ColumnBuilderRegistry()
        self._gateway = gateway or StructureCatalogGateway()
        self._catalog_store = catalog_store or ComparativeTableColumnCatalogStore()
        self._executor: DynamicColumnBuildExecutor | None = None
        self._row_hook: DynamicRowBuilderIntegrationPoint | None = None
        self._initialized = False

    @property
    def registry(self) -> ColumnBuilderRegistry:
        return self._registry

    @property
    def catalog_store(self) -> ComparativeTableColumnCatalogStore:
        return self._catalog_store

    @property
    def executor(self) -> DynamicColumnBuildExecutor:
        if self._executor is None:
            self._executor = DynamicColumnBuildExecutor(self._registry)
        return self._executor

    @property
    def dynamic_row_integration(self) -> DynamicRowBuilderIntegrationPoint:
        if self._row_hook is None:
            self._row_hook = DynamicRowBuilderIntegrationPoint(
                settings=self._column_builder_settings(),
            )
        return self._row_hook

    def is_ready(self) -> bool:
        return self._initialized and self._registry.count() >= self.EXPECTED_BUILDER_COUNT

    def initialize(self) -> None:
        settings = self._column_builder_settings()
        if not self._registry.count():
            self._registry.register_defaults(settings=settings)
        self._executor = DynamicColumnBuildExecutor(self._registry)
        self._row_hook = DynamicRowBuilderIntegrationPoint(settings=settings)
        self._initialized = True

    def build(self, request: ComparativeColumnBuildRequest) -> ComparativeColumnBuildResult:
        settings = self._column_builder_settings()
        catalog_view = self._gateway.validate(request.structure_catalog)
        result = self.executor.execute(catalog_view, settings=settings)
        self._catalog_store.save(result.catalog)

        row_status = self.dynamic_row_integration.prepare_for_future_rows(result.catalog)
        observations = (
            *result.technical_observations,
            f"dynamic_row_builder_status={row_status['status']}",
        )
        return ComparativeColumnBuildResult(
            process_id=result.process_id,
            document_id=result.document_id,
            model_id=result.model_id,
            catalog=result.catalog,
            status=result.status,
            incidents=result.incidents,
            structure_catalog_preserved=result.structure_catalog_preserved,
            domain_model_preserved=result.domain_model_preserved,
            builders_executed=result.builders_executed,
            technical_observations=observations,
        )

    def extend(self, builder: DynamicColumnBuilderPort) -> None:
        """Incorpora un nuevo constructor mediante extensión sin modificar el núcleo."""
        self._registry.register(builder)

    def _column_builder_settings(self) -> DynamicColumnBuilderSettings:
        if self._config_provider is not None:
            return self._config_provider.comparative_tables().dynamic_column_builder
        return DynamicColumnBuilderSettings.default()

    def snapshot(self) -> dict[str, Any]:
        settings = self._column_builder_settings()
        return {
            "initialized": self._initialized,
            "builders_count": self._registry.count(),
            "builders": self._registry.snapshot(),
            "catalog_entries_count": self._catalog_store.count(),
            "gateway": self._gateway.snapshot(),
            "dynamic_row_integration": self.dynamic_row_integration.snapshot(),
            "configuration": {
                "enabled": settings.enabled,
                "preserve_catalog_immutability": settings.preserve_catalog_immutability,
                "structure_attribute_column_builder_enabled": (
                    settings.structure_attribute_column_builder_enabled
                ),
                "column_id_prefix": settings.column_id_prefix,
                "column_id_padding": settings.column_id_padding,
                "column_id_immutable": settings.column_id_immutable,
                "dynamic_row_builder_prepared": settings.dynamic_row_builder_prepared,
            },
        }
