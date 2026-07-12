"""Gateway de consumo del catálogo de conceptos del CAE para clasificación de servicios."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from zovrake_motor.classification.concept_analysis.enums import ConceptKind
from zovrake_motor.classification.concept_analysis.models import (
    ConceptCandidate,
    ConceptCatalog,
    ConceptLocation,
    ConceptTraceability,
)
from zovrake_motor.classification.service_classification.exceptions import ConceptCatalogAccessError

MATERIAL_CONCEPT_KINDS = frozenset({ConceptKind.ITEM, ConceptKind.PARTIDA})


@dataclass(frozen=True)
class ConceptCatalogView:
    """Vista de solo lectura del catálogo de conceptos del CAE."""

    catalog_id: str
    process_id: UUID
    model_id: str
    document_id: str
    concepts: tuple[ConceptCandidate, ...]
    raw_catalog: dict[str, Any]

    def service_candidate_concepts(self) -> tuple[ConceptCandidate, ...]:
        return tuple(
            concept for concept in self.concepts if concept.kind not in MATERIAL_CONCEPT_KINDS
        )


class ConceptCatalogGateway:
    """
    Gateway de consumo del catálogo de conceptos para el SCE.

    Valida preparación para clasificación de servicios sin acceder al documento original.
    """

    REQUIRED_FIELDS: tuple[str, ...] = (
        "catalog_id",
        "process_id",
        "model_id",
        "document_id",
        "concepts",
    )

    def validate(self, catalog_dict: dict[str, Any]) -> ConceptCatalogView:
        if not isinstance(catalog_dict, dict):
            raise ConceptCatalogAccessError("El catálogo de conceptos debe ser un diccionario")

        missing = [field for field in self.REQUIRED_FIELDS if field not in catalog_dict]
        if missing:
            raise ConceptCatalogAccessError(
                f"Campos obligatorios ausentes en el catálogo: {', '.join(missing)}",
            )

        concepts_raw = catalog_dict.get("concepts", [])
        if not isinstance(concepts_raw, list):
            raise ConceptCatalogAccessError("concepts debe ser una lista")

        concepts = tuple(self._parse_concept(item) for item in concepts_raw)
        catalog = ConceptCatalog(
            catalog_id=str(catalog_dict["catalog_id"]),
            process_id=UUID(str(catalog_dict["process_id"])),
            model_id=str(catalog_dict["model_id"]),
            document_id=str(catalog_dict["document_id"]),
            concepts=concepts,
            material_classification_prepared=bool(
                catalog_dict.get("material_classification_prepared", True),
            ),
            service_classification_prepared=bool(
                catalog_dict.get("service_classification_prepared", True),
            ),
            normalization_prepared=bool(catalog_dict.get("normalization_prepared", True)),
        )

        if not catalog.service_classification_prepared:
            raise ConceptCatalogAccessError(
                "El catálogo no está preparado para clasificación de servicios",
            )

        return ConceptCatalogView(
            catalog_id=catalog.catalog_id,
            process_id=catalog.process_id,
            model_id=catalog.model_id,
            document_id=catalog.document_id,
            concepts=concepts,
            raw_catalog=catalog_dict,
        )

    def _parse_concept(self, payload: dict[str, Any]) -> ConceptCandidate:
        if not isinstance(payload, dict):
            raise ConceptCatalogAccessError("Cada concepto debe ser un diccionario")

        location_raw = payload.get("location", {})
        traceability_raw = payload.get("traceability", {})
        return ConceptCandidate(
            concept_id=str(payload["concept_id"]),
            kind=ConceptKind(str(payload["kind"])),
            original_description=str(payload.get("original_description", "")),
            location=ConceptLocation(
                section=str(location_raw.get("section", "")),
                entity_id=str(location_raw.get("entity_id", "")),
                source_reference=str(location_raw.get("source_reference", "")),
                canonical_reference=str(location_raw.get("canonical_reference", "")),
                extraction_reference=str(location_raw.get("extraction_reference", "")),
                entity_index=location_raw.get("entity_index"),
                field_name=str(location_raw.get("field_name", "")),
            ),
            traceability=ConceptTraceability(
                process_id=UUID(str(traceability_raw["process_id"])),
                document_id=str(traceability_raw.get("document_id", "")),
                model_id=str(traceability_raw.get("model_id", "")),
                document_reference=str(traceability_raw.get("document_reference", "")),
                adapter_name=str(traceability_raw.get("adapter_name", "")),
                format_type=str(traceability_raw.get("format_type", "")),
                original_preserved=bool(traceability_raw.get("original_preserved", True)),
            ),
            metadata=dict(payload.get("metadata", {})),
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            "access_mode": "read_only",
            "modifies_concept_catalog": False,
            "accesses_original_documents": False,
            "excludes_material_concept_kinds": [kind.value for kind in MATERIAL_CONCEPT_KINDS],
            "required_fields": list(self.REQUIRED_FIELDS),
        }
