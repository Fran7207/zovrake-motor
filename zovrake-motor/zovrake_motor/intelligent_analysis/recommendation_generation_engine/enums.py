"""Enumeraciones del Recommendation Generation Engine."""

from __future__ import annotations

from enum import Enum


class RecommendationScenarioType(str, Enum):
    """Escenarios oficiales de recomendación."""

    CLEAR_WINNER = "clear_winner"
    EQUIVALENT_ALTERNATIVES = "equivalent_alternatives"
    INSUFFICIENT_INFORMATION = "insufficient_information"


class ConfidenceLevel(str, Enum):
    """Nivel de confianza derivado de evidencias."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RecommendationGenerationStatus(str, Enum):
    """Estado de la generación de recomendaciones."""

    GENERATED = "generated"
    PARTIAL = "partial"
    SKIPPED = "skipped"


class RecommendationGeneratorStrategyType(str, Enum):
    """Estrategias de generación de recomendaciones."""

    ORGANIZED_EVIDENCE_RECOMMENDATION = "organized_evidence_recommendation"
