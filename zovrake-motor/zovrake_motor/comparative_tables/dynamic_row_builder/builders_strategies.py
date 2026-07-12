"""Constructores especializados del Dynamic Row Builder."""

from __future__ import annotations

from zovrake_motor.comparative_tables.dynamic_row_builder.builders import (
    build_row_set_for_column_set,
    resolve_structure_for_column_set,
)
from zovrake_motor.comparative_tables.dynamic_row_builder.enums import RowBuilderStrategyType
from zovrake_motor.comparative_tables.dynamic_row_builder.gateway import RowBuildInputView
from zovrake_motor.comparative_tables.dynamic_row_builder.models import (
    ComparativeRowBuildIncident,
    RowBuilderResult,
)
from zovrake_motor.comparative_tables.dynamic_row_builder.port import DynamicRowBuilderPort
from zovrake_motor.config.categories.comparative_tables import DynamicRowBuilderSettings


class ProviderRowBuilder(DynamicRowBuilderPort):
    """
    Construye filas dinámicas — una fila por cada proveedor del Grupo Comparable.

    Cada grupo genera exclusivamente sus propias filas.
    """

    @property
    def builder_name(self) -> str:
        return "provider_row_builder"

    @property
    def builder_label(self) -> str:
        return "Constructor de Filas — Proveedores del Grupo"

    @property
    def builder_type(self) -> RowBuilderStrategyType:
        return RowBuilderStrategyType.PROVIDER_ROW

    def build(
        self,
        input_view: RowBuildInputView,
        *,
        settings: DynamicRowBuilderSettings,
        start_sequence: int,
    ) -> RowBuilderResult:
        row_sets = []
        incidents: list[ComparativeRowBuildIncident] = []
        sequence = start_sequence

        structures_by_table = {
            structure.table_id: structure
            for structure in input_view.structure_catalog.structures
        }

        for column_set in input_view.column_catalog.column_sets:
            structure_view = resolve_structure_for_column_set(
                column_set=column_set,
                structures_by_table=structures_by_table,
            )
            if structure_view is None:
                incidents.append(
                    ComparativeRowBuildIncident(
                        builder_name=self.builder_name,
                        message=(
                            f"No se encontró estructura para table_id={column_set.table_id} "
                            f"group_id={column_set.group_id}"
                        ),
                        severity="warning",
                    ),
                )
                continue

            row_set, sequence = build_row_set_for_column_set(
                input_view=input_view,
                column_set=column_set,
                structure_view=structure_view,
                settings=settings,
                start_sequence=sequence,
            )
            row_sets.append(row_set)

        total_rows = sum(len(row_set.rows) for row_set in row_sets)
        return RowBuilderResult(
            builder_type=self.builder_type.value,
            builder_name=self.builder_name,
            row_sets=tuple(row_sets),
            incidents=tuple(incidents),
            technical_observations=(
                f"builder_type={self.builder_type.value}",
                f"row_sets_built={len(row_sets)}",
                f"rows_built={total_rows}",
                f"column_sets_consumed={len(input_view.column_catalog.column_sets)}",
            ),
        )
