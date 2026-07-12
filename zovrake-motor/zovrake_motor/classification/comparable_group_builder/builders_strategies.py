"""Constructores especializados del Comparable Group Builder."""

from __future__ import annotations

from zovrake_motor.classification.comparable_group_builder.builders import (
    build_clusters_from_equivalences,
    build_comparable_group_record,
    build_public_group_id,
)
from zovrake_motor.classification.comparable_group_builder.enums import GroupBuilderStrategyType
from zovrake_motor.classification.comparable_group_builder.gateway import EquivalenceCatalogView
from zovrake_motor.classification.comparable_group_builder.models import GroupBuilderResult
from zovrake_motor.classification.comparable_group_builder.port import ComparableGroupBuilderPort
from zovrake_motor.classification.equivalence_detection.models import EquivalenceRecord
from zovrake_motor.config.categories.classification import ComparableGroupBuilderSettings


class EquivalenceClusterGroupBuilder(ComparableGroupBuilderPort):
    """
    Construye grupos comparables agrupando conceptos equivalentes.

    Utiliza únicamente relaciones de tipo equivalent del Modelo de Equivalencias.
    """

    @property
    def builder_name(self) -> str:
        return "equivalence_cluster_group_builder"

    @property
    def builder_label(self) -> str:
        return "Constructor de Grupos — Clústeres de Equivalencia"

    @property
    def builder_type(self) -> GroupBuilderStrategyType:
        return GroupBuilderStrategyType.EQUIVALENCE_CLUSTER

    def build(
        self,
        catalog_view: EquivalenceCatalogView,
        *,
        settings: ComparableGroupBuilderSettings,
        start_sequence: int,
    ) -> GroupBuilderResult:
        clusters = build_clusters_from_equivalences(catalog_view)
        groups = []
        sequence = start_sequence

        relations_by_concept: dict[str, list[EquivalenceRecord]] = {}
        for relation in catalog_view.equivalent_relations:
            for concept_id in relation.involved_concept_ids:
                relations_by_concept.setdefault(concept_id, []).append(relation)

        for members in sorted(clusters.values(), key=lambda item: item[0]):
            if len(members) < settings.min_members_per_group:
                continue

            related: dict[str, EquivalenceRecord] = {}
            for member in members:
                for relation in relations_by_concept.get(member, []):
                    related[relation.equivalence_id] = relation

            public_group_id = build_public_group_id(
                sequence,
                prefix=settings.group_id_prefix,
                padding=settings.group_id_padding,
            )
            groups.append(
                build_comparable_group_record(
                    catalog_view=catalog_view,
                    normalized_concept_ids=members,
                    relations=tuple(related.values()),
                    public_group_id=public_group_id,
                    internal_sequence=sequence,
                    settings=settings,
                ),
            )
            sequence += 1

        return GroupBuilderResult(
            builder_type=self.builder_type.value,
            builder_name=self.builder_name,
            groups=tuple(groups),
            technical_observations=(
                f"builder_type={self.builder_type.value}",
                f"groups_built={len(groups)}",
                f"equivalent_relations_used={len(catalog_view.equivalent_relations)}",
            ),
        )
