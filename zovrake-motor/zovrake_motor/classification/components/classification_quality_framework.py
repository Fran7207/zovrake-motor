"""Classification Quality Framework — integración con el módulo de clasificación."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.classification.classification_quality.engine import ClassificationQualityFrameworkEngine
from zovrake_motor.classification.classification_quality.integration import ClassificationQualityMotorIntegration
from zovrake_motor.classification.classification_quality.models import (
    ClassificationQualityValidationRequest,
    ClassificationQualityValidationResult,
)
from zovrake_motor.classification.components.base import ClassificationComponentPort

if TYPE_CHECKING:
    from zovrake_motor.classification.integration import ClassificationMotorIntegration
    from zovrake_motor.config.provider import ConfigurationProvider


class ClassificationQualityFramework(ClassificationComponentPort):
    """
    Gestor del Classification Quality Framework (CQF).

    Responsabilidad única: validar calidad, consistencia e integridad de la clasificación.
    """

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        engine: ClassificationQualityFrameworkEngine | None = None,
    ) -> None:
        self._engine = engine or ClassificationQualityFrameworkEngine(config_provider=config_provider)
        self._component_initialized = False

    @property
    def component_name(self) -> str:
        return "classification_quality_framework"

    @property
    def component_label(self) -> str:
        return "Classification Quality Framework"

    @property
    def engine(self) -> ClassificationQualityFrameworkEngine:
        return self._engine

    def initialize(self) -> None:
        self._engine.initialize()
        self._component_initialized = True

    def is_ready(self) -> bool:
        return self._component_initialized and self._engine.is_ready()

    def validate(
        self,
        request: ClassificationQualityValidationRequest,
        *,
        integration: ClassificationMotorIntegration | None = None,
        record_traceability: bool = True,
    ) -> ClassificationQualityValidationResult:
        catalog_id = str(request.comparative_domain_model_catalog.get("catalog_id", ""))
        document_id = str(request.comparative_domain_model_catalog.get("document_id", ""))
        model_id = str(request.comparative_domain_model_catalog.get("model_id", ""))

        if integration is not None and record_traceability:
            bridge = ClassificationQualityMotorIntegration.from_classification_integration(integration)
            bridge.begin_quality_validation(
                request.process_id,
                document_id=document_id,
                model_id=model_id,
                comparative_domain_model_catalog_id=catalog_id,
            )

        result = self._engine.validate(request)

        if integration is not None and record_traceability:
            bridge = ClassificationQualityMotorIntegration.from_classification_integration(integration)
            bridge.complete_quality_validation(request.process_id, result)

        return result

    def snapshot(self) -> dict[str, Any]:
        base = super().snapshot()
        base["engine"] = self._engine.snapshot()
        return base
