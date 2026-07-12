"""Gateway de consumo del catálogo de conceptos normalizados del CNE."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from zovrake_motor.classification.concept_normalization.enums import ConceptNormalizationStatus
from zovrake_motor.classification.concept_normalization.models import (
    NormalizedConceptCatalog,
    NormalizedConceptRecord,
    NormalizedConceptTraceability,
    NormalizedModelReference,
)
from zovrake_motor.classification.equivalence_detection.exceptions import NormalizedCatalogAccessError


@dataclass(frozen=True)
class NormalizedConceptCatalogView:
    """Vista de solo lectura del catálogo de conceptos normalizados."""

    catalog_id: str
    process_id: UUID
    model_id: str
    document_id: str
    concepts: tuple[NormalizedConceptRecord, ...]
    raw_catalog: dict[str, Any]


def _parse_normalized_concept(payload: dict[str, Any]) -> NormalizedConceptRecord:
    model_ref_raw = payload.get("model_reference", {})
    traceability_raw = payload.get("traceability", {})

    return NormalizedConceptRecord(
        normalized_concept_id=str(payload["normalized_concept_id"]),
        original_value=str(payload.get("original_value", "")),
        normalized_value=str(payload.get("normalized_value", "")),
        concept_type=str(payload.get("concept_type", "")),
        source_category=str(payload.get("source_category", "")),
        concept_id=str(payload.get("concept_id", "")),
        model_reference=NormalizedModelReference(
            model_id=str(model_ref_raw.get("model_id", "")),
            document_id=str(model_ref_raw.get("document_id", "")),
            concept_id=str(model_ref_raw.get("concept_id", "")),
            source_record_id=str(model_ref_raw.get("source_record_id", "")),
            source_category=str(model_ref_raw.get("source_category", "")),
        ),
        traceability=NormalizedConceptTraceability(
            process_id=UUID(str(traceability_raw["process_id"])),
            document_id=str(traceability_raw.get("document_id", "")),
            model_id=str(traceability_raw.get("model_id", "")),
            concept_id=str(traceability_raw.get("concept_id", "")),
            source_material_catalog_id=str(traceability_raw.get("source_material_catalog_id", "")),
            source_service_catalog_id=str(traceability_raw.get("source_service_catalog_id", "")),
            document_reference=str(traceability_raw.get("document_reference", "")),
            canonical_reference=str(traceability_raw.get("canonical_reference", "")),
            extraction_reference=str(traceability_raw.get("extraction_reference", "")),
            source_reference=str(traceability_raw.get("source_reference", "")),
            adapter_name=str(traceability_raw.get("adapter_name", "")),
            format_type=str(traceability_raw.get("format_type", "")),
            original_preserved=bool(traceability_raw.get("original_preserved", True)),
        ),
        status=ConceptNormalizationStatus(str(payload.get("status", "normalized"))),
        metadata=dict(payload.get("metadata", {})),
    )


class NormalizedConceptCatalogGateway:
    """
    Gateway de consumo del catálogo normalizado para el EDE.

    Valida preparación para detección de equivalencias sin acceder al documento original.
    """

    REQUIRED_FIELDS: tuple[str, ...] = (
        "catalog_id",
        "process_id",
        "model_id",
        "document_id",
        "concepts",
    )

    def validate(self, catalog_dict: dict[str, Any]) -> NormalizedConceptCatalogView:
        if not isinstance(catalog_dict, dict):
            raise NormalizedCatalogAccessError("El catálogo normalizado debe ser un diccionario")

        missing = [field for field in self.REQUIRED_FIELDS if field not in catalog_dict]
        if missing:
            raise NormalizedCatalogAccessError(
                f"Campos obligatorios ausentes en catálogo normalizado: {', '.join(missing)}",
            )

        if not bool(catalog_dict.get("equivalence_detection_prepared", True)):
            raise NormalizedCatalogAccessError(
                "El catálogo normalizado no está preparado para detección de equivalencias",
            )

        concepts_raw = catalog_dict.get("concepts", [])
        if not isinstance(concepts_raw, list):
            raise NormalizedCatalogAccessError("concepts debe ser una lista")

        concepts = tuple(_parse_normalized_concept(item) for item in concepts_raw)
        catalog = NormalizedConceptCatalog(
            catalog_id=str(catalog_dict["catalog_id"]),
            process_id=UUID(str(catalog_dict["process_id"])),
            model_id=str(catalog_dict["model_id"]),
            document_id=str(catalog_dict["document_id"]),
            source_material_catalog_id=str(catalog_dict.get("source_material_catalog_id", "")),
            source_service_catalog_id=str(catalog_dict.get("source_service_catalog_id", "")),
            concepts=concepts,
            equivalence_detection_prepared=True,
        )

        return NormalizedConceptCatalogView(
            catalog_id=catalog.catalog_id,
            process_id=catalog.process_id,
            model_id=catalog.model_id,
            document_id=catalog.document_id,
            concepts=concepts,
            raw_catalog=catalog_dict,
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            "access_mode": "read_only",
            "modifies_normalized_catalog": False,
            "accesses_original_documents": False,
            "required_fields": list(self.REQUIRED_FIELDS),
        }
