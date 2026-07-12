"""Constructores especializados del Comparative Domain Model Builder."""

from __future__ import annotations

from zovrake_motor.classification.comparative_domain_model.builders import (
    _group_by_id,
    build_comparative_domain_model_record,
    build_public_model_id,
)
from zovrake_motor.classification.comparative_domain_model.enums import DomainModelBuilderStrategyType
from zovrake_motor.classification.comparative_domain_model.gateway import ContextAssociationCatalogView
from zovrake_motor.classification.comparative_domain_model.models import DomainModelBuilderResult
from zovrake_motor.classification.comparative_domain_model.port import ComparativeDomainModelBuilderPort
from zovrake_motor.config.categories.classification import ComparativeDomainModelBuilderSettings


class GroupContextAggregationBuilder(ComparativeDomainModelBuilderPort):
    """
    Construye el Modelo Comparativo agregando grupo, contexto y trazabilidad.

    Consume exclusivamente el catálogo de asociaciones del CAE-Context.
    """

    @property
    def builder_name(self) -> str:
        return "group_context_aggregation_builder"

    @property
    def builder_label(self) -> str:
        return "Constructor de Modelo — Agregación Grupo-Contexto"

    @property
    def builder_type(self) -> DomainModelBuilderStrategyType:
        return DomainModelBuilderStrategyType.GROUP_CONTEXT_AGGREGATION

    def build(
        self,
        catalog_view: ContextAssociationCatalogView,
        *,
        settings: ComparativeDomainModelBuilderSettings,
        start_sequence: int,
    ) -> DomainModelBuilderResult:
        groups_by_id = _group_by_id(catalog_view.preserved_groups)
        models = []
        sequence = start_sequence
        preserved_context = catalog_view.preserved_context

        for association in sorted(catalog_view.associations, key=lambda item: item.group_id):
            group = groups_by_id.get(association.group_id)
            if group is None:
                continue

            public_model_id = build_public_model_id(
                sequence,
                prefix=settings.model_id_prefix,
                padding=settings.model_id_padding,
            )
            models.append(
                build_comparative_domain_model_record(
                    catalog_view=catalog_view,
                    association=association,
                    group=group,
                    preserved_context=preserved_context,
                    public_model_id=public_model_id,
                    internal_sequence=sequence,
                    settings=settings,
                ),
            )
            sequence += 1

        return DomainModelBuilderResult(
            builder_type=self.builder_type.value,
            builder_name=self.builder_name,
            models=tuple(models),
            technical_observations=(
                f"builder_type={self.builder_type.value}",
                f"models_built={len(models)}",
                f"associations_used={len(catalog_view.associations)}",
                "source_data_preserved=True",
            ),
        )
