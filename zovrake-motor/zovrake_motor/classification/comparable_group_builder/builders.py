"""Utilidades de construcción de grupos comparables."""

from __future__ import annotations

from typing import Any

from zovrake_motor.classification.equivalence_detection.enums import EquivalenceRelationType

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


def _concept_source_map_from_relations(
    relations: tuple[EquivalenceRecord, ...],
) -> dict[str, dict[str, Any]]:
    """Consolida la fonte documental de cada concepto del grupo."""
    result: dict[str, dict[str, Any]] = {}

    for relation in relations:
        raw_map = relation.metadata.get("concept_source_map", {})
        if not isinstance(raw_map, dict):
            continue

        for concept_id, source in raw_map.items():
            normalized_id = str(concept_id).strip()
            if not normalized_id or not isinstance(source, dict):
                continue
            existing = result.get(normalized_id)
            if existing is None or (not str(existing.get("document_id", "")).strip() and str(source.get("document_id", "")).strip()):
                result[normalized_id] = dict(source)

    return result


def _semantic_group_provenance(
    relations: tuple[EquivalenceRecord, ...],
) -> dict[str, Any]:
    """
    Consolida la procedencia semántica ya calculada por EDE.

    CGB no vuelve a leer documentos ni recalcula equivalencias. Solo transporta
    IDs, hechos y evidencias que ya existen en EquivalenceRecord.metadata.
    """
    fact_ids: list[str] = []
    attribute_ids: list[str] = []
    entity_ids: list[str] = []
    evidence_ids: list[str] = []
    facts: list[dict[str, Any]] = []

    for relation in relations:
        metadata = relation.metadata

        fact_ids.extend(
            str(value).strip()
            for value in metadata.get(
                "semantic_fact_ids",
                (),
            )
            if str(value).strip()
        )
        attribute_ids.extend(
            str(value).strip()
            for value in metadata.get(
                "semantic_attribute_ids",
                (),
            )
            if str(value).strip()
        )
        entity_ids.extend(
            str(value).strip()
            for value in metadata.get(
                "semantic_entity_ids",
                (),
            )
            if str(value).strip()
        )
        evidence_ids.extend(
            str(value).strip()
            for value in metadata.get(
                "semantic_evidence_ids",
                (),
            )
            if str(value).strip()
        )

        raw_facts = metadata.get(
            "semantic_facts",
            (),
        )

        if isinstance(
            raw_facts,
            (list, tuple),
        ):
            for fact in raw_facts:
                if isinstance(
                    fact,
                    dict,
                ):
                    facts.append(
                        dict(fact)
                    )

    unique_fact_map: dict[str, dict[str, Any]] = {}

    for fact in facts:
        fact_id = str(
            fact.get(
                "fact_id",
                "",
            )
        ).strip()

        if fact_id:
            unique_fact_map.setdefault(
                fact_id,
                fact,
            )

    return {
        "semantic_knowledge_available": any(
            bool(
                relation.metadata.get(
                    "semantic_knowledge_available",
                    False,
                )
            )
            for relation in relations
        ),
        "fact_ids": tuple(
            dict.fromkeys(
                fact_ids
            )
        ),
        "attribute_ids": tuple(
            dict.fromkeys(
                attribute_ids
            )
        ),
        "entity_ids": tuple(
            dict.fromkeys(
                entity_ids
            )
        ),
        "evidence_ids": tuple(
            dict.fromkeys(
                evidence_ids
            )
        ),
        "facts": tuple(
            unique_fact_map.values()
        ),
    }


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


def _relation_pair(relation: EquivalenceRecord) -> tuple[str, str] | None:
    """Retorna una clave de par estable para una relación binaria."""
    if len(relation.involved_concept_ids) < 2:
        return None
    left = str(relation.involved_concept_ids[0]).strip()
    right = str(relation.involved_concept_ids[1]).strip()
    if not left or not right or left == right:
        return None
    return tuple(sorted((left, right)))


def _source_provider_identity(
    source: dict[str, Any],
    concept_id: str,
    *,
    allow_document_fallback: bool,
) -> str:
    """
    Resuelve una identidad de proveedor conservadora.

    El nombre de proveedor es preferido y se normaliza únicamente en
    espacios/capitalización. Si no existe, el document_id actúa como
    aislamiento documental. Nunca se inventa un proveedor distinto.
    """
    provider_name = " ".join(
        str(source.get("provider_name", "") or "").strip().casefold().split()
    )
    if provider_name:
        return f"provider:{provider_name}"

    if allow_document_fallback:
        document_id = " ".join(
            str(source.get("document_id", "") or "").strip().casefold().split()
        )
        if document_id:
            return f"document:{document_id}"

    return f"unknown:{concept_id}"


def _concept_provider_map(
    relations: tuple[EquivalenceRecord, ...],
    *,
    allow_document_fallback: bool,
) -> dict[str, str]:
    """Construye concepto -> proveedor desde la procedencia real del EDE."""
    providers: dict[str, str] = {}

    for relation in relations:
        raw_map = relation.metadata.get("concept_source_map", {})
        if not isinstance(raw_map, dict):
            continue

        for concept_id, source in raw_map.items():
            concept_key = str(concept_id).strip()
            if not concept_key or not isinstance(source, dict):
                continue

            identity = _source_provider_identity(
                source,
                concept_key,
                allow_document_fallback=allow_document_fallback,
            )
            existing = providers.get(concept_key)

            if existing is None:
                providers[concept_key] = identity
            elif existing != identity:
                # La misma entidad conceptual no puede tener dos proveedores
                # simultáneamente. Ante contradicción, se pierde la capacidad
                # de atribuirla a un proveedor y se aísla el concepto.
                providers[concept_key] = f"ambiguous:{concept_key}"

    return providers


def _relation_priority(relation: EquivalenceRecord) -> tuple[int, int, float, str]:
    """Ordena primero evidencia fuerte y después similitud semántica."""
    relation_rank = {
        EquivalenceRelationType.EQUIVALENT.value: 2,
        EquivalenceRelationType.COMPARABLE.value: 1,
    }
    evidence_rank = {
        "high": 3,
        "medium": 2,
        "low": 1,
    }
    score = float(
        relation.metadata.get(
            "semantic_similarity_score",
            0.0,
        )
        or 0.0
    )
    return (
        relation_rank.get(str(relation.relation_type), 0),
        evidence_rank.get(str(relation.evidence_level).casefold(), 0),
        score,
        str(relation.equivalence_id),
    )


def build_clusters_from_equivalences(
    catalog_view: EquivalenceCatalogView,
) -> dict[str, tuple[str, ...]]:
    """
    Construye grupos con dos salvaguardas explícitas:

    1. un grupo no puede contener más de un concepto del mismo proveedor;
    2. una unión nueva solo es válida cuando existe relación positiva directa
       entre todos los pares que formarán el nuevo grupo.

    La segunda regla evita que una relación transitiva débil cree falsos
    grupos (A~B y B~C no basta para fusionar A/B/C cuando A~C no existe).
    """
    relations = tuple(catalog_view.comparable_relations)
    nodes: set[str] = set()

    for relation in relations:
        nodes.update(
            str(concept_id).strip()
            for concept_id in relation.involved_concept_ids
            if str(concept_id).strip()
        )

    if not nodes:
        return {}

    relation_by_pair: dict[tuple[str, str], EquivalenceRecord] = {}

    for relation in relations:
        pair = _relation_pair(relation)
        if pair is None:
            continue
        existing = relation_by_pair.get(pair)
        if existing is None or _relation_priority(relation) > _relation_priority(existing):
            relation_by_pair[pair] = relation

    provider_by_concept = _concept_provider_map(
        relations,
        allow_document_fallback=len(catalog_view.document_ids) > 1,
    )
    union_find = _UnionFind(tuple(sorted(nodes)))
    cluster_members: dict[str, set[str]] = {
        concept_id: {concept_id}
        for concept_id in sorted(nodes)
    }
    cluster_providers: dict[str, set[str]] = {
        concept_id: {
            provider_by_concept.get(
                concept_id,
                f"unknown:{concept_id}",
            )
        }
        for concept_id in sorted(nodes)
    }

    def can_merge(left_root: str, right_root: str) -> bool:
        left_members = cluster_members[left_root]
        right_members = cluster_members[right_root]

        if cluster_providers[left_root] & cluster_providers[right_root]:
            return False

        for left in left_members:
            for right in right_members:
                if tuple(sorted((left, right))) not in relation_by_pair:
                    return False

        return True

    ordered_relations = sorted(
        relation_by_pair.values(),
        key=lambda relation: (
            -_relation_priority(relation)[0],
            -_relation_priority(relation)[1],
            -_relation_priority(relation)[2],
            _relation_priority(relation)[3],
        ),
    )

    for relation in ordered_relations:
        pair = _relation_pair(relation)
        if pair is None:
            continue

        left_root = union_find.find(pair[0])
        right_root = union_find.find(pair[1])

        if left_root == right_root:
            continue

        if can_merge(left_root, right_root):
            union_find.union(left_root, right_root)
            cluster_members[left_root].update(cluster_members[right_root])
            cluster_providers[left_root].update(cluster_providers[right_root])
            cluster_members.pop(right_root, None)
            cluster_providers.pop(right_root, None)

    return {
        root: tuple(sorted(members))
        for root, members in cluster_members.items()
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

    concept_source_map = _concept_source_map_from_relations(
        relations
    )

    for relation in relations:
        equivalence_ids.add(relation.equivalence_id)
        concept_ids.update(relation.traceability.concept_ids)
        document_ids.update(relation.traceability.document_ids)
        if not relation.traceability.document_ids and relation.traceability.document_id:
            document_ids.add(relation.traceability.document_id)

    for concept_id in normalized_concept_ids:
        source = concept_source_map.get(str(concept_id), {})
        if not isinstance(source, dict):
            continue
        provider_name = " ".join(
            str(source.get("provider_name", "") or "").strip().split()
        )
        if provider_name:
            provider_references.add(provider_name)
            continue

        document_id = str(source.get("document_id", "") or "").strip()
        if document_id:
            provider_references.add(document_id)

    sorted_document_ids = tuple(sorted(document_ids))
    primary_document_id = sorted_document_ids[0] if sorted_document_ids else catalog_view.document_id
    concept_type = _concept_type_from_relations(relations, normalized_concept_ids[0])
    first_relation = relations[0]

    semantic_provenance = _semantic_group_provenance(
        relations
    )

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
            "semantic_knowledge_available": semantic_provenance[
                "semantic_knowledge_available"
            ],
            "semantic_fact_ids": semantic_provenance[
                "fact_ids"
            ],
            "semantic_attribute_ids": semantic_provenance[
                "attribute_ids"
            ],
            "semantic_entity_ids": semantic_provenance[
                "entity_ids"
            ],
            "semantic_evidence_ids": semantic_provenance[
                "evidence_ids"
            ],
            "semantic_facts": semantic_provenance[
                "facts"
            ],
            "relation_types": sorted(
                {
                    str(relation.relation_type)
                    for relation in relations
                }
            ),
            "semantic_similarity_scores": [
                float(relation.metadata.get("semantic_similarity_score", 0.0))
                for relation in relations
                if "semantic_similarity_score" in relation.metadata
            ],
            "comparable_candidate": any(
                relation.relation_type
                == EquivalenceRelationType.COMPARABLE.value
                or relation.metadata.get(
                    "semantic_comparable_candidate",
                    False,
                )
                for relation in relations
            ),
            "concept_source_map": concept_source_map,
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
