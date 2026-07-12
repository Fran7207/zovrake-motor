"""Enumeraciones del Classification Quality Framework."""

from __future__ import annotations

from enum import Enum


class QualityValidationStatus(str, Enum):
    """Estado global de la validación de calidad."""

    PASSED = "passed"
    PASSED_WITH_WARNINGS = "passed_with_warnings"
    FAILED = "failed"
    SKIPPED = "skipped"


class QualityValidationCategory(str, Enum):
    """Categorías de validación del CQF."""

    CONSISTENCY = "consistency"
    INTEGRITY = "integrity"
    UNIQUENESS = "uniqueness"
    TRACEABILITY = "traceability"
    PIPELINE = "pipeline"


class QualityValidatorStrategyType(str, Enum):
    """Estrategias de validación."""

    MODEL_CONSISTENCY = "model_consistency"
    DATA_INTEGRITY = "data_integrity"
    IDENTIFIER_UNIQUENESS = "identifier_uniqueness"
    TRACEABILITY_CHAIN = "traceability_chain"
    PIPELINE_FLOW = "pipeline_flow"
