"""Context Association Engine — integración con el módulo de clasificación."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.classification.components.base import ClassificationComponentPort
from zovrake_motor.classification.context_association.engine import ContextAssociationEngine
from zovrake_motor.classification.context_association.integration import ContextAssociationMotorIntegration
from zovrake_motor.classification.context_association.models import (
    ContextAssociationRequest,
    ContextAssociationResult,
)

if TYPE_CHECKING:
    from zovrake_motor.classification.integration import ClassificationMotorIntegration
    from zovrake_motor.config.provider import ConfigurationProvider


class ContextAssociationEngineComponent(ClassificationComponentPort):
    """
    Gestor del Context Association Engine (CAE-Context).

    Responsabilidad única: asociar el contexto del requerimiento con cada Grupo Comparable.
    """

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        engine: ContextAssociationEngine | None = None,
    ) -> None:
        self._engine = engine or ContextAssociationEngine(config_provider=config_provider)
        self._component_initialized = False

    @property
    def component_name(self) -> str:
        return "context_association_engine"

    @property
    def component_label(self) -> str:
        return "Context Association Engine"

    @property
    def engine(self) -> ContextAssociationEngine:
        return self._engine

    def initialize(self) -> None:
        self._engine.initialize()
        self._component_initialized = True

    def is_ready(self) -> bool:
        return self._component_initialized and self._engine.is_ready()

    def associate(
        self,
        request: ContextAssociationRequest,
        *,
        integration: ClassificationMotorIntegration | None = None,
        record_traceability: bool = True,
    ) -> ContextAssociationResult:
        catalog_id = str(request.comparable_group_catalog.get("catalog_id", ""))
        document_id = str(request.comparable_group_catalog.get("document_id", ""))
        model_id = str(request.comparable_group_catalog.get("model_id", ""))

        if integration is not None and record_traceability:
            bridge = ContextAssociationMotorIntegration.from_classification_integration(integration)
            bridge.begin_context_association(
                request.process_id,
                document_id=document_id,
                model_id=model_id,
                comparable_group_catalog_id=catalog_id,
            )

        result = self._engine.associate(request)

        if integration is not None and record_traceability:
            bridge = ContextAssociationMotorIntegration.from_classification_integration(integration)
            bridge.complete_context_association(request.process_id, result)

        return result

    def snapshot(self) -> dict[str, Any]:
        base = super().snapshot()
        base["engine"] = self._engine.snapshot()
        return base
