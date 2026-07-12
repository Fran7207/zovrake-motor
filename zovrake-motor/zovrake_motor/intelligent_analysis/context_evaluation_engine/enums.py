"""Enumeraciones del Context Evaluation Engine."""

from __future__ import annotations

from enum import Enum


class ContextElementType(str, Enum):
    """Tipos de elementos del contexto del requerimiento."""

    COMMERCIAL_REQUIREMENT = "commercial_requirement"
    TECHNICAL_REQUIREMENT = "technical_requirement"
    GENERAL_REQUIREMENT = "general_requirement"
    OBJECTIVE = "objective"
    LIMITATION = "limitation"


class ContextAssociationType(str, Enum):
    """Tipos de asociación entre contexto y evidencias."""

    ALIGNMENT = "alignment"
    PARTIAL_ALIGNMENT = "partial_alignment"
    GAP = "gap"
    LIMITATION = "limitation"


class ContextualGapType(str, Enum):
    """Tipos de vacíos contextuales detectados."""

    REQUIREMENT_WITHOUT_EVIDENCE = "requirement_without_evidence"
    EVIDENCE_WITHOUT_CONTEXT = "evidence_without_context"
    QUOTATION_REQUIREMENT_DIFFERENCE = "quotation_requirement_difference"
    INSUFFICIENT_CONTEXT_DATA = "insufficient_context_data"


class ContextEvaluationStatus(str, Enum):
    """Estado de la evaluación contextual."""

    EVALUATED = "evaluated"
    PARTIAL = "partial"
    SKIPPED = "skipped"


class ContextEvaluatorStrategyType(str, Enum):
    """Estrategias de evaluación contextual."""

    ORGANIZED_EVIDENCE_RISK_CONTEXT = "organized_evidence_risk_context"
