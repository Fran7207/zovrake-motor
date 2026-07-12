"""Enumeraciones del Explanation Generation Engine."""

from __future__ import annotations

from enum import Enum


class ExplanationSectionType(str, Enum):
    """Secciones estructuradas de una explicación — reutilizables y presentables."""

    ANALYSIS_SUMMARY = "analysis_summary"
    EVIDENCE_USED = "evidence_used"
    STRENGTH = "strength"
    WEAKNESS = "weakness"
    RISK = "risk"
    CONSISTENCY = "consistency"
    CONTEXT_INFLUENCE = "context_influence"
    MISSING_INFORMATION = "missing_information"
    LIMITATION = "limitation"
    OBSERVATION = "observation"


class ExplanationGenerationStatus(str, Enum):
    """Estado de la generación de explicaciones."""

    GENERATED = "generated"
    PARTIAL = "partial"
    SKIPPED = "skipped"


class ExplanationGeneratorStrategyType(str, Enum):
    """Estrategias de generación de explicaciones."""

    ORGANIZED_ANALYSIS_EXPLANATION = "organized_analysis_explanation"
