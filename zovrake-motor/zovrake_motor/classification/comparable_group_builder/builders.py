"""Utilidades de construcción de grupos comparables."""

from __future__ import annotations

from typing import Any

from zovrake_motor.classification.comparable_group_builder.enums import (
    ComparableGroupBuildStatus,
    ComparableGroupType,
)
from zovrake_motor.classification.comparable_group_builder.gateway import EquivalenceCatalogView
from zovrake_motor.classification.comparable_group_builder.models import (
    ComparableGroupCatalog,
    ComparableGroupCommercialInformation,
    ComparableGroupModelReference,
    ComparableGroupRecord,
    ComparableGroupTechnicalInformation,
    ComparableGroupTraceability,
)
from zovrake_motor.classification.equivalence_detection.models import EquivalenceRecord
from zovrake_motor.config.categories.classification import ComparableGroupBuilderSettings

MATERIAL_CONCEPT_TYPES = frozenset({"material", "partida"})
SERVICE_CONCEPT_TYPES = frozenset({"service", "technical_element", "commercial_element", "observation"})


class _UnionFind:
    def __init__(self, nodes: tuple[str, ...]) -> None:
        self._parent = {node: node for node in nodes}

    def find(self, node: str) -> str:
        parent = self._parent[node]
        if parent != node:
            self._parent[node] = self.find(parent)
        return self._parent[node]

    def union(self, left: str, right: str) -> None:
        root_left = self.find(left)
        root_right = self.find(right)
        if root_left != root_right:
            self._parent[root_right] = root_left

    def clusters(self) -> dict[str, list[str]]:
        grouped: dict[str, list[str]] = {}
        for node in self._parent:
            root = self.find(node)
            grouped.setdefault(root, []).append(node)
        return grouped


def build_public_group_id(sequence: int, *, prefix: str, padding: int) -> str:
    return f"{prefix}-{sequence:0{padding}d}"


def build_internal_group_id(model_id: str, sequence: int) -> str:
    return f"cgb://{model_id}/group-{sequence:04d}"


def resolve_group_type(concept_type: str) -> str:
    if concept_type in MATERIAL_CONCEPT_TYPES:
        return ComparableGroupType.MATERIAL.value
    if concept_type in SERVICE_CONCEPT_TYPES:
        return ComparableGroupType.SERVICE.value
    if concept_type == "specification":
        return ComparableGroupType.MATERIAL.value
    return ComparableGroupType.MATERIAL.value


def _concept_type_from_relations(
    relations: tuple[EquivalenceRecord, ...],
    concept_id: str,
) -> str:
    for relation in relations:
        if concept_id in relation.involved_concept_ids:
            concept_type = relation.metadata.get("shared_concept_type")
            if concept_type:
                return str(concept_type)
            for info in relation.explainability.information_used:
                if info.startswith("concept_type="):
                    return info.split("=", 1)[1]
                if info.startswith("left_concept_type=") and concept_id == relation.involved_concept_ids[0]:
                    return info.split("=", 1)[1]
                if info.startswith("right_concept_type=") and concept_id == relation.involved_concept_ids[-1]:
                    return info.split("=", 1)[1]
    return "material"


def build_clusters_from_equivalences(
    catalog_view: EquivalenceCatalogView,
) -> dict[str, tuple[str, ...]]:
    nodes: set[str] = set()
    for relation in catalog_view.equivalent_relations:
        nodes.update(relation.involved_concept_ids)

    if not nodes:
        return {}

    union_find = _UnionFind(tuple(nodes))
    for relation in catalog_view.equivalent_relations:
        if len(relation.involved_concept_ids) >= 2:
            left, right = relation.involved_concept_ids[0], relation.involved_concept_ids[1]
            union_find.union(left, right)

    return {
        root: tuple(sorted(members))
        for root, members in union_find.clusters().items()
        if len(members) >= 1
    }


def build_comparable_group_record(
    *,
    catalog_view: EquivalenceCatalogView,
    normalized_concept_ids: tuple[str, ...],
    relations: tuple[EquivalenceRecord, ...],
    public_group_id: str,
    internal_sequence: int,
    settings: ComparableGroupBuilderSettings,
) -> ComparableGroupRecord:
    concept_ids: set[str] = set()
    equivalence_ids: set[str] = set()
    provider_references: set[str] = set()
    document_ids: set[str] = set()
    specifications: set[str] = set()

    for relation in relations:
        equivalence_ids.add(relation.equivalence_id)
        concept_ids.update(relation.traceability.concept_ids)
        document_ids.update(relation.traceability.document_ids)
        if not relation.traceability.document_ids and relation.traceability.document_id:
            document_ids.add(relation.traceability.document_id)
        if relation.traceability.document_reference:
            provider_references.add(relation.traceability.document_reference)

    sorted_document_ids = tuple(sorted(document_ids))
    primary_document_id = sorted_document_ids[0] if sorted_document_ids else catalog_view.document_id
    concept_type = _concept_type_from_relations(relations, normalized_concept_ids[0])
    first_relation = relations[0]

    return ComparableGroupRecord(
        group_id=public_group_id,
        internal_group_id=build_internal_group_id(catalog_view.model_id, internal_sequence),
        group_type=resolve_group_type(concept_type),
        normalized_concept_ids=normalized_concept_ids,
        concept_ids=tuple(sorted(concept_ids)),
        equivalence_ids=tuple(sorted(equivalence_ids)),
        provider_references=tuple(sorted(provider_references)),
        commercial_information=ComparableGroupCommercialInformation(
            fields={
                "group_type": resolve_group_type(concept_type),
                "members_count": len(normalized_concept_ids),
            },
        ),
        technical_information=ComparableGroupTechnicalInformation(
            specifications=tuple(sorted(specifications)),
            fields={"concept_type": concept_type},
        ),
        model_reference=ComparableGroupModelReference(
            model_id=catalog_view.model_id,
            document_id=primary_document_id,
            concept_ids=tuple(sorted(concept_ids)),
            normalized_concept_ids=normalized_concept_ids,
            document_ids=sorted_document_ids,
        ),
        traceability=ComparableGroupTraceability(
            process_id=catalog_view.process_id,
            document_id=primary_document_id,
            model_id=catalog_view.model_id,
            source_equivalence_catalog_id=catalog_view.catalog_id,
            source_normalized_catalog_id=catalog_view.source_normalized_catalog_id,
            equivalence_ids=tuple(sorted(equivalence_ids)),
            concept_ids=tuple(sorted(concept_ids)),
            normalized_concept_ids=normalized_concept_ids,
            document_reference=first_relation.traceability.document_reference,
            canonical_reference=first_relation.traceability.canonical_reference,
            original_preserved=first_relation.traceability.original_preserved,
            document_ids=sorted_document_ids,
        ),
        status=ComparableGroupBuildStatus.BUILT,
        metadata={
            "group_id_prefix": settings.group_id_prefix,
            "group_id_immutable": settings.group_id_immutable,
            "members_count": len(normalized_concept_ids),
            "document_count": len(sorted_document_ids),
            "cross_document_group": len(sorted_document_ids) > 1,
        },
    )


def build_comparable_group_catalog(
    *,
    catalog_view: EquivalenceCatalogView,
    groups: tuple[ComparableGroupRecord, ...],
    context_association_prepared: bool,
    comparative_domain_model_prepared: bool,
) -> ComparableGroupCatalog:
    return ComparableGroupCatalog(
        catalog_id=f"cgb-catalog://{catalog_view.model_id}",
        process_id=catalog_view.process_id,
        model_id=catalog_view.model_id,
        document_id=(
            catalog_view.document_id
            if not getattr(catalog_view, "document_ids", ())
            else sorted(catalog_view.document_ids)[0]
        ),
        source_equivalence_catalog_id=catalog_view.catalog_id,
        document_ids=tuple(getattr(catalog_view, "document_ids", ())) or (catalog_view.document_id,),
        groups=groups,
        context_association_prepared=context_association_prepared,
        comparative_domain_model_prepared=comparative_domain_model_prepared,
    )
