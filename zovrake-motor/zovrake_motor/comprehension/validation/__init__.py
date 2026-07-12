"""Document Validation Framework — Implementación 2.3."""

from zovrake_motor.comprehension.validation.enums import (
    DocumentQualityLevel,
    ValidationIncidentType,
    ValidationSeverity,
    ValidationStatus,
)
from zovrake_motor.comprehension.validation.exceptions import (
    ValidationExecutionError,
    ValidationFrameworkError,
    ValidationRuleNotFoundError,
)
from zovrake_motor.comprehension.validation.executor import ValidationExecutor
from zovrake_motor.comprehension.validation.framework import DocumentValidationFramework
from zovrake_motor.comprehension.validation.integration import ValidationMotorIntegration
from zovrake_motor.comprehension.validation.models import (
    DocumentValidationRequest,
    DocumentValidationResult,
    ValidationIncident,
    ValidationRuleResult,
    ValidationWarning,
)
from zovrake_motor.comprehension.validation.port import ValidationRulePort
from zovrake_motor.comprehension.validation.registry import ValidationRuleRegistry
from zovrake_motor.comprehension.validation.rules import (
    CorruptFileRule,
    EmptyFileRule,
    IllegibleDocumentRule,
    InaccessibleFileRule,
    IncompleteDocumentRule,
    InconsistentStructureRule,
    InvalidSizeRule,
    UnsupportedFormatRule,
)

__all__ = [
    "CorruptFileRule",
    "DocumentQualityLevel",
    "DocumentValidationFramework",
    "DocumentValidationRequest",
    "DocumentValidationResult",
    "EmptyFileRule",
    "IllegibleDocumentRule",
    "InaccessibleFileRule",
    "IncompleteDocumentRule",
    "InconsistentStructureRule",
    "InvalidSizeRule",
    "UnsupportedFormatRule",
    "ValidationExecutionError",
    "ValidationExecutor",
    "ValidationFrameworkError",
    "ValidationIncident",
    "ValidationIncidentType",
    "ValidationMotorIntegration",
    "ValidationRuleNotFoundError",
    "ValidationRulePort",
    "ValidationRuleRegistry",
    "ValidationRuleResult",
    "ValidationSeverity",
    "ValidationStatus",
    "ValidationWarning",
]
