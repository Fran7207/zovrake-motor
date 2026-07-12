"""Material Classification Engine (MCE) — integración con el módulo de clasificación."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.classification.components.base import ClassificationComponentPort
from zovrake_motor.classification.material_classification.engine import MaterialClassificationEngine
from zovrake_motor.classification.material_classification.integration import MaterialClassificationMotorIntegration
from zovrake_motor.classification.material_classification.models import (
    MaterialClassificationRequest,
    MaterialClassificationResult,
)

if TYPE_CHECKING:
    from zovrake_motor.classification.integration import ClassificationMotorIntegration
    from zovrake_motor.config.provider import ConfigurationProvider


class MaterialClassificationEngineComponent(ClassificationComponentPort):
    """
    Gestor del Material Classification Engine (MCE).

    Responsabilidad única: clasificar conceptos del CAE como materiales.
    """

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        engine: MaterialClassificationEngine | None = None,
    ) -> None:
        self._engine = engine or MaterialClassificationEngine(config_provider=config_provider)
        self._component_initialized = False

    @property
    def component_name(self) -> str:
        return "material_classification_engine"

    @property
    def component_label(self) -> str:
        return "Material Classification Engine"

    @property
    def engine(self) -> MaterialClassificationEngine:
        return self._engine

    def initialize(self) -> None:
        self._engine.initialize()
        self._component_initialized = True

    def is_ready(self) -> bool:
        return self._component_initialized and self._engine.is_ready()

    def classify(
        self,
        request: MaterialClassificationRequest,
        *,
        integration: ClassificationMotorIntegration | None = None,
        record_traceability: bool = True,
    ) -> MaterialClassificationResult:
        catalog_id = str(request.concept_catalog.get("catalog_id", ""))
        document_id = str(request.concept_catalog.get("document_id", ""))
        model_id = str(request.concept_catalog.get("model_id", ""))

        if integration is not None and record_traceability:
            bridge = MaterialClassificationMotorIntegration.from_classification_integration(integration)
            bridge.begin_material_classification(
                request.process_id,
                document_id=document_id,
                model_id=model_id,
                concept_catalog_id=catalog_id,
            )

        result = self._engine.classify(request)

        if integration is not None and record_traceability:
            bridge = MaterialClassificationMotorIntegration.from_classification_integration(integration)
            bridge.complete_material_classification(request.process_id, result)

        return result

    def snapshot(self) -> dict[str, Any]:
        base = super().snapshot()
        base["engine"] = self._engine.snapshot()
        return base
