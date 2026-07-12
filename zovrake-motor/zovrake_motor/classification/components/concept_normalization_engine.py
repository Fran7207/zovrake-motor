"""Concept Normalization Engine (CNE) — integración con el módulo de clasificación."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.classification.components.base import ClassificationComponentPort
from zovrake_motor.classification.concept_normalization.engine import ConceptNormalizationEngine
from zovrake_motor.classification.concept_normalization.integration import (
    ConceptNormalizationMotorIntegration,
)
from zovrake_motor.classification.concept_normalization.models import (
    ConceptNormalizationRequest,
    ConceptNormalizationResult,
)

if TYPE_CHECKING:
    from zovrake_motor.classification.integration import ClassificationMotorIntegration
    from zovrake_motor.config.provider import ConfigurationProvider


class ConceptNormalizationEngineComponent(ClassificationComponentPort):
    """
    Gestor del Concept Normalization Engine (CNE).

    Responsabilidad única: normalizar conceptos clasificados de materiales y servicios.
    """

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        engine: ConceptNormalizationEngine | None = None,
    ) -> None:
        self._engine = engine or ConceptNormalizationEngine(config_provider=config_provider)
        self._component_initialized = False

    @property
    def component_name(self) -> str:
        return "concept_normalization_engine"

    @property
    def component_label(self) -> str:
        return "Concept Normalization Engine"

    @property
    def engine(self) -> ConceptNormalizationEngine:
        return self._engine

    def initialize(self) -> None:
        self._engine.initialize()
        self._component_initialized = True

    def is_ready(self) -> bool:
        return self._component_initialized and self._engine.is_ready()

    def normalize(
        self,
        request: ConceptNormalizationRequest,
        *,
        integration: ClassificationMotorIntegration | None = None,
        record_traceability: bool = True,
    ) -> ConceptNormalizationResult:
        material_catalog_id = str(request.material_catalog.get("catalog_id", ""))
        service_catalog_id = str(request.service_catalog.get("catalog_id", ""))
        document_id = str(request.material_catalog.get("document_id", ""))
        model_id = str(request.material_catalog.get("model_id", ""))

        if integration is not None and record_traceability:
            bridge = ConceptNormalizationMotorIntegration.from_classification_integration(integration)
            bridge.begin_concept_normalization(
                request.process_id,
                document_id=document_id,
                model_id=model_id,
                material_catalog_id=material_catalog_id,
                service_catalog_id=service_catalog_id,
            )

        result = self._engine.normalize(request)

        if integration is not None and record_traceability:
            bridge = ConceptNormalizationMotorIntegration.from_classification_integration(integration)
            bridge.complete_concept_normalization(request.process_id, result)

        return result

    def snapshot(self) -> dict[str, Any]:
        base = super().snapshot()
        base["engine"] = self._engine.snapshot()
        return base
