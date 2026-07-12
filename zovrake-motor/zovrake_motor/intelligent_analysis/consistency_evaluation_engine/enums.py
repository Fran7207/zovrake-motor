"""Enumeraciones del Consistency Evaluation Engine."""

from __future__ import annotations

from enum import Enum


class ConsistencyCriterionType(str, Enum):
    """Criterios oficiales de evaluación de consistencia."""

    COMMERCIAL_TECHNICAL_COHERENCE = "commercial_technical_coherence"
    PROVIDER_COMPARABILITY = "provider_comparability"
    INFORMATION_INTEGRITY = "information_integrity"
    COMPARABLE_ATTRIBUTE_RELATIONS = "comparable_attribute_relations"
    EVIDENCE_NON_CONTRADICTION = "evidence_non_contradiction"


class InconsistencyType(str, Enum):
    """Tipos de inconsistencias detectadas — sin corrección automática."""

    CONTRADICTORY_INFORMATION = "contradictory_information"
    INCOMPATIBLE_DATA = "incompatible_data"
    INCONSISTENT_ATTRIBUTES = "inconsistent_attributes"
    INCOMPLETE_REFERENCE = "incomplete_reference"
    RELEVANT_DIFFERENCE = "relevant_difference"


class ConsistencyEvaluationStatus(str, Enum):
    """Estado de la evaluación de consistencia."""

    EVALUATED = "evaluated"
    PARTIAL = "partial"
    SKIPPED = "skipped"


class SufficiencyLevel(str, Enum):
    """Nivel de suficiencia para continuar el razonamiento."""

    SUFFICIENT = "sufficient"
    PARTIAL = "partial"
    INSUFFICIENT = "insufficient"


class ConsistencyEvaluatorStrategyType(str, Enum):
    """Estrategias de evaluación de consistencia."""

    ORGANIZED_EVIDENCE = "organized_evidence"
