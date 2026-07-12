"""Motor central del Comparable Group Builder (CGB)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.classification.comparable_group_builder.catalog import ComparableGroupCatalogStore
from zovrake_motor.classification.comparable_group_builder.executor import ComparableGroupBuildExecutor
from zovrake_motor.classification.comparable_group_builder.gateway import EquivalenceCatalogGateway
from zovrake_motor.classification.comparable_group_builder.integration_hooks import (
    ComparativeDomainModelIntegrationPoint,
    ContextAssociationIntegrationPoint,
)
from zovrake_motor.classification.comparable_group_builder.models import (
    ComparableGroupBuildRequest,
    ComparableGroupBuildResult,
)
from zovrake_motor.classification.comparable_group_builder.port import ComparableGroupBuilderPort
from zovrake_motor.classification.comparable_group_builder.registry import GroupBuilderRegistry
from zovrake_motor.config.categories.classification import ComparableGroupBuilderSettings

if TYPE_CHECKING:
    from zovrake_motor.config.provider import ConfigurationProvider


class ComparableGroupBuilderEngine:
    """
    Comparable Group Builder (CGB).

    Construye Grupos Comparables a partir del Modelo de Equivalencias.
    Ningún otro componente construye grupos comparables directamente.
    """

    EXPECTED_BUILDER_COUNT = 1

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        registry: GroupBuilderRegistry | None = None,
        gateway: EquivalenceCatalogGateway | None = None,
        catalog_store: ComparableGroupCatalogStore | None = None,
    ) -> None:
        self._config_provider = config_provider
        self._registry = registry or GroupBuilderRegistry()
        self._gateway = gateway or EquivalenceCatalogGateway()
        self._catalog_store = catalog_store or ComparableGroupCatalogStore()
        self._executor: ComparableGroupBuildExecutor | None = None
        self._context_hook: ContextAssociationIntegrationPoint | None = None
        self._domain_model_hook: ComparativeDomainModelIntegrationPoint | None = None
        self._initialized = False

    @property
    def registry(self) -> GroupBuilderRegistry:
        return self._registry

    @property
    def catalog_store(self) -> ComparableGroupCatalogStore:
        return self._catalog_store

    @property
    def executor(self) -> ComparableGroupBuildExecutor:
        if self._executor is None:
            self._executor = ComparableGroupBuildExecutor(self._registry)
        return self._executor

    @property
    def context_association_integration(self) -> ContextAssociationIntegrationPoint:
        if self._context_hook is None:
            self._context_hook = ContextAssociationIntegrationPoint(
                settings=self._comparable_group_builder_settings(),
            )
        return self._context_hook

    @property
    def comparative_domain_model_integration(self) -> ComparativeDomainModelIntegrationPoint:
        if self._domain_model_hook is None:
            self._domain_model_hook = ComparativeDomainModelIntegrationPoint(
                settings=self._comparable_group_builder_settings(),
            )
        return self._domain_model_hook

    def is_ready(self) -> bool:
        return self._initialized and self._registry.count() >= self.EXPECTED_BUILDER_COUNT

    def initialize(self) -> None:
        settings = self._comparable_group_builder_settings()
        if not self._registry.count():
            self._registry.register_defaults(settings=settings)
        self._executor = ComparableGroupBuildExecutor(self._registry)
        self._context_hook = ContextAssociationIntegrationPoint(settings=settings)
        self._domain_model_hook = ComparativeDomainModelIntegrationPoint(settings=settings)
        self._initialized = True

    def build(self, request: ComparableGroupBuildRequest) -> ComparableGroupBuildResult:
        settings = self._comparable_group_builder_settings()
        catalog_view = self._gateway.validate(request.equivalence_catalog)
        result = self.executor.execute(catalog_view, settings=settings)
        self._catalog_store.save(result.catalog)

        context_status = self.context_association_integration.prepare_for_future_association(
            result.catalog,
        )
        domain_status = self.comparative_domain_model_integration.prepare_for_future_modeling(
            result.catalog,
        )

        observations = (
            *result.technical_observations,
            f"context_association_status={context_status['status']}",
            f"comparative_domain_model_status={domain_status['status']}",
        )
        return ComparableGroupBuildResult(
            process_id=result.process_id,
            document_id=result.document_id,
            model_id=result.model_id,
            catalog=result.catalog,
            status=result.status,
            incidents=result.incidents,
            equivalence_catalog_preserved=result.equivalence_catalog_preserved,
            builders_executed=result.builders_executed,
            technical_observations=observations,
        )

    def extend(self, builder: ComparableGroupBuilderPort) -> None:
        """Incorpora un nuevo constructor mediante extensión sin modificar el núcleo."""
        self._registry.register(builder)

    def _comparable_group_builder_settings(self) -> ComparableGroupBuilderSettings:
        if self._config_provider is not None:
            return self._config_provider.classification().comparable_group_builder
        return ComparableGroupBuilderSettings.default()

    def snapshot(self) -> dict[str, Any]:
        settings = self._comparable_group_builder_settings()
        return {
            "initialized": self._initialized,
            "builders_count": self._registry.count(),
            "builders": self._registry.snapshot(),
            "catalog_entries_count": self._catalog_store.count(),
            "gateway": self._gateway.snapshot(),
            "context_association_integration": self.context_association_integration.snapshot(),
            "comparative_domain_model_integration": self.comparative_domain_model_integration.snapshot(),
            "configuration": {
                "enabled": settings.enabled,
                "preserve_catalog_immutability": settings.preserve_catalog_immutability,
                "equivalence_cluster_builder_enabled": settings.equivalence_cluster_builder_enabled,
                "group_id_prefix": settings.group_id_prefix,
                "group_id_padding": settings.group_id_padding,
                "group_id_immutable": settings.group_id_immutable,
                "context_association_prepared": settings.context_association_prepared,
                "comparative_domain_model_prepared": settings.comparative_domain_model_prepared,
            },
        }
