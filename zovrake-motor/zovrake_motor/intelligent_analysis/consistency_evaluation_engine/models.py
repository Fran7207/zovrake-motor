"""Modelos del Consistency Evaluation Engine — evaluación de consistencia de evidencias."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.enums import (
    ConsistencyCriterionType,
    ConsistencyEvaluationStatus,
    InconsistencyType,
    SufficiencyLevel,
)


@dataclass(frozen=True)
class InconsistencyTraceabilityReference:
    """Referencia de trazabilidad de una inconsistencia — sin modificar origen."""

    evidence_id: str | None
    definitive_model_id: str
    group_id: str
    comparative_table_id: str
    provider_id: str | None
    document_id: str
    source_field: str | None
    traceability: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "definitive_model_id": self.definitive_model_id,
            "group_id": self.group_id,
            "comparative_table_id": self.comparative_table_id,
            "provider_id": self.provider_id,
            "document_id": self.document_id,
            "source_field": self.source_field,
            "traceability": self.traceability,
        }


@dataclass(frozen=True)
class InconsistencyRecord:
    """Inconsistencia detectada — registro sin corrección automática."""

    inconsistency_id: str
    inconsistency_type: InconsistencyType
    criterion: ConsistencyCriterionType
    description: str
    related_evidence_ids: tuple[str, ...]
    provider_ids: tuple[str, ...]
    traceability_ref: InconsistencyTraceabilityReference
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "inconsistency_id": self.inconsistency_id,
            "inconsistency_type": self.inconsistency_type.value,
            "criterion": self.criterion.value,
            "description": self.description,
            "related_evidence_ids": list(self.related_evidence_ids),
            "provider_ids": list(self.provider_ids),
            "traceability_ref": self.traceability_ref.to_dict(),
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class SufficiencyAssessment:
    """Evaluación de suficiencia para continuar el razonamiento — sin conclusión."""

    definitive_model_id: str
    group_id: str
    sufficiency_level: SufficiencyLevel
    sufficient_for_reasoning: bool
    reason: str
    missing_evidence_count: int
    inconsistency_count: int
    blocking_factors: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "definitive_model_id": self.definitive_model_id,
            "group_id": self.group_id,
            "sufficiency_level": self.sufficiency_level.value,
            "sufficient_for_reasoning": self.sufficient_for_reasoning,
            "reason": self.reason,
            "missing_evidence_count": self.missing_evidence_count,
            "inconsistency_count": self.inconsistency_count,
            "blocking_factors": list(self.blocking_factors),
        }


@dataclass(frozen=True)
class ModelConsistencyProfile:
    """Perfil de consistencia por Modelo Comparativo Definitivo."""

    definitive_model_id: str
    comparative_table_id: str
    group_id: str
    group_type: str
    inconsistencies: tuple[InconsistencyRecord, ...]
    sufficiency: SufficiencyAssessment
    criteria_evaluated: tuple[str, ...]
    evidence_records_evaluated: int
    source_data_preserved: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "definitive_model_id": self.definitive_model_id,
            "comparative_table_id": self.comparative_table_id,
            "group_id": self.group_id,
            "group_type": self.group_type,
            "inconsistencies": [record.to_dict() for record in self.inconsistencies],
            "inconsistencies_count": len(self.inconsistencies),
            "sufficiency": self.sufficiency.to_dict(),
            "criteria_evaluated": list(self.criteria_evaluated),
            "evidence_records_evaluated": self.evidence_records_evaluated,
            "source_data_preserved": self.source_data_preserved,
        }


@dataclass(frozen=True)
class ConsistencyEvaluationCatalog:
    """Catálogo de evaluación de consistencia del proceso."""

    catalog_id: str
    process_id: UUID
    model_id: str
    document_id: str
    source_evidence_catalog_id: str
    profiles: tuple[ModelConsistencyProfile, ...]
    risk_analysis_engine_prepared: bool = True
    evidence_catalog_preserved: bool = True
    source_data_preserved: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "catalog_id": self.catalog_id,
            "process_id": str(self.process_id),
            "model_id": self.model_id,
            "document_id": self.document_id,
            "source_evidence_catalog_id": self.source_evidence_catalog_id,
            "profiles": [profile.to_dict() for profile in self.profiles],
            "profiles_count": len(self.profiles),
            "risk_analysis_engine_prepared": self.risk_analysis_engine_prepared,
            "evidence_catalog_preserved": self.evidence_catalog_preserved,
            "source_data_preserved": self.source_data_preserved,
        }


@dataclass(frozen=True)
class EvaluatorResult:
    """Resultado individual de un evaluador de consistencia."""

    evaluator_type: str
    evaluator_name: str
    profiles: tuple[ModelConsistencyProfile, ...] = ()
    technical_observations: tuple[str, ...] = ()


@dataclass(frozen=True)
class ConsistencyEvaluationIncident:
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
class ConsistencyEvaluationRequest:
    """
    Solicitud de evaluación de consistencia.

    El CEE consume exclusivamente el catálogo de evidencias del EAE.
    """

    process_id: UUID
    evidence_catalog: Any
    codigo_req: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ConsistencyEvaluationResult:
    """Resultado uniforme de la evaluación de consistencia."""

    process_id: UUID
    document_id: str
    model_id: str
    catalog: ConsistencyEvaluationCatalog
    status: ConsistencyEvaluationStatus
    inconsistencies_count: int
    sufficient_profiles_count: int
    insufficient_profiles_count: int
    evidence_catalog_preserved: bool
    source_data_preserved: bool
    evaluators_executed: int
    incidents: tuple[ConsistencyEvaluationIncident, ...] = ()
    technical_observations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "document_id": self.document_id,
            "model_id": self.model_id,
            "catalog": self.catalog.to_dict(),
            "status": self.status.value,
            "inconsistencies_count": self.inconsistencies_count,
            "sufficient_profiles_count": self.sufficient_profiles_count,
            "insufficient_profiles_count": self.insufficient_profiles_count,
            "evidence_catalog_preserved": self.evidence_catalog_preserved,
            "source_data_preserved": self.source_data_preserved,
            "evaluators_executed": self.evaluators_executed,
            "incidents": [incident.to_dict() for incident in self.incidents],
            "technical_observations": list(self.technical_observations),
        }
