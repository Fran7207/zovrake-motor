"""Utilidades de construcción de equivalencias y trazabilidad."""

from __future__ import annotations

from typing import Any

from zovrake_motor.classification.concept_normalization.models import (
    NormalizedConceptRecord,
)
from zovrake_motor.classification.equivalence_detection.enums import (
    EquivalenceDetectionStatus,
    EquivalenceRelationType,
    EvidenceLevel,
)
from zovrake_motor.classification.equivalence_detection.gateway import (
    NormalizedConceptCatalogView,
)
from zovrake_motor.classification.equivalence_detection.models import (
    EquivalenceCatalog,
    EquivalenceExplainability,
    EquivalenceRecord,
    EquivalenceTraceability,
)


def build_equivalence_id(
    model_id: str,
    sequence: int,
) -> str:
    return f"ede://{model_id}/equivalence-{sequence:04d}"


def build_equivalence_traceability(
    *,
    catalog_view: NormalizedConceptCatalogView,
    concepts: tuple[NormalizedConceptRecord, ...],
) -> EquivalenceTraceability:
    first = concepts[0]
    traceability = first.traceability

    document_ids = tuple(
        dict.fromkeys(
            concept.traceability.document_id
            for concept in concepts
            if concept.traceability.document_id
        )
    )

    return EquivalenceTraceability(
        process_id=traceability.process_id,
        document_id=traceability.document_id,
        document_ids=document_ids,
        model_id=traceability.model_id,
        source_normalized_catalog_id=catalog_view.catalog_id,
        concept_ids=tuple(
            concept.concept_id
            for concept in concepts
        ),
        document_reference=traceability.document_reference,
        canonical_reference=traceability.canonical_reference,
        original_preserved=traceability.original_preserved,
    )


def _semantic_knowledge(
    concept: NormalizedConceptRecord,
) -> dict[str, Any]:
    """
    Obtiene únicamente la vista semántica previamente calculada por CNE.

    No vuelve a leer el documento ni recalcula hechos.
    """
    raw = concept.metadata.get(
        "semantic_knowledge",
        {},
    )

    if not isinstance(
        raw,
        dict,
    ):
        return {}

    return raw


def _unique_non_empty(
    values: Any,
) -> tuple[str, ...]:
    if not isinstance(
        values,
        (list, tuple, set, frozenset),
    ):
        return ()

    return tuple(
        dict.fromkeys(
            str(value).strip()
            for value in values
            if str(value).strip()
        )
    )


def _semantic_provenance(
    concepts: tuple[NormalizedConceptRecord, ...],
) -> dict[str, Any]:
    """
    Construye una huella de procedencia semántica para la equivalencia.

    Se limita a IDs y hechos ya existentes. No introduce inferencias nuevas.
    """
    fact_ids: list[str] = []
    attribute_ids: list[str] = []
    entity_ids: list[str] = []
    evidence_ids: list[str] = []
    facts: list[dict[str, Any]] = []

    for concept in concepts:
        semantic = _semantic_knowledge(
            concept
        )

        fact_ids.extend(
            _unique_non_empty(
                semantic.get(
                    "fact_ids",
                    (),
                )
            )
        )
        attribute_ids.extend(
            _unique_non_empty(
                semantic.get(
                    "attribute_ids",
                    (),
                )
            )
        )
        entity_ids.extend(
            _unique_non_empty(
                semantic.get(
                    "entity_ids",
                    (),
                )
            )
        )
        evidence_ids.extend(
            _unique_non_empty(
                semantic.get(
                    "evidence_ids",
                    (),
                )
            )
        )

        raw_facts = semantic.get(
            "facts",
            (),
        )

        if isinstance(
            raw_facts,
            (list, tuple),
        ):
            for fact in raw_facts:
                if not isinstance(
                    fact,
                    dict,
                ):
                    continue

                fact_id = str(
                    fact.get(
                        "fact_id",
                        "",
                    )
                ).strip()

                if not fact_id:
                    continue

                facts.append(
                    {
                        "fact_id": fact_id,
                        "fact_type": str(
                            fact.get(
                                "fact_type",
                                "",
                            )
                        ),
                        "label": str(
                            fact.get(
                                "label",
                                "",
                            )
                        ),
                        "value": fact.get(
                            "value",
                            "",
                        ),
                        "raw_value": str(
                            fact.get(
                                "raw_value",
                                "",
                            )
                        ),
                        "page_number": fact.get(
                            "page_number",
                        ),
                        "region_id": str(
                            fact.get(
                                "region_id",
                                "",
                            )
                        ),
                        "evidence_id": str(
                            fact.get(
                                "evidence_id",
                                "",
                            )
                        ),
                        "confidence": fact.get(
                            "confidence",
                            0.0,
                        ),
                        "link_score": fact.get(
                            "link_score",
                            0.0,
                        ),
                        "link_reasons": list(
                            _unique_non_empty(
                                fact.get(
                                    "link_reasons",
                                    (),
                                )
                            )
                        ),
                    }
                )

    unique_facts: dict[str, dict[str, Any]] = {}

    for fact in facts:
        unique_facts.setdefault(
            fact["fact_id"],
            fact,
        )

    return {
        "semantic_knowledge_available": any(
            bool(
                _semantic_knowledge(
                    concept
                ).get(
                    "semantic_knowledge_available",
                    False,
                )
            )
            for concept in concepts
        ),
        "fact_ids": _unique_non_empty(
            fact_ids
        ),
        "attribute_ids": _unique_non_empty(
            attribute_ids
        ),
        "entity_ids": _unique_non_empty(
            entity_ids
        ),
        "evidence_ids": _unique_non_empty(
            evidence_ids
        ),
        "facts": tuple(
            unique_facts.values()
        ),
    }


def _concept_source_provenance(
    concepts: tuple[NormalizedConceptRecord, ...],
) -> dict[str, dict[str, Any]]:
    """Preserva la correspondencia concepto normalizado -> fuente/ítem."""
    result: dict[str, dict[str, Any]] = {}

    for concept in concepts:
        metadata = concept.metadata if isinstance(concept.metadata, dict) else {}
        fields = metadata.get("fields", {})
        if not isinstance(fields, dict):
            fields = {}

        result[str(concept.normalized_concept_id)] = {
            "concept_id": str(concept.concept_id),
            "document_id": str(concept.traceability.document_id),
            "document_reference": str(concept.traceability.document_reference),
            "source_record_id": str(concept.model_reference.source_record_id),
            "original_value": str(concept.original_value),
            "normalized_value": str(concept.normalized_value),
            "item_id": str(metadata.get("item_id", "") or ""),
            "quantity": metadata.get("quantity", ""),
            "unit": metadata.get("unit", ""),
            "unit_price": metadata.get("unit_price", ""),
            "fields": dict(fields),
        }

    return result


def build_equivalence_record(
    *,
    catalog_view: NormalizedConceptCatalogView,
    concepts: tuple[NormalizedConceptRecord, ...],
    sequence: int,
    relation_type: EquivalenceRelationType,
    evidence_level: EvidenceLevel,
    detector_type: str,
    detector_name: str,
    criteria_used: tuple[str, ...],
    information_used: tuple[str, ...],
    limitations: tuple[str, ...],
    rationale: str,
    metadata: dict[str, Any] | None = None,
) -> EquivalenceRecord:
    semantic = _semantic_provenance(
        concepts
    )

    semantic_metadata = {
        "semantic_knowledge_available": semantic[
            "semantic_knowledge_available"
        ],
        "semantic_fact_ids": semantic[
            "fact_ids"
        ],
        "semantic_attribute_ids": semantic[
            "attribute_ids"
        ],
        "semantic_entity_ids": semantic[
            "entity_ids"
        ],
        "semantic_evidence_ids": semantic[
            "evidence_ids"
        ],
        "semantic_facts": semantic[
            "facts"
        ],
        "semantic_concept_count": len(
            concepts
        ),
        "concept_source_map": _concept_source_provenance(
            concepts
        ),
    }

    enriched_information = tuple(
        dict.fromkeys(
            (
                *information_used,
                (
                    "semantic_knowledge_available="
                    f"{semantic['semantic_knowledge_available']}"
                ),
                (
                    "semantic_fact_count="
                    f"{len(semantic['fact_ids'])}"
                ),
                (
                    "semantic_entity_count="
                    f"{len(semantic['entity_ids'])}"
                ),
                (
                    "semantic_evidence_count="
                    f"{len(semantic['evidence_ids'])}"
                ),
            )
        )
    )

    return EquivalenceRecord(
        equivalence_id=build_equivalence_id(
            catalog_view.model_id,
            sequence,
        ),
        involved_concept_ids=tuple(
            concept.normalized_concept_id
            for concept in concepts
        ),
        relation_type=relation_type.value,
        evidence_level=evidence_level.value,
        status=EquivalenceDetectionStatus.DETECTED.value,
        detector_type=detector_type,
        explainability=EquivalenceExplainability(
            criteria_used=criteria_used,
            information_used=enriched_information,
            limitations=limitations,
            rationale=rationale,
        ),
        traceability=build_equivalence_traceability(
            catalog_view=catalog_view,
            concepts=concepts,
        ),
        metadata={
            "detector_name": detector_name,
            **semantic_metadata,
            **(metadata or {}),
        },
    )


def build_equivalence_catalog(
    *,
    catalog_view: NormalizedConceptCatalogView,
    equivalences: tuple[EquivalenceRecord, ...],
    comparable_group_builder_prepared: bool,
    context_association_prepared: bool,
    comparative_domain_model_prepared: bool,
) -> EquivalenceCatalog:
    document_ids = tuple(
        dict.fromkeys(
            document_id
            for equivalence in equivalences
            for document_id
            in equivalence.traceability.document_ids
            if document_id
        )
    )

    if not document_ids:
        document_ids = (
            catalog_view.document_id,
        )

    return EquivalenceCatalog(
        catalog_id=(
            f"ede-catalog://"
            f"{catalog_view.model_id}"
        ),
        process_id=catalog_view.process_id,
        model_id=catalog_view.model_id,
        document_id=catalog_view.document_id,
        source_normalized_catalog_id=(
            catalog_view.catalog_id
        ),
        equivalences=equivalences,
        document_ids=document_ids,
        comparable_group_builder_prepared=(
            comparable_group_builder_prepared
        ),
        context_association_prepared=(
            context_association_prepared
        ),
        comparative_domain_model_prepared=(
            comparative_domain_model_prepared
        ),
    )
