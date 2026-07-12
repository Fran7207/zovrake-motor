"""Service Classification Engine (SCE) — integración con el módulo de clasificación."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.classification.components.base import ClassificationComponentPort
from zovrake_motor.classification.service_classification.engine import ServiceClassificationEngine
from zovrake_motor.classification.service_classification.integration import ServiceClassificationMotorIntegration
from zovrake_motor.classification.service_classification.models import (
    ServiceClassificationRequest,
    ServiceClassificationResult,
)

if TYPE_CHECKING:
    from zovrake_motor.classification.integration import ClassificationMotorIntegration
    from zovrake_motor.config.provider import ConfigurationProvider


class ServiceClassificationEngineComponent(ClassificationComponentPort):
    """
    Gestor del Service Classification Engine (SCE).

    Responsabilidad única: clasificar conceptos del CAE como servicios.
    """

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        engine: ServiceClassificationEngine | None = None,
    ) -> None:
        self._engine = engine or ServiceClassificationEngine(config_provider=config_provider)
        self._component_initialized = False

    @property
    def component_name(self) -> str:
        return "service_classification_engine"

    @property
    def component_label(self) -> str:
        return "Service Classification Engine"

    @property
    def engine(self) -> ServiceClassificationEngine:
        return self._engine

    def initialize(self) -> None:
        self._engine.initialize()
        self._component_initialized = True

    def is_ready(self) -> bool:
        return self._component_initialized and self._engine.is_ready()

    def classify(
        self,
        request: ServiceClassificationRequest,
        *,
        integration: ClassificationMotorIntegration | None = None,
        record_traceability: bool = True,
    ) -> ServiceClassificationResult:
        catalog_id = str(request.concept_catalog.get("catalog_id", ""))
        document_id = str(request.concept_catalog.get("document_id", ""))
        model_id = str(request.concept_catalog.get("model_id", ""))

        if integration is not None and record_traceability:
            bridge = ServiceClassificationMotorIntegration.from_classification_integration(integration)
            bridge.begin_service_classification(
                request.process_id,
                document_id=document_id,
                model_id=model_id,
                concept_catalog_id=catalog_id,
            )

        result = self._engine.classify(request)

        if integration is not None and record_traceability:
            bridge = ServiceClassificationMotorIntegration.from_classification_integration(integration)
            bridge.complete_service_classification(request.process_id, result)

        return result

    def snapshot(self) -> dict[str, Any]:
        base = super().snapshot()
        base["engine"] = self._engine.snapshot()
        return base
