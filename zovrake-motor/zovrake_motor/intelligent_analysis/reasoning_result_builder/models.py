"""Modelos del Reasoning Result Builder — contrato oficial del PM7."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from zovrake_motor.intelligent_analysis.reasoning_result_builder.enums import (
    ReasoningResultBuildStatus,
)
from zovrake_motor.intelligent_analysis.reasoning_result_builder.governance import (
    PM7_OUTPUT_CATALOG_CONTRACT_NAME,
    PM7_OUTPUT_CATALOG_CONTRACT_VERSION,
    PM7_OUTPUT_CONTRACT_NAME,
    PM7_OUTPUT_CONTRACT_VERSION,
)


@dataclass(frozen=True)
class DocumentTraceabilityRecord:
    """Referencias de trazabilidad documental consolidadas."""

    evidence_ids: tuple[str, ...]
    risk_ids: tuple[str, ...]
    inconsistency_ids: tuple[str, ...]
    missing_evidence_ids: tuple[str, ...]
    explanation_segment_ids: tuple[str, ...]
    context_association_ids: tuple[str, ...]
    contextual_gap_ids: tuple[str, ...]
    provider_ids: tuple[str, ...]
    definitive_model_id: str
    group_id: str
    comparative_table_id: str
    document_id: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_ids": list(self.evidence_ids),
            "risk_ids": list(self.risk_ids),
            "inconsistency_ids": list(self.inconsistency_ids),
            "missing_evidence_ids": list(self.missing_evidence_ids),
            "explanation_segment_ids": list(self.explanation_segment_ids),
            "context_association_ids": list(self.context_association_ids),
            "contextual_gap_ids": list(self.contextual_gap_ids),
            "provider_ids": list(self.provider_ids),
            "definitive_model_id": self.definitive_model_id,
            "group_id": self.group_id,
            "comparative_table_id": self.comparative_table_id,
            "document_id": self.document_id,
        }


@dataclass(frozen=True)
class GroupIntelligentAnalysisResult:
    """
    Resultado del Análisis Inteligente por Grupo Comparable.

    Contrato oficial de salida del Prompt Maestro 7 — inmutable y trazable.
    """

    result_id: str
    group_id: str
    definitive_model_id: str
    comparative_table_id: str
    group_type: str
    executive_summary: dict[str, Any]
    structured_explanation: dict[str, Any]
    recommendation: dict[str, Any]
    confidence_level: str
    strengths: tuple[str, ...]
    weaknesses: tuple[str, ...]
    risks: tuple[str, ...]
    limitations: tuple[str, ...]
    context_considered: dict[str, Any]
    document_traceability: DocumentTraceabilityRecord
    analysis_metadata: dict[str, Any]
    source_data_preserved: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "result_id": self.result_id,
            "contract_name": PM7_OUTPUT_CONTRACT_NAME,
            "contract_version": PM7_OUTPUT_CONTRACT_VERSION,
            "group_id": self.group_id,
            "definitive_model_id": self.definitive_model_id,
            "comparative_table_id": self.comparative_table_id,
            "group_type": self.group_type,
            "executive_summary": self.executive_summary,
            "structured_explanation": self.structured_explanation,
            "recommendation": self.recommendation,
            "confidence_level": self.confidence_level,
            "strengths": list(self.strengths),
            "weaknesses": list(self.weaknesses),
            "risks": list(self.risks),
            "limitations": list(self.limitations),
            "context_considered": self.context_considered,
            "document_traceability": self.document_traceability.to_dict(),
            "analysis_metadata": self.analysis_metadata,
            "source_data_preserved": self.source_data_preserved,
        }


@dataclass(frozen=True)
class IntelligentAnalysisResultCatalog:
    """Catálogo de Resultados del Análisis Inteligente del proceso."""

    catalog_id: str
    process_id: UUID
    model_id: str
    document_id: str
    source_evidence_catalog_id: str
    source_consistency_catalog_id: str
    source_risk_catalog_id: str
    source_context_catalog_id: str
    source_explanation_catalog_id: str
    source_recommendation_catalog_id: str
    source_definitive_catalog_id: str
    results: tuple[GroupIntelligentAnalysisResult, ...]
    integration_certification_framework_prepared: bool = True
    evidence_catalog_preserved: bool = True
    consistency_catalog_preserved: bool = True
    risk_catalog_preserved: bool = True
    context_catalog_preserved: bool = True
    explanation_catalog_preserved: bool = True
    recommendation_catalog_preserved: bool = True
    definitive_catalog_preserved: bool = True
    source_data_preserved: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "catalog_id": self.catalog_id,
            "contract_name": PM7_OUTPUT_CATALOG_CONTRACT_NAME,
            "contract_version": PM7_OUTPUT_CATALOG_CONTRACT_VERSION,
            "process_id": str(self.process_id),
            "model_id": self.model_id,
            "document_id": self.document_id,
            "source_evidence_catalog_id": self.source_evidence_catalog_id,
            "source_consistency_catalog_id": self.source_consistency_catalog_id,
            "source_risk_catalog_id": self.source_risk_catalog_id,
            "source_context_catalog_id": self.source_context_catalog_id,
            "source_explanation_catalog_id": self.source_explanation_catalog_id,
            "source_recommendation_catalog_id": self.source_recommendation_catalog_id,
            "source_definitive_catalog_id": self.source_definitive_catalog_id,
            "results": [result.to_dict() for result in self.results],
            "results_count": len(self.results),
            "integration_certification_framework_prepared": (
                self.integration_certification_framework_prepared
            ),
            "evidence_catalog_preserved": self.evidence_catalog_preserved,
            "consistency_catalog_preserved": self.consistency_catalog_preserved,
            "risk_catalog_preserved": self.risk_catalog_preserved,
            "context_catalog_preserved": self.context_catalog_preserved,
            "explanation_catalog_preserved": self.explanation_catalog_preserved,
            "recommendation_catalog_preserved": self.recommendation_catalog_preserved,
            "definitive_catalog_preserved": self.definitive_catalog_preserved,
            "source_data_preserved": self.source_data_preserved,
        }


@dataclass(frozen=True)
class BuilderResult:
    """Resultado individual de un constructor."""

    builder_type: str
    builder_name: str
    results: tuple[GroupIntelligentAnalysisResult, ...] = ()
    technical_observations: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReasoningResultBuildIncident:
    """Incidencia estructural durante la construcción."""

    builder_name: str
    message: str
    severity: str = "info"

    def to_dict(self) -> dict[str, Any]:
        return {
            "builder_name": self.builder_name,
            "message": self.message,
            "severity": self.severity,
        }


@dataclass(frozen=True)
class ReasoningResultBuildRequest:
    """
    Solicitud de construcción del Resultado del Análisis Inteligente.

    El RRB consume exclusivamente salidas de EAE, CEE, RAE, CxEE, EGE y RGE.
    """

    process_id: UUID
    evidence_catalog: Any
    consistency_catalog: Any
    risk_catalog: Any
    context_catalog: Any
    explanation_catalog: Any
    recommendation_catalog: Any
    definitive_catalog: dict[str, Any]
    codigo_req: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ReasoningResultBuildResult:
    """Resultado uniforme de la construcción del Resultado del Análisis Inteligente."""

    process_id: UUID
    document_id: str
    model_id: str
    catalog: IntelligentAnalysisResultCatalog
    status: ReasoningResultBuildStatus
    results_count: int
    evidence_catalog_preserved: bool
    consistency_catalog_preserved: bool
    risk_catalog_preserved: bool
    context_catalog_preserved: bool
    explanation_catalog_preserved: bool
    recommendation_catalog_preserved: bool
    definitive_catalog_preserved: bool
    source_data_preserved: bool
    builders_executed: int
    incidents: tuple[ReasoningResultBuildIncident, ...] = ()
    technical_observations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "document_id": self.document_id,
            "model_id": self.model_id,
            "catalog": self.catalog.to_dict(),
            "status": self.status.value,
            "results_count": self.results_count,
            "evidence_catalog_preserved": self.evidence_catalog_preserved,
            "consistency_catalog_preserved": self.consistency_catalog_preserved,
            "risk_catalog_preserved": self.risk_catalog_preserved,
            "context_catalog_preserved": self.context_catalog_preserved,
            "explanation_catalog_preserved": self.explanation_catalog_preserved,
            "recommendation_catalog_preserved": self.recommendation_catalog_preserved,
            "definitive_catalog_preserved": self.definitive_catalog_preserved,
            "source_data_preserved": self.source_data_preserved,
            "builders_executed": self.builders_executed,
            "incidents": [incident.to_dict() for incident in self.incidents],
            "technical_observations": list(self.technical_observations),
        }
