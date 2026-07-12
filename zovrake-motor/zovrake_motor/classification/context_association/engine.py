"""Motor central del Context Association Engine (CAE-Context)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.classification.context_association.catalog import ContextAssociationCatalogStore
from zovrake_motor.classification.context_association.executor import ContextAssociationExecutor
from zovrake_motor.classification.context_association.gateway import ContextAssociationGateway
from zovrake_motor.classification.context_association.integration_hooks import (
    ComparativeDomainModelIntegrationPoint,
)
from zovrake_motor.classification.context_association.models import (
    ContextAssociationRequest,
    ContextAssociationResult,
)
from zovrake_motor.classification.context_association.port import ContextAssociatorPort
from zovrake_motor.classification.context_association.registry import ContextAssociatorRegistry
from zovrake_motor.config.categories.classification import ContextAssociationSettings

if TYPE_CHECKING:
    from zovrake_motor.config.provider import ConfigurationProvider


class ContextAssociationEngine:
    """
    Context Association Engine (CAE-Context).

    Asocia el contexto del requerimiento con cada Grupo Comparable.
    Ningún otro componente realiza esta función.
    """

    EXPECTED_ASSOCIATOR_COUNT = 1

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        registry: ContextAssociatorRegistry | None = None,
        gateway: ContextAssociationGateway | None = None,
        catalog_store: ContextAssociationCatalogStore | None = None,
    ) -> None:
        self._config_provider = config_provider
        self._registry = registry or ContextAssociatorRegistry()
        self._gateway = gateway or ContextAssociationGateway()
        self._catalog_store = catalog_store or ContextAssociationCatalogStore()
        self._executor: ContextAssociationExecutor | None = None
        self._domain_model_hook: ComparativeDomainModelIntegrationPoint | None = None
        self._initialized = False

    @property
    def registry(self) -> ContextAssociatorRegistry:
        return self._registry

    @property
    def catalog_store(self) -> ContextAssociationCatalogStore:
        return self._catalog_store

    @property
    def executor(self) -> ContextAssociationExecutor:
        if self._executor is None:
            self._executor = ContextAssociationExecutor(self._registry)
        return self._executor

    @property
    def comparative_domain_model_integration(self) -> ComparativeDomainModelIntegrationPoint:
        if self._domain_model_hook is None:
            self._domain_model_hook = ComparativeDomainModelIntegrationPoint(
                settings=self._context_association_settings(),
            )
        return self._domain_model_hook

    def is_ready(self) -> bool:
        return self._initialized and self._registry.count() >= self.EXPECTED_ASSOCIATOR_COUNT

    def initialize(self) -> None:
        settings = self._context_association_settings()
        if not self._registry.count():
            self._registry.register_defaults(settings=settings)
        self._executor = ContextAssociationExecutor(self._registry)
        self._domain_model_hook = ComparativeDomainModelIntegrationPoint(settings=settings)
        self._initialized = True

    def associate(self, request: ContextAssociationRequest) -> ContextAssociationResult:
        settings = self._context_association_settings()
        input_view = self._gateway.validate(
            request.comparable_group_catalog,
            request.integrated_context,
            process_id=request.process_id,
        )
        result = self.executor.execute(input_view, settings=settings)
        self._catalog_store.save(result.catalog)

        domain_status = self.comparative_domain_model_integration.prepare_for_future_modeling(
            result.catalog,
        )

        observations = (
            *result.technical_observations,
            f"comparative_domain_model_status={domain_status['status']}",
        )
        return ContextAssociationResult(
            process_id=result.process_id,
            document_id=result.document_id,
            model_id=result.model_id,
            catalog=result.catalog,
            status=result.status,
            incidents=result.incidents,
            comparable_group_catalog_preserved=result.comparable_group_catalog_preserved,
            context_preserved=result.context_preserved,
            associators_executed=result.associators_executed,
            technical_observations=observations,
        )

    def extend(self, associator: ContextAssociatorPort) -> None:
        self._registry.register(associator)

    def _context_association_settings(self) -> ContextAssociationSettings:
        if self._config_provider is not None:
            return self._config_provider.classification().context_association
        return ContextAssociationSettings.default()

    def snapshot(self) -> dict[str, Any]:
        settings = self._context_association_settings()
        return {
            "initialized": self._initialized,
            "associators_count": self._registry.count(),
            "associators": self._registry.snapshot(),
            "catalog_entries_count": self._catalog_store.count(),
            "gateway": self._gateway.snapshot(),
            "comparative_domain_model_integration": self.comparative_domain_model_integration.snapshot(),
            "configuration": {
                "enabled": settings.enabled,
                "preserve_catalog_immutability": settings.preserve_catalog_immutability,
                "preserve_context_immutability": settings.preserve_context_immutability,
                "uniform_group_context_associator_enabled": settings.uniform_group_context_associator_enabled,
                "comparative_domain_model_prepared": settings.comparative_domain_model_prepared,
            },
        }
