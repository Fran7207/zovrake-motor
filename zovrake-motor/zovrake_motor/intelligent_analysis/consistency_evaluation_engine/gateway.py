"""Gateway de consumo del catálogo de evidencias del EAE para el CEE."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.exceptions import (
    EvidenceCatalogAccessError,
)
from zovrake_motor.intelligent_analysis.consistency_evaluation_engine.governance import (
    PM7_EVIDENCE_CATALOG_REQUIRED_FIELDS,
    PM7_EVIDENCE_PROFILE_REQUIRED_FIELDS,
)
from zovrake_motor.intelligent_analysis.evidence_analysis_engine.enums import EvidenceCategory
from zovrake_motor.intelligent_analysis.evidence_analysis_engine.models import (
    EvidenceAnalysisCatalog,
    EvidenceRecord,
    EvidenceTraceabilityReference,
    MissingEvidenceRecord,
    ModelEvidenceProfile,
)


@dataclass(frozen=True)
class EvidenceRecordView:
    """Vista de solo lectura de una evidencia identificada por el EAE."""

    evidence_id: str
    evidence_category: EvidenceCategory
    evidence_key: str
    evidence_value: Any
    provider_id: str | None
    traceability_ref: EvidenceTraceabilityReference
    metadata: dict[str, Any]


@dataclass(frozen=True)
class MissingEvidenceRecordView:
    """Vista de solo lectura de una ausencia de evidencia."""

    missing_evidence_id: str
    evidence_category: EvidenceCategory
    expected_key: str
    provider_id: str | None
    definitive_model_id: str
    group_id: str
    document_id: str
    reason: str


@dataclass(frozen=True)
class ModelEvidenceProfileView:
    """Vista de solo lectura del perfil de evidencias de un modelo."""

    definitive_model_id: str
    comparative_table_id: str
    group_id: str
    group_type: str
    evidence_records: tuple[EvidenceRecordView, ...]
    missing_evidence_records: tuple[MissingEvidenceRecordView, ...]
    categories_present: tuple[str, ...]
    categories_missing: tuple[str, ...]
    confidence_level_available: str
    source_data_preserved: bool


@dataclass(frozen=True)
class EvidenceAnalysisCatalogView:
    """Vista de solo lectura del catálogo de evidencias del EAE."""

    catalog_id: str
    process_id: UUID
    model_id: str
    document_id: str
    source_definitive_catalog_id: str
    profiles: tuple[ModelEvidenceProfileView, ...]
    consistency_evaluation_engine_prepared: bool
    definitive_catalog_preserved: bool
    source_data_preserved: bool
    raw_catalog: EvidenceAnalysisCatalog


def _parse_evidence_record(payload: EvidenceRecord) -> EvidenceRecordView:
    return EvidenceRecordView(
        evidence_id=payload.evidence_id,
        evidence_category=payload.evidence_category,
        evidence_key=payload.evidence_key,
        evidence_value=payload.evidence_value,
        provider_id=payload.provider_id,
        traceability_ref=payload.traceability_ref,
        metadata=dict(payload.metadata),
    )


def _parse_missing_record(payload: MissingEvidenceRecord) -> MissingEvidenceRecordView:
    return MissingEvidenceRecordView(
        missing_evidence_id=payload.missing_evidence_id,
        evidence_category=payload.evidence_category,
        expected_key=payload.expected_key,
        provider_id=payload.provider_id,
        definitive_model_id=payload.definitive_model_id,
        group_id=payload.group_id,
        document_id=payload.document_id,
        reason=payload.reason,
    )


def _parse_profile(payload: ModelEvidenceProfile) -> ModelEvidenceProfileView:
    return ModelEvidenceProfileView(
        definitive_model_id=payload.definitive_model_id,
        comparative_table_id=payload.comparative_table_id,
        group_id=payload.group_id,
        group_type=payload.group_type,
        evidence_records=tuple(_parse_evidence_record(record) for record in payload.evidence_records),
        missing_evidence_records=tuple(
            _parse_missing_record(record) for record in payload.missing_evidence_records
        ),
        categories_present=payload.categories_present,
        categories_missing=payload.categories_missing,
        confidence_level_available=payload.confidence_level_available,
        source_data_preserved=payload.source_data_preserved,
    )


def _validate_profile_dict(payload: dict[str, Any]) -> None:
    missing = [field for field in PM7_EVIDENCE_PROFILE_REQUIRED_FIELDS if field not in payload]
    if missing:
        raise EvidenceCatalogAccessError(
            "Campos obligatorios ausentes en perfil de evidencias: " + ", ".join(missing),
        )


def _catalog_to_dict(catalog: EvidenceAnalysisCatalog) -> dict[str, Any]:
    return catalog.to_dict()


class EvidenceAnalysisCatalogGateway:
    """
    Gateway de consumo del catálogo de evidencias del EAE.

    Valida el contrato EAE→CEE sin acceder al Modelo Comparativo Definitivo.
    """

    REQUIRED_FIELDS: tuple[str, ...] = PM7_EVIDENCE_CATALOG_REQUIRED_FIELDS

    def validate(self, catalog: EvidenceAnalysisCatalog) -> EvidenceAnalysisCatalogView:
        if not isinstance(catalog, EvidenceAnalysisCatalog):
            raise EvidenceCatalogAccessError(
                "El catálogo de evidencias debe ser una instancia de EvidenceAnalysisCatalog",
            )

        catalog_dict = _catalog_to_dict(catalog)
        missing = [field for field in self.REQUIRED_FIELDS if field not in catalog_dict]
        if missing:
            raise EvidenceCatalogAccessError(
                "Campos obligatorios ausentes en catálogo de evidencias: " + ", ".join(missing),
            )

        if not bool(catalog.consistency_evaluation_engine_prepared):
            raise EvidenceCatalogAccessError(
                "El catálogo de evidencias no está preparado para evaluación de consistencia",
            )

        if not bool(catalog.definitive_catalog_preserved):
            raise EvidenceCatalogAccessError(
                "El catálogo de evidencias no preserva el Modelo Comparativo Definitivo",
            )

        if not bool(catalog.source_data_preserved):
            raise EvidenceCatalogAccessError(
                "El catálogo de evidencias no preserva los datos de origen",
            )

        if str(catalog.process_id) != str(catalog_dict["process_id"]):
            raise EvidenceCatalogAccessError("process_id inconsistente en catálogo de evidencias")

        profiles = tuple(_parse_profile(profile) for profile in catalog.profiles)

        return EvidenceAnalysisCatalogView(
            catalog_id=catalog.catalog_id,
            process_id=catalog.process_id,
            model_id=catalog.model_id,
            document_id=catalog.document_id,
            source_definitive_catalog_id=catalog.source_definitive_catalog_id,
            profiles=profiles,
            consistency_evaluation_engine_prepared=True,
            definitive_catalog_preserved=True,
            source_data_preserved=True,
            raw_catalog=catalog,
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            "access_mode": "read_only",
            "modifies_evidence_catalog": False,
            "accesses_definitive_model": False,
            "accesses_source_files": False,
            "accesses_intermediate_models": False,
            "required_fields": list(self.REQUIRED_FIELDS),
        }
