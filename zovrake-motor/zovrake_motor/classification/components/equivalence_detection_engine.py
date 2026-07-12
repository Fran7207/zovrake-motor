"""Equivalence Detection Engine (EDE) — integración con el módulo de clasificación."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.classification.components.base import ClassificationComponentPort
from zovrake_motor.classification.equivalence_detection.engine import EquivalenceDetectionEngine
from zovrake_motor.classification.equivalence_detection.integration import EquivalenceDetectionMotorIntegration
from zovrake_motor.classification.equivalence_detection.models import (
    EquivalenceDetectionRequest,
    EquivalenceDetectionResult,
)

if TYPE_CHECKING:
    from zovrake_motor.classification.integration import ClassificationMotorIntegration
    from zovrake_motor.config.provider import ConfigurationProvider


class EquivalenceDetectionEngineComponent(ClassificationComponentPort):
    """
    Gestor del Equivalence Detection Engine (EDE).

    Responsabilidad única: detectar equivalencias entre conceptos normalizados.
    """

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        engine: EquivalenceDetectionEngine | None = None,
    ) -> None:
        self._engine = engine or EquivalenceDetectionEngine(config_provider=config_provider)
        self._component_initialized = False

    @property
    def component_name(self) -> str:
        return "equivalence_detection_engine"

    @property
    def component_label(self) -> str:
        return "Equivalence Detection Engine"

    @property
    def engine(self) -> EquivalenceDetectionEngine:
        return self._engine

    def initialize(self) -> None:
        self._engine.initialize()
        self._component_initialized = True

    def is_ready(self) -> bool:
        return self._component_initialized and self._engine.is_ready()

    def detect(
        self,
        request: EquivalenceDetectionRequest,
        *,
        integration: ClassificationMotorIntegration | None = None,
        record_traceability: bool = True,
    ) -> EquivalenceDetectionResult:
        catalog_id = str(request.normalized_catalog.get("catalog_id", ""))
        document_id = str(request.normalized_catalog.get("document_id", ""))
        model_id = str(request.normalized_catalog.get("model_id", ""))

        if integration is not None and record_traceability:
            bridge = EquivalenceDetectionMotorIntegration.from_classification_integration(integration)
            bridge.begin_equivalence_detection(
                request.process_id,
                document_id=document_id,
                model_id=model_id,
                normalized_catalog_id=catalog_id,
            )

        result = self._engine.detect(request)

        if integration is not None and record_traceability:
            bridge = EquivalenceDetectionMotorIntegration.from_classification_integration(integration)
            bridge.complete_equivalence_detection(request.process_id, result)

        return result

    def snapshot(self) -> dict[str, Any]:
        base = super().snapshot()
        base["engine"] = self._engine.snapshot()
        return base
