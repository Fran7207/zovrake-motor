"""Gateway de consumo del catálogo de equivalencias del EDE."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from zovrake_motor.classification.comparable_group_builder.exceptions import EquivalenceCatalogAccessError
from zovrake_motor.classification.equivalence_detection.enums import EquivalenceRelationType
from zovrake_motor.classification.equivalence_detection.models import (
    EquivalenceCatalog,
    EquivalenceExplainability,
    EquivalenceRecord,
    EquivalenceTraceability,
)


@dataclass(frozen=True)
class EquivalenceCatalogView:
    """Vista de solo lectura del catálogo de equivalencias."""

    catalog_id: str
    process_id: UUID
    model_id: str
    document_id: str
    source_normalized_catalog_id: str
    equivalences: tuple[EquivalenceRecord, ...]
    equivalent_relations: tuple[EquivalenceRecord, ...]
    comparable_relations: tuple[EquivalenceRecord, ...]
    raw_catalog: dict[str, Any]
    document_ids: tuple[str, ...] = ()


def _parse_equivalence(payload: dict[str, Any]) -> EquivalenceRecord:
    explainability_raw = payload.get("explainability", {})
    traceability_raw = payload.get("traceability", {})

    return EquivalenceRecord(
        equivalence_id=str(payload["equivalence_id"]),
        involved_concept_ids=tuple(payload.get("involved_concept_ids", [])),
        relation_type=str(payload.get("relation_type", "")),
        evidence_level=str(payload.get("evidence_level", "")),
        status=str(payload.get("status", "")),
        detector_type=str(payload.get("detector_type", "")),
        explainability=EquivalenceExplainability(
            criteria_used=tuple(explainability_raw.get("criteria_used", [])),
            information_used=tuple(explainability_raw.get("information_used", [])),
            limitations=tuple(explainability_raw.get("limitations", [])),
            rationale=str(explainability_raw.get("rationale", "")),
        ),
        traceability=EquivalenceTraceability(
            process_id=UUID(str(traceability_raw["process_id"])),
            document_id=str(traceability_raw.get("document_id", "")),
            document_ids=tuple(traceability_raw.get("document_ids", [])),
            model_id=str(traceability_raw.get("model_id", "")),
            source_normalized_catalog_id=str(traceability_raw.get("source_normalized_catalog_id", "")),
            concept_ids=tuple(traceability_raw.get("concept_ids", [])),
            document_reference=str(traceability_raw.get("document_reference", "")),
            canonical_reference=str(traceability_raw.get("canonical_reference", "")),
            original_preserved=bool(traceability_raw.get("original_preserved", True)),
        ),
        metadata=dict(payload.get("metadata", {})),
    )


class EquivalenceCatalogGateway:
    """
    Gateway de consumo del catálogo de equivalencias para el CGB.

    Valida preparación para construcción de grupos sin acceder al documento original.
    """

    REQUIRED_FIELDS: tuple[str, ...] = (
        "catalog_id",
        "process_id",
        "model_id",
        "document_id",
        "equivalences",
    )

    def validate(self, catalog_dict: dict[str, Any]) -> EquivalenceCatalogView:
        if not isinstance(catalog_dict, dict):
            raise EquivalenceCatalogAccessError("El catálogo de equivalencias debe ser un diccionario")

        missing = [field for field in self.REQUIRED_FIELDS if field not in catalog_dict]
        if missing:
            raise EquivalenceCatalogAccessError(
                f"Campos obligatorios ausentes en catálogo de equivalencias: {', '.join(missing)}",
            )

        if not bool(catalog_dict.get("comparable_group_builder_prepared", True)):
            raise EquivalenceCatalogAccessError(
                "El catálogo de equivalencias no está preparado para construcción de grupos",
            )

        equivalences_raw = catalog_dict.get("equivalences", [])
        if not isinstance(equivalences_raw, list):
            raise EquivalenceCatalogAccessError("equivalences debe ser una lista")

        equivalences = tuple(_parse_equivalence(item) for item in equivalences_raw)
        equivalent_relations = tuple(
            equivalence
            for equivalence in equivalences
            if equivalence.relation_type == EquivalenceRelationType.EQUIVALENT.value
        )
        comparable_relations = tuple(
            equivalence
            for equivalence in equivalences
            if equivalence.relation_type
            in {
                EquivalenceRelationType.EQUIVALENT.value,
                EquivalenceRelationType.COMPARABLE.value,
            }
            and bool(
                equivalence.metadata.get(
                    "semantic_comparable_candidate",
                    equivalence.relation_type == EquivalenceRelationType.EQUIVALENT.value,
                )
            )
        )

        catalog = EquivalenceCatalog(
            catalog_id=str(catalog_dict["catalog_id"]),
            process_id=UUID(str(catalog_dict["process_id"])),
            model_id=str(catalog_dict["model_id"]),
            document_id=str(catalog_dict["document_id"]),
            source_normalized_catalog_id=str(catalog_dict.get("source_normalized_catalog_id", "")),
            equivalences=equivalences,
            comparable_group_builder_prepared=True,
        )

        return EquivalenceCatalogView(
            catalog_id=catalog.catalog_id,
            process_id=catalog.process_id,
            model_id=catalog.model_id,
            document_id=catalog.document_id,
            source_normalized_catalog_id=catalog.source_normalized_catalog_id,
            equivalences=equivalences,
            equivalent_relations=equivalent_relations,
            comparable_relations=comparable_relations,
            raw_catalog=catalog_dict,
            document_ids=tuple(catalog_dict.get("document_ids", []))
            or tuple(
                sorted(
                    {
                        document_id
                        for equivalence in equivalences
                        for document_id in (
                            *equivalence.traceability.document_ids,
                            equivalence.traceability.document_id,
                        )
                        if document_id
                    }
                )
            ),
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            "access_mode": "read_only",
            "modifies_equivalence_catalog": False,
            "accesses_original_documents": False,
            "required_fields": list(self.REQUIRED_FIELDS),
        }