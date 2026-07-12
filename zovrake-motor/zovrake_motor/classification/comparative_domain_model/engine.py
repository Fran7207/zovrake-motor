"""Motor central del Comparative Domain Model Builder (CDMB)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.classification.comparative_domain_model.catalog import ComparativeDomainModelCatalogStore
from zovrake_motor.classification.comparative_domain_model.executor import ComparativeDomainModelBuildExecutor
from zovrake_motor.classification.comparative_domain_model.gateway import ContextAssociationCatalogGateway
from zovrake_motor.classification.comparative_domain_model.models import (
    ComparativeDomainModelBuildRequest,
    ComparativeDomainModelBuildResult,
)
from zovrake_motor.classification.comparative_domain_model.port import ComparativeDomainModelBuilderPort
from zovrake_motor.classification.comparative_domain_model.registry import DomainModelBuilderRegistry
from zovrake_motor.config.categories.classification import ComparativeDomainModelBuilderSettings

if TYPE_CHECKING:
    from zovrake_motor.config.provider import ConfigurationProvider


class ComparativeDomainModelBuilderEngine:
    """
    Comparative Domain Model Builder (CDMB).

    Construye el Modelo Comparativo de Dominio — salida oficial del PM5.
    Ningún otro componente construye este modelo.
    """

    EXPECTED_BUILDER_COUNT = 1

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        registry: DomainModelBuilderRegistry | None = None,
        gateway: ContextAssociationCatalogGateway | None = None,
        catalog_store: ComparativeDomainModelCatalogStore | None = None,
    ) -> None:
        self._config_provider = config_provider
        self._registry = registry or DomainModelBuilderRegistry()
        self._gateway = gateway or ContextAssociationCatalogGateway()
        self._catalog_store = catalog_store or ComparativeDomainModelCatalogStore()
        self._executor: ComparativeDomainModelBuildExecutor | None = None
        self._initialized = False

    @property
    def registry(self) -> DomainModelBuilderRegistry:
        return self._registry

    @property
    def catalog_store(self) -> ComparativeDomainModelCatalogStore:
        return self._catalog_store

    @property
    def executor(self) -> ComparativeDomainModelBuildExecutor:
        if self._executor is None:
            self._executor = ComparativeDomainModelBuildExecutor(self._registry)
        return self._executor

    def is_ready(self) -> bool:
        return self._initialized and self._registry.count() >= self.EXPECTED_BUILDER_COUNT

    def initialize(self) -> None:
        settings = self._comparative_domain_model_builder_settings()
        if not self._registry.count():
            self._registry.register_defaults(settings=settings)
        self._executor = ComparativeDomainModelBuildExecutor(self._registry)
        self._initialized = True

    def build(self, request: ComparativeDomainModelBuildRequest) -> ComparativeDomainModelBuildResult:
        settings = self._comparative_domain_model_builder_settings()
        catalog_view = self._gateway.validate(request.context_association_catalog)
        result = self.executor.execute(catalog_view, settings=settings)
        self._catalog_store.save(result.catalog)
        return result

    def extend(self, builder: ComparativeDomainModelBuilderPort) -> None:
        self._registry.register(builder)

    def _comparative_domain_model_builder_settings(self) -> ComparativeDomainModelBuilderSettings:
        if self._config_provider is not None:
            return self._config_provider.classification().comparative_domain_model_builder
        return ComparativeDomainModelBuilderSettings.default()

    def snapshot(self) -> dict[str, Any]:
        settings = self._comparative_domain_model_builder_settings()
        return {
            "initialized": self._initialized,
            "builders_count": self._registry.count(),
            "builders": self._registry.snapshot(),
            "catalog_entries_count": self._catalog_store.count(),
            "gateway": self._gateway.snapshot(),
            "configuration": {
                "enabled": settings.enabled,
                "preserve_catalog_immutability": settings.preserve_catalog_immutability,
                "group_context_aggregation_builder_enabled": settings.group_context_aggregation_builder_enabled,
                "model_id_prefix": settings.model_id_prefix,
                "model_id_padding": settings.model_id_padding,
                "model_id_immutable": settings.model_id_immutable,
                "default_confidence_level": settings.default_confidence_level,
                "pm6_output_contract": settings.pm6_output_contract,
            },
        }
