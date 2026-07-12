"""Validador Documental — integración con el Document Validation Framework."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.comprehension.components.base import ComprehensionComponentPort
from zovrake_motor.comprehension.validation.framework import DocumentValidationFramework
from zovrake_motor.comprehension.validation.integration import ValidationMotorIntegration
from zovrake_motor.comprehension.validation.models import DocumentValidationRequest, DocumentValidationResult

if TYPE_CHECKING:
    from zovrake_motor.comprehension.integration import ComprehensionMotorIntegration
    from zovrake_motor.config.provider import ConfigurationProvider


class DocumentValidator(ComprehensionComponentPort):
    """
    Gestor del Document Validation Framework (DVF).

    Responsabilidad única: coordinar la validación documental previa
    al procesamiento posterior del Pipeline.
    """

    def __init__(
        self,
        *,
        config_provider: ConfigurationProvider | None = None,
        framework: DocumentValidationFramework | None = None,
    ) -> None:
        self._framework = framework or DocumentValidationFramework(config_provider=config_provider)
        self._component_initialized = False

    @property
    def component_name(self) -> str:
        return "document_validator"

    @property
    def component_label(self) -> str:
        return "Validador Documental"

    @property
    def framework(self) -> DocumentValidationFramework:
        return self._framework

    def initialize(self) -> None:
        self._framework.initialize()
        self._component_initialized = True

    def is_ready(self) -> bool:
        return self._component_initialized and self._framework.is_ready()

    def validate(
        self,
        request: DocumentValidationRequest,
        *,
        integration: ComprehensionMotorIntegration | None = None,
        record_traceability: bool = True,
    ) -> DocumentValidationResult:
        if integration is not None and record_traceability:
            bridge = ValidationMotorIntegration.from_comprehension_integration(integration)
            bridge.begin_validation(request.process_id, document_id=request.document_id)

        result = self._framework.validate(request)

        traceability: dict[str, Any] | None = None
        if integration is not None and record_traceability:
            bridge = ValidationMotorIntegration.from_comprehension_integration(integration)
            traceability = bridge.complete_validation(request.process_id, result)

        if traceability is not None:
            return DocumentValidationResult(
                process_id=result.process_id,
                document_id=result.document_id,
                status=result.status,
                incidents=result.incidents,
                warnings=result.warnings,
                quality_level=result.quality_level,
                technical_observations=(
                    *result.technical_observations,
                    f"traceability_recorded={bool(traceability)}",
                ),
                rules_executed=result.rules_executed,
                rules_passed=result.rules_passed,
            )

        return result

    def snapshot(self) -> dict[str, Any]:
        base = super().snapshot()
        base["framework"] = self._framework.snapshot()
        return base
