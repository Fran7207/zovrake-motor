"""Modelos del Context Evaluation Engine — evaluación contextual de evidencias."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from zovrake_motor.intelligent_analysis.context_evaluation_engine.enums import (
    ContextAssociationType,
    ContextElementType,
    ContextEvaluationStatus,
    ContextualGapType,
)


@dataclass(frozen=True)
class ContextTraceabilityReference:
    """Referencia de trazabilidad contextual — sin modificar origen."""

    context_key: str
    context_source: str
    evidence_id: str | None
    definitive_model_id: str
    group_id: str
    comparative_table_id: str
    provider_id: str | None
    document_id: str
    traceability: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "context_key": self.context_key,
            "context_source": self.context_source,
            "evidence_id": self.evidence_id,
            "definitive_model_id": self.definitive_model_id,
            "group_id": self.group_id,
            "comparative_table_id": self.comparative_table_id,
            "provider_id": self.provider_id,
            "document_id": self.document_id,
            "traceability": self.traceability,
        }


@dataclass(frozen=True)
class ContextElementRecord:
    """Elemento del contexto del requerimiento identificado."""

    context_key: str
    context_value: Any
    element_type: ContextElementType
    context_source: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "context_key": self.context_key,
            "context_value": self.context_value,
            "element_type": self.element_type.value,
            "context_source": self.context_source,
        }


@dataclass(frozen=True)
class ContextAssociationRecord:
    """Asociación entre contexto y evidencia — sin interpretación decisoria."""

    association_id: str
    association_type: ContextAssociationType
    context_key: str
    context_value: Any
    element_type: ContextElementType
    associated_evidence_ids: tuple[str, ...]
    provider_ids: tuple[str, ...]
    traceability_ref: ContextTraceabilityReference
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "association_id": self.association_id,
            "association_type": self.association_type.value,
            "context_key": self.context_key,
            "context_value": self.context_value,
            "element_type": self.element_type.value,
            "associated_evidence_ids": list(self.associated_evidence_ids),
            "provider_ids": list(self.provider_ids),
            "traceability_ref": self.traceability_ref.to_dict(),
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class ContextualGapRecord:
    """Vacío contextual detectado — registro sin completar datos."""

    gap_id: str
    gap_type: ContextualGapType
    description: str
    context_key: str
    related_evidence_ids: tuple[str, ...]
    provider_ids: tuple[str, ...]
    traceability_ref: ContextTraceabilityReference
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "gap_id": self.gap_id,
            "gap_type": self.gap_type.value,
            "description": self.description,
            "context_key": self.context_key,
            "related_evidence_ids": list(self.related_evidence_ids),
            "provider_ids": list(self.provider_ids),
            "traceability_ref": self.traceability_ref.to_dict(),
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class ModelContextProfile:
    """Perfil de evaluación contextual por Modelo Comparativo Definitivo."""

    definitive_model_id: str
    comparative_table_id: str
    group_id: str
    group_type: str
    context_elements: tuple[ContextElementRecord, ...]
    associations: tuple[ContextAssociationRecord, ...]
    contextual_gaps: tuple[ContextualGapRecord, ...]
    context_elements_evaluated: int
    evidence_records_evaluated: int
    source_data_preserved: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "definitive_model_id": self.definitive_model_id,
            "comparative_table_id": self.comparative_table_id,
            "group_id": self.group_id,
            "group_type": self.group_type,
            "context_elements": [element.to_dict() for element in self.context_elements],
            "context_elements_count": len(self.context_elements),
            "associations": [record.to_dict() for record in self.associations],
            "associations_count": len(self.associations),
            "contextual_gaps": [record.to_dict() for record in self.contextual_gaps],
            "contextual_gaps_count": len(self.contextual_gaps),
            "context_elements_evaluated": self.context_elements_evaluated,
            "evidence_records_evaluated": self.evidence_records_evaluated,
            "source_data_preserved": self.source_data_preserved,
        }


@dataclass(frozen=True)
class ContextEvaluationCatalog:
    """Catálogo de evaluación contextual del proceso."""

    catalog_id: str
    process_id: UUID
    model_id: str
    document_id: str
    source_evidence_catalog_id: str
    source_consistency_catalog_id: str
    source_risk_catalog_id: str
    source_definitive_catalog_id: str
    profiles: tuple[ModelContextProfile, ...]
    explanation_generation_engine_prepared: bool = True
    evidence_catalog_preserved: bool = True
    consistency_catalog_preserved: bool = True
    risk_catalog_preserved: bool = True
    definitive_catalog_preserved: bool = True
    requirement_context_preserved: bool = True
    source_data_preserved: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "catalog_id": self.catalog_id,
            "process_id": str(self.process_id),
            "model_id": self.model_id,
            "document_id": self.document_id,
            "source_evidence_catalog_id": self.source_evidence_catalog_id,
            "source_consistency_catalog_id": self.source_consistency_catalog_id,
            "source_risk_catalog_id": self.source_risk_catalog_id,
            "source_definitive_catalog_id": self.source_definitive_catalog_id,
            "profiles": [profile.to_dict() for profile in self.profiles],
            "profiles_count": len(self.profiles),
            "explanation_generation_engine_prepared": self.explanation_generation_engine_prepared,
            "evidence_catalog_preserved": self.evidence_catalog_preserved,
            "consistency_catalog_preserved": self.consistency_catalog_preserved,
            "risk_catalog_preserved": self.risk_catalog_preserved,
            "definitive_catalog_preserved": self.definitive_catalog_preserved,
            "requirement_context_preserved": self.requirement_context_preserved,
            "source_data_preserved": self.source_data_preserved,
        }


@dataclass(frozen=True)
class EvaluatorResult:
    """Resultado individual de un evaluador contextual."""

    evaluator_type: str
    evaluator_name: str
    profiles: tuple[ModelContextProfile, ...] = ()
    technical_observations: tuple[str, ...] = ()


@dataclass(frozen=True)
class ContextEvaluationIncident:
    """Incidencia estructural durante la evaluación — sin corrección automática."""

    evaluator_name: str
    message: str
    severity: str = "info"

    def to_dict(self) -> dict[str, Any]:
        return {
            "evaluator_name": self.evaluator_name,
            "message": self.message,
            "severity": self.severity,
        }


@dataclass(frozen=True)
class ContextEvaluationRequest:
    """
    Solicitud de evaluación contextual.

    El CxEE consume exclusivamente salidas del EAE, CEE, RAE,
    Modelo Comparativo Definitivo y contexto del requerimiento (PM4).
    """

    process_id: UUID
    evidence_catalog: Any
    consistency_catalog: Any
    risk_catalog: Any
    definitive_catalog: dict[str, Any]
    requirement_context: dict[str, Any] = field(default_factory=dict)
    codigo_req: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ContextEvaluationResult:
    """Resultado uniforme de la evaluación contextual."""

    process_id: UUID
    document_id: str
    model_id: str
    catalog: ContextEvaluationCatalog
    status: ContextEvaluationStatus
    associations_count: int
    contextual_gaps_count: int
    evidence_catalog_preserved: bool
    consistency_catalog_preserved: bool
    risk_catalog_preserved: bool
    definitive_catalog_preserved: bool
    requirement_context_preserved: bool
    source_data_preserved: bool
    evaluators_executed: int
    incidents: tuple[ContextEvaluationIncident, ...] = ()
    technical_observations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "document_id": self.document_id,
            "model_id": self.model_id,
            "catalog": self.catalog.to_dict(),
            "status": self.status.value,
            "associations_count": self.associations_count,
            "contextual_gaps_count": self.contextual_gaps_count,
            "evidence_catalog_preserved": self.evidence_catalog_preserved,
            "consistency_catalog_preserved": self.consistency_catalog_preserved,
            "risk_catalog_preserved": self.risk_catalog_preserved,
            "definitive_catalog_preserved": self.definitive_catalog_preserved,
            "requirement_context_preserved": self.requirement_context_preserved,
            "source_data_preserved": self.source_data_preserved,
            "evaluators_executed": self.evaluators_executed,
            "incidents": [incident.to_dict() for incident in self.incidents],
            "technical_observations": list(self.technical_observations),
        }
