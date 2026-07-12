"""Modelos del Evidence Analysis Engine — catálogo de evidencias organizadas."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from zovrake_motor.intelligent_analysis.evidence_analysis_engine.enums import (
    EvidenceAnalysisStatus,
    EvidenceCategory,
    EvidencePresenceStatus,
)


@dataclass(frozen=True)
class EvidenceTraceabilityReference:
    """Referencia de trazabilidad preservada — sin modificación de origen."""

    document_id: str
    definitive_model_id: str
    group_id: str
    comparative_table_id: str
    provider_id: str | None
    source_field: str
    traceability: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "definitive_model_id": self.definitive_model_id,
            "group_id": self.group_id,
            "comparative_table_id": self.comparative_table_id,
            "provider_id": self.provider_id,
            "source_field": self.source_field,
            "traceability": self.traceability,
        }


@dataclass(frozen=True)
class EvidenceRecord:
    """Evidencia identificada — valor literal sin interpretación."""

    evidence_id: str
    evidence_category: EvidenceCategory
    evidence_key: str
    evidence_value: Any
    presence_status: EvidencePresenceStatus
    provider_id: str | None
    traceability_ref: EvidenceTraceabilityReference
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "evidence_category": self.evidence_category.value,
            "evidence_key": self.evidence_key,
            "evidence_value": self.evidence_value,
            "presence_status": self.presence_status.value,
            "provider_id": self.provider_id,
            "traceability_ref": self.traceability_ref.to_dict(),
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class MissingEvidenceRecord:
    """Ausencia de evidencia registrada — sin completar datos."""

    missing_evidence_id: str
    evidence_category: EvidenceCategory
    expected_key: str
    provider_id: str | None
    definitive_model_id: str
    group_id: str
    document_id: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "missing_evidence_id": self.missing_evidence_id,
            "evidence_category": self.evidence_category.value,
            "expected_key": self.expected_key,
            "provider_id": self.provider_id,
            "definitive_model_id": self.definitive_model_id,
            "group_id": self.group_id,
            "document_id": self.document_id,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class ModelEvidenceProfile:
    """Perfil de evidencias organizadas por Modelo Comparativo Definitivo."""

    definitive_model_id: str
    comparative_table_id: str
    group_id: str
    group_type: str
    evidence_records: tuple[EvidenceRecord, ...]
    missing_evidence_records: tuple[MissingEvidenceRecord, ...]
    categories_present: tuple[str, ...]
    categories_missing: tuple[str, ...]
    confidence_level_available: str
    source_data_preserved: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "definitive_model_id": self.definitive_model_id,
            "comparative_table_id": self.comparative_table_id,
            "group_id": self.group_id,
            "group_type": self.group_type,
            "evidence_records": [record.to_dict() for record in self.evidence_records],
            "evidence_records_count": len(self.evidence_records),
            "missing_evidence_records": [
                record.to_dict() for record in self.missing_evidence_records
            ],
            "missing_evidence_records_count": len(self.missing_evidence_records),
            "categories_present": list(self.categories_present),
            "categories_missing": list(self.categories_missing),
            "confidence_level_available": self.confidence_level_available,
            "source_data_preserved": self.source_data_preserved,
        }


@dataclass(frozen=True)
class EvidenceAnalysisCatalog:
    """Catálogo de evidencias analizadas del proceso."""

    catalog_id: str
    process_id: UUID
    model_id: str
    document_id: str
    source_definitive_catalog_id: str
    profiles: tuple[ModelEvidenceProfile, ...]
    consistency_evaluation_engine_prepared: bool = True
    definitive_catalog_preserved: bool = True
    source_data_preserved: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "catalog_id": self.catalog_id,
            "process_id": str(self.process_id),
            "model_id": self.model_id,
            "document_id": self.document_id,
            "source_definitive_catalog_id": self.source_definitive_catalog_id,
            "profiles": [profile.to_dict() for profile in self.profiles],
            "profiles_count": len(self.profiles),
            "consistency_evaluation_engine_prepared": self.consistency_evaluation_engine_prepared,
            "definitive_catalog_preserved": self.definitive_catalog_preserved,
            "source_data_preserved": self.source_data_preserved,
        }


@dataclass(frozen=True)
class AnalyzerResult:
    """Resultado individual de un analizador de evidencias."""

    analyzer_type: str
    analyzer_name: str
    profiles: tuple[ModelEvidenceProfile, ...] = ()
    technical_observations: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvidenceAnalysisIncident:
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
class EvidenceAnalysisRequest:
    """
    Solicitud de análisis de evidencias.

    El EAE consume exclusivamente el Modelo Comparativo Definitivo (PM6).
    """

    process_id: UUID
    definitive_catalog: dict[str, Any]
    codigo_req: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EvidenceAnalysisResult:
    """Resultado uniforme del análisis de evidencias."""

    process_id: UUID
    document_id: str
    model_id: str
    catalog: EvidenceAnalysisCatalog
    status: EvidenceAnalysisStatus
    evidence_records_count: int
    missing_evidence_records_count: int
    definitive_catalog_preserved: bool
    source_data_preserved: bool
    analyzers_executed: int
    incidents: tuple[EvidenceAnalysisIncident, ...] = ()
    technical_observations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "process_id": str(self.process_id),
            "document_id": self.document_id,
            "model_id": self.model_id,
            "catalog": self.catalog.to_dict(),
            "status": self.status.value,
            "evidence_records_count": self.evidence_records_count,
            "missing_evidence_records_count": self.missing_evidence_records_count,
            "definitive_catalog_preserved": self.definitive_catalog_preserved,
            "source_data_preserved": self.source_data_preserved,
            "analyzers_executed": self.analyzers_executed,
            "incidents": [incident.to_dict() for incident in self.incidents],
            "technical_observations": list(self.technical_observations),
        }
