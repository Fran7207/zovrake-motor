"""Constructores especializados del Comparative Structure Engine."""

from __future__ import annotations

from zovrake_motor.comparative_tables.comparative_structure_engine.builders import (
    build_comparative_table_base_structure,
    build_public_table_id,
)
from zovrake_motor.comparative_tables.comparative_structure_engine.enums import (
    StructureBuilderStrategyType,
)
from zovrake_motor.comparative_tables.comparative_structure_engine.gateway import (
    DomainModelCatalogView,
)
from zovrake_motor.comparative_tables.comparative_structure_engine.models import StructureBuilderResult
from zovrake_motor.comparative_tables.comparative_structure_engine.port import (
    ComparativeStructureBuilderPort,
)
from zovrake_motor.config.categories.comparative_tables import ComparativeStructureEngineSettings


class DomainModelGroupStructureBuilder(ComparativeStructureBuilderPort):
    """
    Construye una estructura base independiente por cada Grupo Comparable.

    La cantidad de estructuras depende únicamente del Modelo Comparativo de Dominio.
    """

    @property
    def builder_name(self) -> str:
        return "domain_model_group_structure_builder"

    @property
    def builder_label(self) -> str:
        return "Constructor de Estructuras — Grupos del Modelo de Dominio"

    @property
    def builder_type(self) -> StructureBuilderStrategyType:
        return StructureBuilderStrategyType.DOMAIN_MODEL_GROUP

    def build(
        self,
        catalog_view: DomainModelCatalogView,
        *,
        settings: ComparativeStructureEngineSettings,
        start_sequence: int,
    ) -> StructureBuilderResult:
        structures = []
        sequence = start_sequence

        for group_view in catalog_view.groups:
            public_table_id = build_public_table_id(
                sequence,
                prefix=settings.structure_id_prefix,
                padding=settings.structure_id_padding,
            )
            structures.append(
                build_comparative_table_base_structure(
                    catalog_view=catalog_view,
                    group_view=group_view,
                    public_table_id=public_table_id,
                    internal_sequence=sequence,
                    settings=settings,
                ),
            )
            sequence += 1

        return StructureBuilderResult(
            builder_type=self.builder_type.value,
            builder_name=self.builder_name,
            structures=tuple(structures),
            technical_observations=(
                f"builder_type={self.builder_type.value}",
                f"structures_built={len(structures)}",
                f"domain_groups_consumed={len(catalog_view.groups)}",
            ),
        )
