"""Clasificador de errores del FTRRF — determinístico, sin efectos colaterales."""

from __future__ import annotations

from zovrake_motor.enterprise_integration.ftrrf.enums import ErrorCategory, ErrorSeverity
from zovrake_motor.enterprise_integration.ftrrf.models import FaultClassification

_ERROR_CODE_CATEGORY: dict[str, ErrorCategory] = {
    "structural_validation_failed": ErrorCategory.VALIDATION,
    "required_field_missing": ErrorCategory.VALIDATION,
    "invalid_field_type": ErrorCategory.VALIDATION,
    "contract_version_unsupported": ErrorCategory.VALIDATION,
    "process_not_found": ErrorCategory.SYSTEM_INTERNAL,
    "operation_not_executed": ErrorCategory.PROCESSING,
    "api_not_initialized": ErrorCategory.COMMUNICATION,
    "coordinator_required": ErrorCategory.COMMUNICATION,
    "pio_orchestration_required": ErrorCategory.COMMUNICATION,
}

_RECOVERABLE_CATEGORIES: frozenset[ErrorCategory] = frozenset(
    {
        ErrorCategory.COMMUNICATION,
        ErrorCategory.PROCESSING,
        ErrorCategory.TEMPORARY,
    }
)

_SEVERITY_BY_CATEGORY: dict[ErrorCategory, ErrorSeverity] = {
    ErrorCategory.VALIDATION: ErrorSeverity.WARNING,
    ErrorCategory.DOCUMENTAL: ErrorSeverity.WARNING,
    ErrorCategory.COMMUNICATION: ErrorSeverity.ERROR,
    ErrorCategory.PROCESSING: ErrorSeverity.ERROR,
    ErrorCategory.TEMPORARY: ErrorSeverity.WARNING,
    ErrorCategory.PERMANENT: ErrorSeverity.CRITICAL,
    ErrorCategory.SYSTEM_INTERNAL: ErrorSeverity.CRITICAL,
}


class ErrorClassifier:
    """
    Clasifica errores por código y descripción.

    No resuelve errores automáticamente; solo determina su naturaleza.
    """

    def classify(
        self,
        *,
        error_code: str = "",
        description: str = "",
        origin_component: str = "pipeline_integration_orchestrator",
    ) -> FaultClassification:
        category = self._resolve_category(error_code, description)
        recoverable = category in _RECOVERABLE_CATEGORIES
        severity = _SEVERITY_BY_CATEGORY.get(category, ErrorSeverity.ERROR)
        return FaultClassification(
            category=category,
            severity=severity,
            recoverable=recoverable,
            origin_component=origin_component,
            description=description or f"Error controlado ({category.value})",
        )

    def _resolve_category(self, error_code: str, description: str) -> ErrorCategory:
        code = (error_code or "").strip().lower()
        if code in _ERROR_CODE_CATEGORY:
            return _ERROR_CODE_CATEGORY[code]

        text = (description or "").lower()
        if any(token in text for token in ("document", "documento", "evidencia")):
            return ErrorCategory.DOCUMENTAL
        if any(token in text for token in ("timeout", "temporal", "temporary", "retry")):
            return ErrorCategory.TEMPORARY
        if any(token in text for token in ("comunic", "communication", "connection", "conexion")):
            return ErrorCategory.COMMUNICATION
        if any(token in text for token in ("valid", "contract", "campo", "field")):
            return ErrorCategory.VALIDATION
        if any(token in text for token in ("permanent", "irrecuperable")):
            return ErrorCategory.PERMANENT
        if any(token in text for token in ("procesa", "processing", "pipeline")):
            return ErrorCategory.PROCESSING
        return ErrorCategory.SYSTEM_INTERNAL
