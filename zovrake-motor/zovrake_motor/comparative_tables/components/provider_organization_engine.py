"""Provider Organization Engine — integración con el módulo de cuadros comparativos."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.comparative_tables.components.base import ComparativeTablesComponentPort
from zovrake_motor.comparative_tables.provider_organization_engine.engine import (
    ProviderOrganizationEngineCore,
)
from zovrake_motor.comparative_tables.provider_organization_engine.integration import (
    ProviderOrganizationMotorIntegration,
)
from zovrake_motor.comparative_tables.provider_organization_engine.models import (
    ProviderOrganizationBuildRequest,
    ProviderOrganizationBuildResult,
)

if TYPE_CHECKING:
    from zovrake_motor.comparative_tables.integration import ComparativeTablesMotorIntegration
    from zovrake_motor.config.provider import ConfigurationProvider


class ProviderOrganizationEngine(ComparativeTablesComponentPort):
    """
    Gestor del Provider Organization Engine (POE).

    Responsabilidad única: organizar proveedores dentro de cuadros comparativos.
    """

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        engine: ProviderOrganizationEngineCore | None = None,
    ) -> None:
        self._engine = engine or ProviderOrganizationEngineCore(config_provider=config_provider)
        self._component_initialized = False

    @property
    def component_name(self) -> str:
        return "provider_organization_engine"

    @property
    def component_label(self) -> str:
        return "Provider Organization Engine"

    @property
    def engine(self) -> ProviderOrganizationEngineCore:
        return self._engine

    def initialize(self) -> None:
        self._engine.initialize()
        self._component_initialized = True

    def is_ready(self) -> bool:
        return self._component_initialized and self._engine.is_ready()

    def organize(
        self,
        request: ProviderOrganizationBuildRequest,
        *,
        integration: ComparativeTablesMotorIntegration | None = None,
        record_traceability: bool = True,
    ) -> ProviderOrganizationBuildResult:
        structure_catalog_id = str(request.structure_catalog.get("catalog_id", ""))
        column_catalog_id = str(request.column_catalog.get("catalog_id", ""))
        row_catalog_id = str(request.row_catalog.get("catalog_id", ""))
        document_id = str(request.row_catalog.get("document_id", ""))
        model_id = str(request.row_catalog.get("model_id", ""))

        if integration is not None and record_traceability:
            bridge = ProviderOrganizationMotorIntegration.from_comparative_tables_integration(
                integration,
            )
            bridge.begin_provider_organization(
                request.process_id,
                document_id=document_id,
                model_id=model_id,
                row_catalog_id=row_catalog_id,
                structure_catalog_id=structure_catalog_id,
                column_catalog_id=column_catalog_id,
            )

        result = self._engine.organize(request)

        if integration is not None and record_traceability:
            bridge = ProviderOrganizationMotorIntegration.from_comparative_tables_integration(
                integration,
            )
            bridge.complete_provider_organization(request.process_id, result)

        return result

    def snapshot(self) -> dict[str, Any]:
        base = super().snapshot()
        base["engine"] = self._engine.snapshot()
        return base
