"""Modelos del Recommendation Generation Engine — recomendaciones trazables."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from zovrake_motor.intelligent_analysis.recommendation_generation_engine.enums import (
    ConfidenceLevel,
    RecommendationGenerationStatus,
    RecommendationScenarioType,
)


@dataclass(frozen=True)
class RecommendationTraceabilityReference:
    """Referencia de trazabilidad de una recomendación."""

    evidence_id: str | None
    risk_id: str | None
    inconsistency_id: str | None
    missing_evidence_id: str | None
    explanation_segment_id: str | None
    definitive_model_id: str
    group_id: str
    comparative_table_id: str
    provider_id: str | None
    document_id: str
    traceability: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "risk_id": self.risk_id,
            "inconsistency_id": self.inconsistency_id,
            "missing_evidence_id": self.missing_evidence_id,
            "explanation_segment_id": self.explanation_segment_id,
            "definitive_model_id": self.definitive_model_id,
            "group_id": self.group_id,
            "comparative_table_id": self.comparative_table_id,
            "provider_id": self.provider_id,
            "document_id": self.document_id,
            "traceability": self.traceability,
        }


@dataclass(frozen=True)
class ProviderAlternativeRecord:
    """Alternativa equivalente documentada — Escenario B."""

    provider_id: str
    strengths: tuple[str, ...]
    relevant_differences: tuple[str, ...]
    supporting_evidence_ids: tuple[str, ...]
    evidence_score: float
    risk_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "strengths": list(self.strengths),
            "relevant_differences": list(self.relevant_differences),
            "supporting_evidence_ids": list(self.supporting_evidence_ids),
            "evidence_score": self.evidence_score,
            "risk_count": self.risk_count,
        }


@dataclass(frozen=True)
class RecommendationJustificationRecord:
    """Justificación estructurada de la recomendación."""

    why_issued: str
    supporting_evidence_ids: tuple[str, ...]
    remaining_risk_ids: tuple[str, ...]
    limitations: tuple[str, ...]
    missing_information: tuple[str, ...]
    structured_content: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "why_issued": self.why_issued,
            "supporting_evidence_ids": list(self.supporting_evidence_ids),
            "remaining_risk_ids": list(self.remaining_risk_ids),
            "limitations": list(self.limitations),
            "missing_information": list(self.missing_information),
            "structured_content": self.structured_content,
        }


@dataclass(frozen=True)
class ModelRecommendationProfile:
    """Perfil de recomendación por Modelo Comparativo Definitivo."""

    definitive_model_id: str
    comparative_table_id: str
    group_id: str
    group_type: str
    scenario_type: RecommendationScenarioType
    confidence_level: ConfidenceLevel
    recommended_provider_id: str | None
    justification: RecommendationJustificationRecord
    primary_strengths: tuple[str, ...]
    identified_risks: tuple[str, ...]
    limitations: tuple[str, ...]
    equivalent_alternatives: tuple[ProviderAlternativeRecord, ...]
    suggested_actions: tuple[str, ...]
    missing_documentation: tuple[str, ...]
    supporting_evidence_ids: tuple[str, ...]
    traceability_ref: RecommendationTraceabilityReference
    confidence_factors: dict[str, Any]
    source_data_preserved: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "definitive_model_id": self.definitive_model_id,
            "comparative_table_id": self.comparative_table_id,
            "group_id": self.group_id,
            "group_type": self.group_type,
            "scenario_type": self.scenario_type.value,
            "confidence_level": self.confidence_level.value,
            "recommended_provider_id": self.recommended_provider_id,
            "justification": self.justification.to_dict(),
            "primary_strengths": list(self.primary_strengths),
            "identified_risks": list(self.identified_risks),
            "limitations": list(self.limitations),
            "equivalent_alternatives": [alt.to_dict() for alt in self.equivalent_alternatives],
            "equivalent_alternatives_count": len(self.equivalent_alternatives),
            "suggested_actions": list(self.suggested_actions),
            "missing_documentation": list(self.missing_documentation),
            "supporting_evidence_ids": list(self.supporting_evidence_ids),
            "traceability_ref": self.traceability_ref.to_dict(),
            "confidence_factors": self.confidence_factors,
            "source_data_preserved": self.source_data_preserved,
        }


@dataclass(frozen=True)
class RecommendationGenerationCatalog:
    """Catálogo de recomendaciones generadas del proceso."""

    catalog_id: str
    process_id: UUID
    model_id: str
    document_id: str
    source_evidence_catalog_id: str
    source_consistency_catalog_id: str
    source_risk_catalog_id: str
    source_context_catalog_id: str
    source_explanation_catalog_id: str
    source_definitive_catalog_id: str
    profiles: tuple[ModelRecommendationProfile, ...]
    reasoning_result_builder_prepared: bool = True
    evidence_catalog_preserved: bool = True
    consistency_catalog_preserved: bool = True
    risk_catalog_preserved: bool = True
    context_catalog_preserved: bool = True
    explanation_catalog_preserved: bool = True
    definitive_catalog_preserved: bool = True
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
            "source_context_catalog_id": self.source_context_catalog_id,
            "source_explanation_catalog_id": self.source_explanation_catalog_id,
            "source_definitive_catalog_id": self.source_definitive_catalog_id,
            "profiles": [profile.to_dict() for profile in self.profiles],
            "profiles_count": len(self.profiles),
            "reasoning_result_builder_prepared": self.reasoning_result_builder_prepared,
            "evidence_catalog_preserved": self.evidence_catalog_preserved,
            "consistency_catalog_preserved": self.consistency_catalog_preserved,
            "risk_catalog_preserved": self.risk_catalog_preserved,
            "context_catalog_preserved": self.context_catalog_preserved,
            "explanation_catalog_preserved": self.explanation_catalog_preserved,
            "definitive_catalog_preserved": self.definitive_catalog_preserved,
            "source_data_preserved": self.source_data_preserved,
        }


@dataclass(frozen=True)
class GeneratorResult:
    """Resultado individual de un generador de recomendaciones."""

    generator_type: str
    generator_name: str
    profiles: tuple[ModelRecommendationProfile, ...] = ()
    technical_observations: tuple[str, ...] = ()


@dataclass(frozen=True)
class RecommendationGenerationIncident:
    """Incidencia estructural durante la generación."""

    generator_name: str
    message: str
    severity: str = "info"

    def to_dict(self) -> dict[str, Any]:
        return {
            "generator_name": self.generator_name,
            "message": self.message,
            "severity": self.severity,
        }


@dataclass(frozen=True)
class RecommendationGenerationRequest:
    """
    Solicitud de generación de recomendaciones.

    El RGE consume exclusivamente salidas del EAE, CEE, RAE, CxEE, EGE
    y Modelo Comparativo Definitivo.
    """

    process_id: UUID
    evidence_catalog: Any
    consistency_catalog: Any
    risk_catalog: Any
    context_catalog: Any
    explanation_catalog: Any
    definitive_catalog: dict[str, Any]
    codigo_req: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RecommendationGenerationResult:
    """Resultado uniforme de la generación de recomendaciones."""

    process_id: UUID
    document_id: str
    model_id: str
    catalog: RecommendationGenerationCatalog
    status: RecommendationGenerationStatus
    recommendations_count: int
    evidence_catalog_preserved: bool
    consistency_catalog_preserved: bool
    risk_catalog_preserved: bool
    context_catalog_preserved: bool
    explanation_catalog_preserved: bool
    definitive_catalog_preserved: bool
    source_data_preserved: bool
    generators_executed: int
    incidents: tuple[RecommendationGenerationIncident, ...] = ()
    technical_observations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "document_id": self.document_id,
            "model_id": self.model_id,
            "catalog": self.catalog.to_dict(),
            "status": self.status.value,
            "recommendations_count": self.recommendations_count,
            "evidence_catalog_preserved": self.evidence_catalog_preserved,
            "consistency_catalog_preserved": self.consistency_catalog_preserved,
            "risk_catalog_preserved": self.risk_catalog_preserved,
            "context_catalog_preserved": self.context_catalog_preserved,
            "explanation_catalog_preserved": self.explanation_catalog_preserved,
            "definitive_catalog_preserved": self.definitive_catalog_preserved,
            "source_data_preserved": self.source_data_preserved,
            "generators_executed": self.generators_executed,
            "incidents": [incident.to_dict() for incident in self.incidents],
            "technical_observations": list(self.technical_observations),
        }
