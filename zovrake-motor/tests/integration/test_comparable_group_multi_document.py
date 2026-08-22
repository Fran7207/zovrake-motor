"""Prueba de grupos comparables multi-documento."""

from __future__ import annotations

from uuid import uuid4

from zovrake_motor.classification.comparable_group_builder.builders import (
    build_clusters_from_equivalences,
    build_comparable_group_catalog,
    build_comparable_group_record,
)
from zovrake_motor.classification.comparable_group_builder.gateway import (
    EquivalenceCatalogGateway,
)
from zovrake_motor.config.categories.classification import (
    ComparableGroupBuilderSettings,
)


def _catalog():
    process_id = uuid4()

    return process_id, {
        "catalog_id": "eq://collective-001",
        "process_id": str(process_id),
        "model_id": "collective-model",
        "document_id": "DOC-A",
        "document_ids": ["DOC-A", "DOC-B"],
        "source_normalized_catalog_id": "cne://collective-001",
        "equivalences": [
            {
                "equivalence_id": "EQ-001",
                "involved_concept_ids": ["CONCEPT-A", "CONCEPT-B"],
                "relation_type": "equivalent",
                "evidence_level": "high",
                "status": "confirmed",
                "detector_type": "exact_normalized_match",
                "explainability": {
                    "criteria_used": ["normalized_value"],
                    "information_used": [
                        "concept_type=material",
                    ],
                    "limitations": [],
                    "rationale": "Mismo concepto normalizado.",
                },
                "traceability": {
                    "process_id": str(process_id),
                    "document_id": "DOC-A",
                    "document_ids": ["DOC-A", "DOC-B"],
                    "model_id": "collective-model",
                    "source_normalized_catalog_id": (
                        "cne://collective-001"
                    ),
                    "concept_ids": [
                        "CONCEPT-A",
                        "CONCEPT-B",
                    ],
                    "document_reference": "document://DOC-A",
                    "canonical_reference": "canonical://collective",
                    "original_preserved": True,
                },
                "metadata": {
                    "shared_concept_type": "material",
                },
            }
        ],
        "comparable_group_builder_prepared": True,
    }


def test_comparable_group_preserves_all_document_ids() -> None:
    process_id, raw_catalog = _catalog()

    view = EquivalenceCatalogGateway().validate(raw_catalog)

    assert view.document_ids == ("DOC-A", "DOC-B")

    clusters = build_clusters_from_equivalences(view)

    assert clusters
    assert any(
        set(members) == {"CONCEPT-A", "CONCEPT-B"}
        for members in clusters.values()
    )

    group = build_comparable_group_record(
        catalog_view=view,
        normalized_concept_ids=(
            "CONCEPT-A",
            "CONCEPT-B",
        ),
        relations=view.equivalent_relations,
        public_group_id="GC-000001",
        internal_sequence=1,
        settings=ComparableGroupBuilderSettings.default(),
    )

    assert group.model_reference.document_ids == (
        "DOC-A",
        "DOC-B",
    )

    assert group.traceability.document_ids == (
        "DOC-A",
        "DOC-B",
    )

    assert group.metadata["cross_document_group"] is True
    assert group.metadata["document_count"] == 2

    catalog = build_comparable_group_catalog(
        catalog_view=view,
        groups=(group,),
        context_association_prepared=True,
        comparative_domain_model_prepared=True,
    )

    assert catalog.document_ids == (
        "DOC-A",
        "DOC-B",
    )

    serialized = catalog.to_dict()

    assert serialized["document_ids"] == [
        "DOC-A",
        "DOC-B",
    ]

    assert serialized["groups"][0]["model_reference"]["document_ids"] == [
        "DOC-A",
        "DOC-B",
    ]

    assert serialized["groups"][0]["traceability"]["document_ids"] == [
        "DOC-A",
        "DOC-B",
    ]