"""Motor central del Dynamic Row Builder (DRB)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.comparative_tables.dynamic_row_builder.catalog import (
    ComparativeTableRowCatalogStore,
)
from zovrake_motor.comparative_tables.dynamic_row_builder.executor import DynamicRowBuildExecutor
from zovrake_motor.comparative_tables.dynamic_row_builder.gateway import RowBuildInputGateway
from zovrake_motor.comparative_tables.dynamic_row_builder.integration_hooks import (
    ProviderOrganizationEngineIntegrationPoint,
)
from zovrake_motor.comparative_tables.dynamic_row_builder.models import (
    ComparativeRowBuildRequest,
    ComparativeRowBuildResult,
)
from zovrake_motor.comparative_tables.dynamic_row_builder.port import DynamicRowBuilderPort
from zovrake_motor.comparative_tables.dynamic_row_builder.registry import RowBuilderRegistry
from zovrake_motor.config.categories.comparative_tables import DynamicRowBuilderSettings

if TYPE_CHECKING:
    from zovrake_motor.config.provider import ConfigurationProvider


class DynamicRowBuilderEngine:
    """
    Dynamic Row Builder (DRB).

    Construye filas dinámicas a partir de los catálogos del CSE y el DCB.
    Ningún otro componente crea filas directamente.
    """

    EXPECTED_BUILDER_COUNT = 1

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        registry: RowBuilderRegistry | None = None,
        gateway: RowBuildInputGateway | None = None,
        catalog_store: ComparativeTableRowCatalogStore | None = None,
    ) -> None:
        self._config_provider = config_provider
        self._registry = registry or RowBuilderRegistry()
        self._gateway = gateway or RowBuildInputGateway()
        self._catalog_store = catalog_store or ComparativeTableRowCatalogStore()
        self._executor: DynamicRowBuildExecutor | None = None
        self._poe_hook: ProviderOrganizationEngineIntegrationPoint | None = None
        self._initialized = False

    @property
    def registry(self) -> RowBuilderRegistry:
        return self._registry

    @property
    def catalog_store(self) -> ComparativeTableRowCatalogStore:
        return self._catalog_store

    @property
    def executor(self) -> DynamicRowBuildExecutor:
        if self._executor is None:
            self._executor = DynamicRowBuildExecutor(self._registry)
        return self._executor

    @property
    def provider_organization_integration(self) -> ProviderOrganizationEngineIntegrationPoint:
        if self._poe_hook is None:
            self._poe_hook = ProviderOrganizationEngineIntegrationPoint(
                settings=self._row_builder_settings(),
            )
        return self._poe_hook

    def is_ready(self) -> bool:
        return self._initialized and self._registry.count() >= self.EXPECTED_BUILDER_COUNT

    def initialize(self) -> None:
        settings = self._row_builder_settings()
        if not self._registry.count():
            self._registry.register_defaults(settings=settings)
        self._executor = DynamicRowBuildExecutor(self._registry)
        self._poe_hook = ProviderOrganizationEngineIntegrationPoint(settings=settings)
        self._initialized = True

    def build(self, request: ComparativeRowBuildRequest) -> ComparativeRowBuildResult:
        settings = self._row_builder_settings()
        input_view = self._gateway.validate(
            request.column_catalog,
            request.structure_catalog,
        )
        result = self.executor.execute(input_view, settings=settings)
        self._catalog_store.save(result.catalog)

        poe_status = self.provider_organization_integration.prepare_for_future_organization(
            result.catalog,
        )
        observations = (
            *result.technical_observations,
            f"provider_organization_engine_status={poe_status['status']}",
        )
        return ComparativeRowBuildResult(
            process_id=result.process_id,
            document_id=result.document_id,
            model_id=result.model_id,
            catalog=result.catalog,
            status=result.status,
            incidents=result.incidents,
            column_catalog_preserved=result.column_catalog_preserved,
            structure_catalog_preserved=result.structure_catalog_preserved,
            domain_model_preserved=result.domain_model_preserved,
            builders_executed=result.builders_executed,
            technical_observations=observations,
        )

    def extend(self, builder: DynamicRowBuilderPort) -> None:
        """Incorpora un nuevo constructor mediante extensión sin modificar el núcleo."""
        self._registry.register(builder)

    def _row_builder_settings(self) -> DynamicRowBuilderSettings:
        if self._config_provider is not None:
            return self._config_provider.comparative_tables().dynamic_row_builder
        return DynamicRowBuilderSettings.default()

    def snapshot(self) -> dict[str, Any]:
        settings = self._row_builder_settings()
        return {
            "initialized": self._initialized,
            "builders_count": self._registry.count(),
            "builders": self._registry.snapshot(),
            "catalog_entries_count": self._catalog_store.count(),
            "gateway": self._gateway.snapshot(),
            "provider_organization_integration": self.provider_organization_integration.snapshot(),
            "configuration": {
                "enabled": settings.enabled,
                "preserve_catalog_immutability": settings.preserve_catalog_immutability,
                "provider_row_builder_enabled": settings.provider_row_builder_enabled,
                "row_id_prefix": settings.row_id_prefix,
                "row_id_padding": settings.row_id_padding,
                "row_id_immutable": settings.row_id_immutable,
                "provider_organization_engine_prepared": settings.provider_organization_engine_prepared,
            },
        }
