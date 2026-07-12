"""Constructores especializados del Dynamic Column Builder."""

from __future__ import annotations

from zovrake_motor.comparative_tables.dynamic_column_builder.builders import (
    build_column_set_for_structure,
)
from zovrake_motor.comparative_tables.dynamic_column_builder.enums import ColumnBuilderStrategyType
from zovrake_motor.comparative_tables.dynamic_column_builder.gateway import StructureCatalogView
from zovrake_motor.comparative_tables.dynamic_column_builder.models import ColumnBuilderResult
from zovrake_motor.comparative_tables.dynamic_column_builder.port import DynamicColumnBuilderPort
from zovrake_motor.config.categories.comparative_tables import DynamicColumnBuilderSettings


class StructureAttributeColumnBuilder(DynamicColumnBuilderPort):
    """
    Construye columnas dinámicas a partir de los atributos disponibles en cada estructura.

    Cada Grupo Comparable genera exclusivamente sus propias columnas.
    """

    @property
    def builder_name(self) -> str:
        return "structure_attribute_column_builder"

    @property
    def builder_label(self) -> str:
        return "Constructor de Columnas — Atributos de Estructura"

    @property
    def builder_type(self) -> ColumnBuilderStrategyType:
        return ColumnBuilderStrategyType.STRUCTURE_ATTRIBUTE

    def build(
        self,
        catalog_view: StructureCatalogView,
        *,
        settings: DynamicColumnBuilderSettings,
        start_sequence: int,
    ) -> ColumnBuilderResult:
        column_sets = []
        sequence = start_sequence

        for structure_view in catalog_view.structures:
            column_set, sequence = build_column_set_for_structure(
                catalog_view=catalog_view,
                structure_view=structure_view,
                settings=settings,
                start_sequence=sequence,
            )
            column_sets.append(column_set)

        total_columns = sum(len(column_set.columns) for column_set in column_sets)
        return ColumnBuilderResult(
            builder_type=self.builder_type.value,
            builder_name=self.builder_name,
            column_sets=tuple(column_sets),
            technical_observations=(
                f"builder_type={self.builder_type.value}",
                f"column_sets_built={len(column_sets)}",
                f"columns_built={total_columns}",
                f"structures_consumed={len(catalog_view.structures)}",
            ),
        )
