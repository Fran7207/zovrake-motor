"""Ejecutor de constructores del Dynamic Row Builder."""

from __future__ import annotations

from zovrake_motor.comparative_tables.dynamic_row_builder.builders import build_row_catalog
from zovrake_motor.comparative_tables.dynamic_row_builder.enums import ComparativeRowBuildStatus
from zovrake_motor.comparative_tables.dynamic_row_builder.gateway import RowBuildInputView
from zovrake_motor.comparative_tables.dynamic_row_builder.models import (
    ComparativeRowBuildIncident,
    ComparativeRowBuildResult,
    ComparativeTableRowSet,
)
from zovrake_motor.comparative_tables.dynamic_row_builder.registry import RowBuilderRegistry
from zovrake_motor.config.categories.comparative_tables import DynamicRowBuilderSettings


class DynamicRowBuildExecutor:
    """Coordina la ejecución secuencial de constructores sin modificar catálogos de entrada."""

    def __init__(self, registry: RowBuilderRegistry) -> None:
        self._registry = registry

    def execute(
        self,
        input_view: RowBuildInputView,
        *,
        settings: DynamicRowBuilderSettings,
    ) -> ComparativeRowBuildResult:
        row_sets: list[ComparativeTableRowSet] = []
        incidents: list[ComparativeRowBuildIncident] = []
        observations: list[str] = []
        sequence = 1

        for builder in self._registry.all_builders():
            result = builder.build(
                input_view,
                settings=settings,
                start_sequence=sequence,
            )
            row_sets.extend(result.row_sets)
            incidents.extend(result.incidents)
            observations.extend(result.technical_observations)
            sequence += sum(len(row_set.rows) for row_set in result.row_sets)

        total_rows = sum(len(row_set.rows) for row_set in row_sets)
        if total_rows > settings.max_rows_per_process:
            incidents.append(
                ComparativeRowBuildIncident(
                    builder_name="dynamic_row_build_executor",
                    message=(
                        f"Se construyeron {total_rows} filas; "
                        f"límite configurado: {settings.max_rows_per_process}"
                    ),
                    severity="warning",
                ),
            )
            trimmed_sets: list[ComparativeTableRowSet] = []
            remaining = settings.max_rows_per_process
            for row_set in row_sets:
                if remaining <= 0:
                    break
                rows = row_set.rows[:remaining]
                remaining -= len(rows)
                trimmed_sets.append(
                    ComparativeTableRowSet(
                        table_id=row_set.table_id,
                        group_id=row_set.group_id,
                        rows=rows,
                        source_column_catalog_id=row_set.source_column_catalog_id,
                        source_structure_catalog_id=row_set.source_structure_catalog_id,
                    ),
                )
            row_sets = trimmed_sets

        catalog = build_row_catalog(
            input_view=input_view,
            row_sets=tuple(row_sets),
            provider_organization_engine_prepared=settings.provider_organization_engine_prepared,
        )

        status = (
            ComparativeRowBuildStatus.BUILT
            if row_sets
            else ComparativeRowBuildStatus.SKIPPED
        )
        observations.extend(
            (
                "column_catalog_preserved=True",
                "structure_catalog_preserved=True",
                "domain_model_preserved=True",
                "source_files_unaccessed=True",
                "rows_built=" + str(total_rows),
            ),
        )

        return ComparativeRowBuildResult(
            process_id=input_view.column_catalog.process_id,
            document_id=input_view.column_catalog.document_id,
            model_id=input_view.column_catalog.model_id,
            catalog=catalog,
            status=status,
            incidents=tuple(incidents),
            column_catalog_preserved=True,
            structure_catalog_preserved=True,
            domain_model_preserved=input_view.column_catalog.domain_model_preserved,
            builders_executed=self._registry.count(),
            technical_observations=tuple(observations),
        )
