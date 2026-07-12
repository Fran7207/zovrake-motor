"""Enumeraciones del Comparative Quality Framework."""

from __future__ import annotations

from enum import Enum


class ComparativeQualityValidationStatus(str, Enum):
    """Estado global de la auditoría de calidad."""

    PASSED = "passed"
    PASSED_WITH_WARNINGS = "passed_with_warnings"
    FAILED = "failed"
    SKIPPED = "skipped"


class ComparativeQualityCategory(str, Enum):
    """Categorías de auditoría del CQF."""

    ARCHITECTURAL = "architectural"
    CONSISTENCY = "consistency"
    INTEGRITY = "integrity"
    UNIQUENESS = "uniqueness"
    TRACEABILITY = "traceability"
    PIPELINE = "pipeline"


class ComparativeQualityValidatorStrategyType(str, Enum):
    """Estrategias de auditoría de calidad."""

    ARCHITECTURAL_COMPLIANCE = "architectural_compliance"
    DEFINITIVE_MODEL_CONSISTENCY = "definitive_model_consistency"
    VALIDATION_REPORT_INTEGRITY = "validation_report_integrity"
    IDENTIFIER_UNIQUENESS = "identifier_uniqueness"
    TRACEABILITY_CHAIN = "traceability_chain"
    PIPELINE_FLOW = "pipeline_flow"
