"""Pruebas ZO-046: agrupación multi-proveedor segura y trazable."""

from __future__ import annotations

from uuid import uuid4

from zovrake_motor.classification.comparable_group_builder.builders import (
    build_clusters_from_equivalences,
    build_comparable_group_record,
)
from zovrake_motor.classification.comparable_group_builder.gateway import (
    EquivalenceCatalogGateway,
)
from zovrake_motor.config.categories.classification import (
    ComparableGroupBuilderSettings,
)


def _relation(
    *,
    process_id: str,
    equivalence_id: str,
    left: str,
    right: str,
    left_provider: str,
    right_provider: str,
    relation_type: str = "equivalent",
    score: float = 0.95,
) -> dict:
    return {
        "equivalence_id": equivalence_id,
        "involved_concept_ids": [left, right],
        "relation_type": relation_type,
        "evidence_level": "high" if relation_type == "equivalent" else "medium",
        "status": "confirmed",
        "detector_type": "semantic_similarity",
        "explainability": {
            "criteria_used": ["provider_aware_test"],
            "information_used": [],
            "limitations": [],
            "rationale": "test",
        },
        "traceability": {
            "process_id": process_id,
            "document_id": f"DOC-{left_provider}",
            "document_ids": [f"DOC-{left_provider}", f"DOC-{right_provider}"],
            "model_id": "collective-model",
            "source_normalized_catalog_id": "cne://collective",
            "concept_ids": [left, right],
            "document_reference": f"document://DOC-{left_provider}",
            "canonical_reference": "canonical://collective",
            "original_preserved": True,
        },
        "metadata": {
            "semantic_comparable_candidate": True,
            "semantic_similarity_score": score,
            "concept_source_map": {
                left: {
                    "concept_id": f"CID-{left}",
                    "document_id": f"DOC-{left_provider}",
                    "provider_name": left_provider,
                    "document_reference": f"document://DOC-{left_provider}",
                    "source_record_id": left,
                    "original_value": "PRODUCTO X",
                    "normalized_value": "producto x",
                    "item_id": left,
                    "quantity": "1",
                    "unit": "UND",
                    "unit_price": "10",
                    "fields": {},
                },
                right: {
                    "concept_id": f"CID-{right}",
                    "document_id": f"DOC-{right_provider}",
                    "provider_name": right_provider,
                    "document_reference": f"document://DOC-{right_provider}",
                    "source_record_id": right,
                    "original_value": "PRODUCTO X",
                    "normalized_value": "producto x",
                    "item_id": right,
                    "quantity": "1",
                    "unit": "UND",
                    "unit_price": "10",
                    "fields": {},
                },
            },
        },
    }


def _catalog(relations: list[dict], process_id: str) -> dict:
    document_ids = sorted(
        {
            document_id
            for relation in relations
            for document_id in relation["traceability"]["document_ids"]
        }
    )
    return {
        "catalog_id": "eq://collective",
        "process_id": process_id,
        "model_id": "collective-model",
        "document_id": document_ids[0],
        "document_ids": document_ids,
        "source_normalized_catalog_id": "cne://collective",
        "equivalences": relations,
        "comparable_group_builder_prepared": True,
    }


def test_same_provider_cannot_occupy_two_slots_of_one_group() -> None:
    process_id = str(uuid4())

    relations = [
        _relation(
            process_id=process_id,
            equivalence_id="EQ-001",
            left="A1",
            right="B1",
            left_provider="PROVIDER-A",
            right_provider="PROVIDER-B",
        ),
        _relation(
            process_id=process_id,
            equivalence_id="EQ-002",
            left="A2",
            right="B1",
            left_provider="PROVIDER-A",
            right_provider="PROVIDER-B",
        ),
    ]

    view = EquivalenceCatalogGateway().validate(
        _catalog(relations, process_id)
    )
    clusters = build_clusters_from_equivalences(view)

    assert any(set(members) == {"A1", "B1"} for members in clusters.values())
    assert not any(set(members) == {"A1", "A2", "B1"} for members in clusters.values())

    for members in clusters.values():
        providers = []
        for concept_id in members:
            relation_map = relations[0]["metadata"]["concept_source_map"]
            provider = relation_map.get(concept_id, {}).get("provider_name", "")
            if not provider and concept_id == "A2":
                provider = relations[1]["metadata"]["concept_source_map"][concept_id]["provider_name"]
            if provider:
                providers.append(provider.casefold())
        assert len(providers) == len(set(providers))


def test_transitive_semantic_bridge_does_not_merge_without_direct_pair() -> None:
    process_id = str(uuid4())

    relations = [
        _relation(
            process_id=process_id,
            equivalence_id="EQ-001",
            left="A",
            right="B",
            left_provider="PROVIDER-A",
            right_provider="PROVIDER-B",
            relation_type="comparable",
            score=0.70,
        ),
        _relation(
            process_id=process_id,
            equivalence_id="EQ-002",
            left="B",
            right="C",
            left_provider="PROVIDER-B",
            right_provider="PROVIDER-C",
            relation_type="comparable",
            score=0.69,
        ),
    ]

    view = EquivalenceCatalogGateway().validate(
        _catalog(relations, process_id)
    )
    clusters = build_clusters_from_equivalences(view)

    assert any(set(members) == {"A", "B"} for members in clusters.values())
    assert any(set(members) == {"C"} for members in clusters.values())
    assert not any(set(members) == {"A", "B", "C"} for members in clusters.values())


def test_provider_name_is_preserved_in_group_and_relation_outside_cluster_is_not_attached() -> None:
    process_id = str(uuid4())

    relations = [
        _relation(
            process_id=process_id,
            equivalence_id="EQ-001",
            left="A1",
            right="B1",
            left_provider="PROVIDER-A",
            right_provider="PROVIDER-B",
        ),
        _relation(
            process_id=process_id,
            equivalence_id="EQ-002",
            left="A2",
            right="B1",
            left_provider="PROVIDER-A",
            right_provider="PROVIDER-B",
        ),
    ]

    view = EquivalenceCatalogGateway().validate(
        _catalog(relations, process_id)
    )
    clusters = build_clusters_from_equivalences(view)
    members = next(
        members
        for members in clusters.values()
        if set(members) == {"A1", "B1"}
    )

    related = tuple(
        relation
        for relation in view.comparable_relations
        if set(relation.involved_concept_ids).issubset(set(members))
    )
    assert [r.equivalence_id for r in related] == ["EQ-001"]

    group = build_comparable_group_record(
        catalog_view=view,
        normalized_concept_ids=tuple(sorted(members)),
        relations=related,
        public_group_id="GC-000001",
        internal_sequence=1,
        settings=ComparableGroupBuilderSettings.default(),
    )

    assert group.provider_references == ("PROVIDER-A", "PROVIDER-B")
    assert "A2" not in group.metadata["concept_source_map"]


def test_collective_normalized_catalog_injects_provider_identity_into_concepts() -> None:
    from zovrake_motor.motor_runtime.cotizaciones_executor import CotizacionesAnalysisExecutor

    process_id = uuid4()
    catalogs = (
        {
            "catalog_id": "cne://A",
            "process_id": str(process_id),
            "model_id": "model-A",
            "document_id": "DOC-A",
            "source_document": {"provider_name": "PROVIDER-A"},
            "concepts": [
                {
                    "concept_id": "CON-A",
                    "normalized_concept_id": "N-A",
                    "metadata": {"item_id": "ITEM-A"},
                }
            ],
        },
        {
            "catalog_id": "cne://B",
            "process_id": str(process_id),
            "model_id": "model-B",
            "document_id": "DOC-B",
            "provider_name": "PROVIDER-B",
            "concepts": [
                {
                    "concept_id": "CON-B",
                    "normalized_concept_id": "N-B",
                    "metadata": {"item_id": "ITEM-B"},
                }
            ],
        },
    )

    collective = CotizacionesAnalysisExecutor._build_collective_normalized_catalog(
        process_id=process_id,
        normalized_catalogs=catalogs,
    )

    by_id = {
        concept["concept_id"]: concept
        for concept in collective["concepts"]
    }

    assert by_id["CON-A"]["metadata"]["provider_name"] == "PROVIDER-A"
    assert by_id["CON-B"]["metadata"]["provider_name"] == "PROVIDER-B"
