"""Motor central del Provider Organization Engine (POE)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.comparative_tables.provider_organization_engine.catalog import (
    OrganizedProviderCatalogStore,
)
from zovrake_motor.comparative_tables.provider_organization_engine.executor import (
    ProviderOrganizationExecutor,
)
from zovrake_motor.comparative_tables.provider_organization_engine.gateway import (
    ProviderOrganizationInputGateway,
)
from zovrake_motor.comparative_tables.provider_organization_engine.integration_hooks import (
    GroupIntegrityEngineIntegrationPoint,
)
from zovrake_motor.comparative_tables.provider_organization_engine.models import (
    ProviderOrganizationBuildRequest,
    ProviderOrganizationBuildResult,
)
from zovrake_motor.comparative_tables.provider_organization_engine.port import ProviderOrganizerPort
from zovrake_motor.comparative_tables.provider_organization_engine.registry import (
    ProviderOrganizerRegistry,
)
from zovrake_motor.config.categories.comparative_tables import ProviderOrganizationEngineSettings

if TYPE_CHECKING:
    from zovrake_motor.config.provider import ConfigurationProvider


class ProviderOrganizationEngineCore:
    """
    Provider Organization Engine (POE).

    Organiza proveedores a partir de los catálogos del CSE, DCB y DRB.
    Ningún otro componente organiza proveedores directamente.
    """

    EXPECTED_ORGANIZER_COUNT = 1

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        registry: ProviderOrganizerRegistry | None = None,
        gateway: ProviderOrganizationInputGateway | None = None,
        catalog_store: OrganizedProviderCatalogStore | None = None,
    ) -> None:
        self._config_provider = config_provider
        self._registry = registry or ProviderOrganizerRegistry()
        self._gateway = gateway or ProviderOrganizationInputGateway()
        self._catalog_store = catalog_store or OrganizedProviderCatalogStore()
        self._executor: ProviderOrganizationExecutor | None = None
        self._gie_hook: GroupIntegrityEngineIntegrationPoint | None = None
        self._initialized = False

    @property
    def registry(self) -> ProviderOrganizerRegistry:
        return self._registry

    @property
    def catalog_store(self) -> OrganizedProviderCatalogStore:
        return self._catalog_store

    @property
    def executor(self) -> ProviderOrganizationExecutor:
        if self._executor is None:
            self._executor = ProviderOrganizationExecutor(self._registry)
        return self._executor

    @property
    def group_integrity_integration(self) -> GroupIntegrityEngineIntegrationPoint:
        if self._gie_hook is None:
            self._gie_hook = GroupIntegrityEngineIntegrationPoint(
                settings=self._organization_settings(),
            )
        return self._gie_hook

    def is_ready(self) -> bool:
        return self._initialized and self._registry.count() >= self.EXPECTED_ORGANIZER_COUNT

    def initialize(self) -> None:
        settings = self._organization_settings()
        if not self._registry.count():
            self._registry.register_defaults(settings=settings)
        self._executor = ProviderOrganizationExecutor(self._registry)
        self._gie_hook = GroupIntegrityEngineIntegrationPoint(settings=settings)
        self._initialized = True

    def organize(
        self,
        request: ProviderOrganizationBuildRequest,
    ) -> ProviderOrganizationBuildResult:
        settings = self._organization_settings()
        input_view = self._gateway.validate(
            request.structure_catalog,
            request.column_catalog,
            request.row_catalog,
        )
        result = self.executor.execute(input_view, settings=settings)
        self._catalog_store.save(result.catalog)

        gie_status = self.group_integrity_integration.prepare_for_future_integrity_check(
            result.catalog,
        )
        observations = (
            *result.technical_observations,
            f"group_integrity_engine_status={gie_status['status']}",
        )
        return ProviderOrganizationBuildResult(
            process_id=result.process_id,
            document_id=result.document_id,
            model_id=result.model_id,
            catalog=result.catalog,
            status=result.status,
            incidents=result.incidents,
            column_catalog_preserved=result.column_catalog_preserved,
            structure_catalog_preserved=result.structure_catalog_preserved,
            row_catalog_preserved=result.row_catalog_preserved,
            domain_model_preserved=result.domain_model_preserved,
            organizers_executed=result.organizers_executed,
            technical_observations=observations,
        )

    def extend(self, organizer: ProviderOrganizerPort) -> None:
        """Incorpora un nuevo organizador mediante extensión sin modificar el núcleo."""
        self._registry.register(organizer)

    def _organization_settings(self) -> ProviderOrganizationEngineSettings:
        if self._config_provider is not None:
            return self._config_provider.comparative_tables().provider_organization_engine
        return ProviderOrganizationEngineSettings.default()

    def snapshot(self) -> dict[str, Any]:
        settings = self._organization_settings()
        return {
            "initialized": self._initialized,
            "organizers_count": self._registry.count(),
            "organizers": self._registry.snapshot(),
            "catalog_entries_count": self._catalog_store.count(),
            "gateway": self._gateway.snapshot(),
            "group_integrity_integration": self.group_integrity_integration.snapshot(),
            "configuration": {
                "enabled": settings.enabled,
                "preserve_catalog_immutability": settings.preserve_catalog_immutability,
                "group_provider_organizer_enabled": settings.group_provider_organizer_enabled,
                "organization_id_prefix": settings.organization_id_prefix,
                "organization_id_padding": settings.organization_id_padding,
                "organization_id_immutable": settings.organization_id_immutable,
                "deterministic_sort_enabled": settings.deterministic_sort_enabled,
                "group_integrity_engine_prepared": settings.group_integrity_engine_prepared,
            },
        }
