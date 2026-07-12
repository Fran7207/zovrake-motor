"""Enumeraciones del Evidence Analysis Engine."""

from __future__ import annotations

from enum import Enum


class EvidenceCategory(str, Enum):
    """Categorías oficiales de evidencias identificadas por el EAE."""

    COMMERCIAL_INFORMATION = "commercial_information"
    TECHNICAL_INFORMATION = "technical_information"
    COMMERCIAL_CONDITIONS = "commercial_conditions"
    DELIVERY_TIMES = "delivery_times"
    WARRANTIES = "warranties"
    CERTIFICATIONS = "certifications"
    OBSERVATIONS = "observations"
    RESTRICTIONS = "restrictions"
    METADATA = "metadata"
    REQUIREMENT_CONTEXT = "requirement_context"


class EvidencePresenceStatus(str, Enum):
    """Estado de presencia de una evidencia."""

    PRESENT = "present"
    ABSENT = "absent"


class EvidenceAnalysisStatus(str, Enum):
    """Estado del análisis de evidencias."""

    ANALYZED = "analyzed"
    PARTIAL = "partial"
    SKIPPED = "skipped"


class EvidenceAnalyzerStrategyType(str, Enum):
    """Estrategias de análisis de evidencias."""

    DEFINITIVE_MODEL = "definitive_model"
