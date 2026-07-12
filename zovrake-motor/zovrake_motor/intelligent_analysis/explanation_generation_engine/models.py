"""Modelos del Explanation Generation Engine — explicaciones estructuradas y trazables."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from zovrake_motor.intelligent_analysis.explanation_generation_engine.enums import (
    ExplanationGenerationStatus,
    ExplanationSectionType,
)


@dataclass(frozen=True)
class ExplanationTraceabilityReference:
    """Referencia de trazabilidad de una explicación — sin modificar origen."""

    evidence_id: str | None
    risk_id: str | None
    inconsistency_id: str | None
    missing_evidence_id: str | None
    context_association_id: str | None
    contextual_gap_id: str | None
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
            "context_association_id": self.context_association_id,
            "contextual_gap_id": self.contextual_gap_id,
            "definitive_model_id": self.definitive_model_id,
            "group_id": self.group_id,
            "comparative_table_id": self.comparative_table_id,
            "provider_id": self.provider_id,
            "document_id": self.document_id,
            "traceability": self.traceability,
        }


@dataclass(frozen=True)
class ExplanationSegment:
    """
    Unidad estructurada de explicación — reutilizable para múltiples formatos e idiomas.

    El contenido se expresa como hechos estructurados, no como texto fijo.
    """

    segment_id: str
    section_type: ExplanationSectionType
    subject: str
    structured_content: dict[str, Any]
    supporting_evidence_ids: tuple[str, ...]
    supporting_risk_ids: tuple[str, ...]
    supporting_inconsistency_ids: tuple[str, ...]
    supporting_context_association_ids: tuple[str, ...]
    supporting_contextual_gap_ids: tuple[str, ...]
    provider_ids: tuple[str, ...]
    traceability_ref: ExplanationTraceabilityReference
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "segment_id": self.segment_id,
            "section_type": self.section_type.value,
            "subject": self.subject,
            "structured_content": self.structured_content,
            "supporting_evidence_ids": list(self.supporting_evidence_ids),
            "supporting_risk_ids": list(self.supporting_risk_ids),
            "supporting_inconsistency_ids": list(self.supporting_inconsistency_ids),
            "supporting_context_association_ids": list(self.supporting_context_association_ids),
            "supporting_contextual_gap_ids": list(self.supporting_contextual_gap_ids),
            "provider_ids": list(self.provider_ids),
            "traceability_ref": self.traceability_ref.to_dict(),
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class ModelExplanationProfile:
    """Perfil de explicación por Modelo Comparativo Definitivo."""

    definitive_model_id: str
    comparative_table_id: str
    group_id: str
    group_type: str
    segments: tuple[ExplanationSegment, ...]
    sections_summary: dict[str, int]
    evidence_segments_count: int
    strengths_count: int
    weaknesses_count: int
    risks_count: int
    source_data_preserved: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "definitive_model_id": self.definitive_model_id,
            "comparative_table_id": self.comparative_table_id,
            "group_id": self.group_id,
            "group_type": self.group_type,
            "segments": [segment.to_dict() for segment in self.segments],
            "segments_count": len(self.segments),
            "sections_summary": self.sections_summary,
            "evidence_segments_count": self.evidence_segments_count,
            "strengths_count": self.strengths_count,
            "weaknesses_count": self.weaknesses_count,
            "risks_count": self.risks_count,
            "source_data_preserved": self.source_data_preserved,
        }


@dataclass(frozen=True)
class ExplanationGenerationCatalog:
    """Catálogo de explicaciones generadas del proceso."""

    catalog_id: str
    process_id: UUID
    model_id: str
    document_id: str
    source_evidence_catalog_id: str
    source_consistency_catalog_id: str
    source_risk_catalog_id: str
    source_context_catalog_id: str
    source_definitive_catalog_id: str
    profiles: tuple[ModelExplanationProfile, ...]
    recommendation_generation_engine_prepared: bool = True
    conclusion_generation_engine_prepared: bool = True
    evidence_catalog_preserved: bool = True
    consistency_catalog_preserved: bool = True
    risk_catalog_preserved: bool = True
    context_catalog_preserved: bool = True
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
            "source_definitive_catalog_id": self.source_definitive_catalog_id,
            "profiles": [profile.to_dict() for profile in self.profiles],
            "profiles_count": len(self.profiles),
            "recommendation_generation_engine_prepared": self.recommendation_generation_engine_prepared,
            "conclusion_generation_engine_prepared": self.conclusion_generation_engine_prepared,
            "evidence_catalog_preserved": self.evidence_catalog_preserved,
            "consistency_catalog_preserved": self.consistency_catalog_preserved,
            "risk_catalog_preserved": self.risk_catalog_preserved,
            "context_catalog_preserved": self.context_catalog_preserved,
            "definitive_catalog_preserved": self.definitive_catalog_preserved,
            "source_data_preserved": self.source_data_preserved,
        }


@dataclass(frozen=True)
class GeneratorResult:
    """Resultado individual de un generador de explicaciones."""

    generator_type: str
    generator_name: str
    profiles: tuple[ModelExplanationProfile, ...] = ()
    technical_observations: tuple[str, ...] = ()


@dataclass(frozen=True)
class ExplanationGenerationIncident:
    """Incidencia estructural durante la generación — sin corrección automática."""

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
class ExplanationGenerationRequest:
    """
    Solicitud de generación de explicaciones.

    El EGE consume exclusivamente salidas del EAE, CEE, RAE, CxEE
    y Modelo Comparativo Definitivo.
    """

    process_id: UUID
    evidence_catalog: Any
    consistency_catalog: Any
    risk_catalog: Any
    context_catalog: Any
    definitive_catalog: dict[str, Any]
    codigo_req: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExplanationGenerationResult:
    """Resultado uniforme de la generación de explicaciones."""

    process_id: UUID
    document_id: str
    model_id: str
    catalog: ExplanationGenerationCatalog
    status: ExplanationGenerationStatus
    segments_count: int
    evidence_catalog_preserved: bool
    consistency_catalog_preserved: bool
    risk_catalog_preserved: bool
    context_catalog_preserved: bool
    definitive_catalog_preserved: bool
    source_data_preserved: bool
    generators_executed: int
    incidents: tuple[ExplanationGenerationIncident, ...] = ()
    technical_observations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "document_id": self.document_id,
            "model_id": self.model_id,
            "catalog": self.catalog.to_dict(),
            "status": self.status.value,
            "segments_count": self.segments_count,
            "evidence_catalog_preserved": self.evidence_catalog_preserved,
            "consistency_catalog_preserved": self.consistency_catalog_preserved,
            "risk_catalog_preserved": self.risk_catalog_preserved,
            "context_catalog_preserved": self.context_catalog_preserved,
            "definitive_catalog_preserved": self.definitive_catalog_preserved,
            "source_data_preserved": self.source_data_preserved,
            "generators_executed": self.generators_executed,
            "incidents": [incident.to_dict() for incident in self.incidents],
            "technical_observations": list(self.technical_observations),
        }
