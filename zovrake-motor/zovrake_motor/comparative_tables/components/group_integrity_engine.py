"""Group Integrity Engine — integración con el módulo de cuadros comparativos."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.comparative_tables.components.base import ComparativeTablesComponentPort
from zovrake_motor.comparative_tables.group_integrity_engine.engine import GroupIntegrityEngineCore
from zovrake_motor.comparative_tables.group_integrity_engine.integration import (
    GroupIntegrityMotorIntegration,
)
from zovrake_motor.comparative_tables.group_integrity_engine.models import (
    GroupIntegrityValidationRequest,
    GroupIntegrityValidationResult,
)

if TYPE_CHECKING:
    from zovrake_motor.comparative_tables.integration import ComparativeTablesMotorIntegration
    from zovrake_motor.config.provider import ConfigurationProvider


class GroupIntegrityEngine(ComparativeTablesComponentPort):
    """
    Gestor del Group Integrity Engine (GIE).

    Responsabilidad única: validar integridad estructural de cuadros comparativos.
    """

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        engine: GroupIntegrityEngineCore | None = None,
    ) -> None:
        self._engine = engine or GroupIntegrityEngineCore(config_provider=config_provider)
        self._component_initialized = False

    @property
    def component_name(self) -> str:
        return "group_integrity_engine"

    @property
    def component_label(self) -> str:
        return "Group Integrity Engine"

    @property
    def engine(self) -> GroupIntegrityEngineCore:
        return self._engine

    def initialize(self) -> None:
        self._engine.initialize()
        self._component_initialized = True

    def is_ready(self) -> bool:
        return self._component_initialized and self._engine.is_ready()

    def validate(
        self,
        request: GroupIntegrityValidationRequest,
        *,
        integration: ComparativeTablesMotorIntegration | None = None,
        record_traceability: bool = True,
    ) -> GroupIntegrityValidationResult:
        provider_catalog_id = str(request.provider_catalog.get("catalog_id", ""))
        document_id = str(request.provider_catalog.get("document_id", ""))
        model_id = str(request.provider_catalog.get("model_id", ""))

        if integration is not None and record_traceability:
            bridge = GroupIntegrityMotorIntegration.from_comparative_tables_integration(
                integration,
            )
            bridge.begin_group_integrity_validation(
                request.process_id,
                document_id=document_id,
                model_id=model_id,
                provider_catalog_id=provider_catalog_id,
            )

        result = self._engine.validate(request)

        if integration is not None and record_traceability:
            bridge = GroupIntegrityMotorIntegration.from_comparative_tables_integration(
                integration,
            )
            bridge.complete_group_integrity_validation(request.process_id, result)

        return result

    def snapshot(self) -> dict[str, Any]:
        base = super().snapshot()
        base["engine"] = self._engine.snapshot()
        return base
