"""Modelos del Risk Analysis Engine — catálogo de riesgos identificados."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from zovrake_motor.intelligent_analysis.risk_analysis_engine.enums import (
    RiskAnalysisStatus,
    RiskCategory,
    RiskStatus,
)


@dataclass(frozen=True)
class RiskTraceabilityReference:
    """Referencia de trazabilidad del riesgo — sin modificar origen."""

    evidence_id: str | None
    inconsistency_id: str | None
    missing_evidence_id: str | None
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
            "inconsistency_id": self.inconsistency_id,
            "missing_evidence_id": self.missing_evidence_id,
            "definitive_model_id": self.definitive_model_id,
            "group_id": self.group_id,
            "comparative_table_id": self.comparative_table_id,
            "provider_id": self.provider_id,
            "document_id": self.document_id,
            "source_field": self.source_field,
            "traceability": self.traceability,
        }


@dataclass(frozen=True)
class RiskRecord:
    """Riesgo identificado — registro sin resolución automática."""

    risk_id: str
    risk_category: RiskCategory
    description: str
    associated_evidence_ids: tuple[str, ...]
    associated_inconsistency_ids: tuple[str, ...]
    associated_missing_evidence_ids: tuple[str, ...]
    provider_ids: tuple[str, ...]
    traceability_ref: RiskTraceabilityReference
    risk_status: RiskStatus
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "risk_id": self.risk_id,
            "risk_category": self.risk_category.value,
            "description": self.description,
            "associated_evidence_ids": list(self.associated_evidence_ids),
            "associated_inconsistency_ids": list(self.associated_inconsistency_ids),
            "associated_missing_evidence_ids": list(self.associated_missing_evidence_ids),
            "provider_ids": list(self.provider_ids),
            "traceability_ref": self.traceability_ref.to_dict(),
            "risk_status": self.risk_status.value,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class ModelRiskProfile:
    """Perfil de riesgos por Modelo Comparativo Definitivo."""

    definitive_model_id: str
    comparative_table_id: str
    group_id: str
    group_type: str
    risks: tuple[RiskRecord, ...]
    risks_by_category: dict[str, int]
    evidence_records_analyzed: int
    inconsistencies_analyzed: int
    source_data_preserved: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "definitive_model_id": self.definitive_model_id,
            "comparative_table_id": self.comparative_table_id,
            "group_id": self.group_id,
            "group_type": self.group_type,
            "risks": [record.to_dict() for record in self.risks],
            "risks_count": len(self.risks),
            "risks_by_category": self.risks_by_category,
            "evidence_records_analyzed": self.evidence_records_analyzed,
            "inconsistencies_analyzed": self.inconsistencies_analyzed,
            "source_data_preserved": self.source_data_preserved,
        }


@dataclass(frozen=True)
class RiskAnalysisCatalog:
    """Catálogo de riesgos analizados del proceso."""

    catalog_id: str
    process_id: UUID
    model_id: str
    document_id: str
    source_evidence_catalog_id: str
    source_consistency_catalog_id: str
    profiles: tuple[ModelRiskProfile, ...]
    context_evaluation_engine_prepared: bool = True
    evidence_catalog_preserved: bool = True
    consistency_catalog_preserved: bool = True
    source_data_preserved: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "catalog_id": self.catalog_id,
            "process_id": str(self.process_id),
            "model_id": self.model_id,
            "document_id": self.document_id,
            "source_evidence_catalog_id": self.source_evidence_catalog_id,
            "source_consistency_catalog_id": self.source_consistency_catalog_id,
            "profiles": [profile.to_dict() for profile in self.profiles],
            "profiles_count": len(self.profiles),
            "context_evaluation_engine_prepared": self.context_evaluation_engine_prepared,
            "evidence_catalog_preserved": self.evidence_catalog_preserved,
            "consistency_catalog_preserved": self.consistency_catalog_preserved,
            "source_data_preserved": self.source_data_preserved,
        }


@dataclass(frozen=True)
class AnalyzerResult:
    """Resultado individual de un analizador de riesgos."""

    analyzer_type: str
    analyzer_name: str
    profiles: tuple[ModelRiskProfile, ...] = ()
    technical_observations: tuple[str, ...] = ()


@dataclass(frozen=True)
class RiskAnalysisIncident:
    """Incidencia estructural durante el análisis — sin corrección automática."""

    analyzer_name: str
    message: str
    severity: str = "info"

    def to_dict(self) -> dict[str, Any]:
        return {
            "analyzer_name": self.analyzer_name,
            "message": self.message,
            "severity": self.severity,
        }


@dataclass(frozen=True)
class RiskAnalysisRequest:
    """
    Solicitud de análisis de riesgos.

    El RAE consume exclusivamente las salidas del EAE y del CEE.
    """

    process_id: UUID
    evidence_catalog: Any
    consistency_catalog: Any
    codigo_req: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RiskAnalysisResult:
    """Resultado uniforme del análisis de riesgos."""

    process_id: UUID
    document_id: str
    model_id: str
    catalog: RiskAnalysisCatalog
    status: RiskAnalysisStatus
    risks_count: int
    evidence_catalog_preserved: bool
    consistency_catalog_preserved: bool
    source_data_preserved: bool
    analyzers_executed: int
    incidents: tuple[RiskAnalysisIncident, ...] = ()
    technical_observations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "document_id": self.document_id,
            "model_id": self.model_id,
            "catalog": self.catalog.to_dict(),
            "status": self.status.value,
            "risks_count": self.risks_count,
            "evidence_catalog_preserved": self.evidence_catalog_preserved,
            "consistency_catalog_preserved": self.consistency_catalog_preserved,
            "source_data_preserved": self.source_data_preserved,
            "analyzers_executed": self.analyzers_executed,
            "incidents": [incident.to_dict() for incident in self.incidents],
            "technical_observations": list(self.technical_observations),
        }
