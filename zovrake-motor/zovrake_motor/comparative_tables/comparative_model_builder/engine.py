"""Motor central del Comparative Model Builder (CMB)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.comparative_tables.comparative_model_builder.catalog_store import (
    DefinitiveComparativeModelCatalogStore,
)
from zovrake_motor.comparative_tables.comparative_model_builder.executor import (
    ComparativeModelBuildExecutor,
)
from zovrake_motor.comparative_tables.comparative_model_builder.gateway import ModelBuildInputGateway
from zovrake_motor.comparative_tables.comparative_model_builder.integration_hooks import (
    ComparativeValidationFrameworkIntegrationPoint,
)
from zovrake_motor.comparative_tables.comparative_model_builder.models import (
    ComparativeModelBuildRequest,
    ComparativeModelBuildResult,
)
from zovrake_motor.comparative_tables.comparative_model_builder.port import ModelBuilderPort
from zovrake_motor.comparative_tables.comparative_model_builder.registry import ModelBuilderRegistry
from zovrake_motor.config.categories.comparative_tables import ComparativeModelBuilderSettings

if TYPE_CHECKING:
    from zovrake_motor.config.provider import ConfigurationProvider


class ComparativeModelBuilderEngine:
    """
    Comparative Model Builder (CMB).

    Construye el Modelo Comparativo Definitivo — contrato oficial de salida del PM6.
    """

    EXPECTED_BUILDER_COUNT = 1

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        registry: ModelBuilderRegistry | None = None,
        gateway: ModelBuildInputGateway | None = None,
        catalog_store: DefinitiveComparativeModelCatalogStore | None = None,
    ) -> None:
        self._config_provider = config_provider
        self._registry = registry or ModelBuilderRegistry()
        self._gateway = gateway or ModelBuildInputGateway()
        self._catalog_store = catalog_store or DefinitiveComparativeModelCatalogStore()
        self._executor: ComparativeModelBuildExecutor | None = None
        self._cvf_hook: ComparativeValidationFrameworkIntegrationPoint | None = None
        self._initialized = False

    @property
    def registry(self) -> ModelBuilderRegistry:
        return self._registry

    @property
    def catalog_store(self) -> DefinitiveComparativeModelCatalogStore:
        return self._catalog_store

    @property
    def executor(self) -> ComparativeModelBuildExecutor:
        if self._executor is None:
            self._executor = ComparativeModelBuildExecutor(self._registry)
        return self._executor

    @property
    def validation_framework_integration(self) -> ComparativeValidationFrameworkIntegrationPoint:
        if self._cvf_hook is None:
            self._cvf_hook = ComparativeValidationFrameworkIntegrationPoint(
                settings=self._builder_settings(),
            )
        return self._cvf_hook

    def is_ready(self) -> bool:
        return self._initialized and self._registry.count() >= self.EXPECTED_BUILDER_COUNT

    def initialize(self) -> None:
        settings = self._builder_settings()
        if not self._registry.count():
            self._registry.register_defaults(settings=settings)
        self._executor = ComparativeModelBuildExecutor(self._registry)
        self._cvf_hook = ComparativeValidationFrameworkIntegrationPoint(settings=settings)
        self._initialized = True

    def build(
        self,
        request: ComparativeModelBuildRequest,
    ) -> ComparativeModelBuildResult:
        settings = self._builder_settings()
        input_view = self._gateway.validate(
            request.enriched_catalog,
            request.structure_catalog,
            request.column_catalog,
            request.row_catalog,
            request.provider_catalog,
            request.integrity_report,
        )
        result = self.executor.execute(input_view, settings=settings)
        self._catalog_store.save(result.catalog)

        cvf_status = self.validation_framework_integration.prepare_for_future_validation(
            result.catalog,
        )
        observations = (
            *result.technical_observations,
            f"comparative_validation_framework_status={cvf_status['status']}",
        )
        return ComparativeModelBuildResult(
            process_id=result.process_id,
            document_id=result.document_id,
            model_id=result.model_id,
            catalog=result.catalog,
            status=result.status,
            models_built_count=result.models_built_count,
            enriched_catalog_preserved=result.enriched_catalog_preserved,
            structure_catalog_preserved=result.structure_catalog_preserved,
            column_catalog_preserved=result.column_catalog_preserved,
            row_catalog_preserved=result.row_catalog_preserved,
            provider_catalog_preserved=result.provider_catalog_preserved,
            integrity_report_preserved=result.integrity_report_preserved,
            domain_model_preserved=result.domain_model_preserved,
            builders_executed=result.builders_executed,
            technical_observations=observations,
        )

    def extend(self, builder: ModelBuilderPort) -> None:
        """Incorpora un nuevo constructor mediante extensión sin modificar el núcleo."""
        self._registry.register(builder)

    def _builder_settings(self) -> ComparativeModelBuilderSettings:
        if self._config_provider is not None:
            return self._config_provider.comparative_tables().comparative_model_builder
        return ComparativeModelBuilderSettings.default()

    def snapshot(self) -> dict[str, Any]:
        settings = self._builder_settings()
        return {
            "initialized": self._initialized,
            "builders_count": self._registry.count(),
            "builders": self._registry.snapshot(),
            "catalog_entries_count": self._catalog_store.count(),
            "gateway": self._gateway.snapshot(),
            "validation_framework_integration": self.validation_framework_integration.snapshot(),
            "configuration": {
                "enabled": settings.enabled,
                "preserve_catalog_immutability": settings.preserve_catalog_immutability,
                "group_comparative_model_builder_enabled": (
                    settings.group_comparative_model_builder_enabled
                ),
                "definitive_model_id_prefix": settings.definitive_model_id_prefix,
                "definitive_model_id_padding": settings.definitive_model_id_padding,
                "comparative_validation_framework_prepared": (
                    settings.comparative_validation_framework_prepared
                ),
            },
        }
