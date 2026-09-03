"""Enumeraciones del Equivalence Detection Engine."""

from __future__ import annotations

from enum import Enum


class EquivalenceDetectionStatus(str, Enum):
    """Estado de la detección de equivalencias."""

    DETECTED = "detected"
    SKIPPED = "skipped"
    PARTIAL = "partial"


class EquivalenceRelationType(str, Enum):
    """Tipo de relación entre conceptos normalizados."""

    EQUIVALENT = "equivalent"
    DISTINCT = "distinct"
    RELATED = "related"
    COMPARABLE = "comparable"


class EvidenceLevel(str, Enum):
    """Nivel de evidencia de una relación detectada."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EquivalenceDetectorType(str, Enum):
    """Tipos de detectores del EDE."""

    EXACT_NORMALIZED_MATCH = "exact_normalized_match"
    CROSS_TYPE_DISTINCT = "cross_type_distinct"
    SHARED_ORIGIN_RELATION = "shared_origin_relation"
    SEMANTIC_SIMILARITY = "semantic_similarity"
