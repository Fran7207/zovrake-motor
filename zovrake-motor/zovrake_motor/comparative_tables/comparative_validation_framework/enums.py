"""Enumeraciones del Comparative Validation Framework."""

from __future__ import annotations

from enum import Enum


class ComparativeModelValidationStatus(str, Enum):
    """Estado global de la validación del modelo comparativo definitivo."""

    VALID = "valid"
    INVALID = "invalid"
    PARTIAL = "partial"
    SKIPPED = "skipped"


class ValidationFindingCategory(str, Enum):
    """Categoría de un hallazgo de validación."""

    STRUCTURAL = "structural"
    INTEGRITY = "integrity"
    COMPLETENESS = "completeness"
    CONSISTENCY = "consistency"
    TRACEABILITY = "traceability"
    GENERAL = "general"


class ValidationFindingSeverity(str, Enum):
    """Severidad de un hallazgo de validación."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class ValidationValidatorStrategyType(str, Enum):
    """Estrategias de validación de modelos comparativos."""

    DEFINITIVE_MODEL = "definitive_model"
