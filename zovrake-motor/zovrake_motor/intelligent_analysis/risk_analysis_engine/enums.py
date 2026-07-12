"""Enumeraciones del Risk Analysis Engine."""

from __future__ import annotations

from enum import Enum


class RiskCategory(str, Enum):
    """Categorías oficiales de riesgos identificados por el RAE."""

    DOCUMENTATION = "documentation"
    COMMERCIAL = "commercial"
    TECHNICAL = "technical"
    INFORMATION = "information"
    CONSISTENCY = "consistency"


class RiskStatus(str, Enum):
    """Estado del riesgo — sin resolución automática."""

    IDENTIFIED = "identified"
    REGISTERED = "registered"


class RiskAnalysisStatus(str, Enum):
    """Estado del análisis de riesgos."""

    ANALYZED = "analyzed"
    PARTIAL = "partial"
    SKIPPED = "skipped"


class RiskAnalyzerStrategyType(str, Enum):
    """Estrategias de análisis de riesgos."""

    ORGANIZED_EVIDENCE_CONSISTENCY = "organized_evidence_consistency"
