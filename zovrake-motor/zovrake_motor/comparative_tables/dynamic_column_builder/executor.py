"""Ejecutor de constructores del Dynamic Column Builder."""

from __future__ import annotations

from zovrake_motor.comparative_tables.dynamic_column_builder.builders import build_column_catalog
from zovrake_motor.comparative_tables.dynamic_column_builder.enums import ComparativeColumnBuildStatus
from zovrake_motor.comparative_tables.dynamic_column_builder.gateway import StructureCatalogView
from zovrake_motor.comparative_tables.dynamic_column_builder.models import (
    ComparativeColumnBuildIncident,
    ComparativeColumnBuildResult,
    ComparativeTableColumnSet,
)
from zovrake_motor.comparative_tables.dynamic_column_builder.registry import ColumnBuilderRegistry
from zovrake_motor.config.categories.comparative_tables import DynamicColumnBuilderSettings


class DynamicColumnBuildExecutor:
    """Coordina la ejecución secuencial de constructores sin modificar el catálogo de estructuras."""

    def __init__(self, registry: ColumnBuilderRegistry) -> None:
        self._registry = registry

    def execute(
        self,
        catalog_view: StructureCatalogView,
        *,
        settings: DynamicColumnBuilderSettings,
    ) -> ComparativeColumnBuildResult:
        column_sets: list[ComparativeTableColumnSet] = []
        incidents: list[ComparativeColumnBuildIncident] = []
        observations: list[str] = []
        sequence = 1

        for builder in self._registry.all_builders():
            result = builder.build(
                catalog_view,
                settings=settings,
                start_sequence=sequence,
            )
            column_sets.extend(result.column_sets)
            incidents.extend(result.incidents)
            observations.extend(result.technical_observations)
            sequence += sum(len(column_set.columns) for column_set in result.column_sets)

        total_columns = sum(len(column_set.columns) for column_set in column_sets)
        if total_columns > settings.max_columns_per_process:
            incidents.append(
                ComparativeColumnBuildIncident(
                    builder_name="dynamic_column_build_executor",
                    message=(
                        f"Se construyeron {total_columns} columnas; "
                        f"límite configurado: {settings.max_columns_per_process}"
                    ),
                    severity="warning",
                ),
            )
            trimmed_sets: list[ComparativeTableColumnSet] = []
            remaining = settings.max_columns_per_process
            for column_set in column_sets:
                if remaining <= 0:
                    break
                columns = column_set.columns[:remaining]
                remaining -= len(columns)
                trimmed_sets.append(
                    ComparativeTableColumnSet(
                        table_id=column_set.table_id,
                        group_id=column_set.group_id,
                        columns=columns,
                        source_structure_catalog_id=column_set.source_structure_catalog_id,
                    ),
                )
            column_sets = trimmed_sets

        catalog = build_column_catalog(
            catalog_view=catalog_view,
            column_sets=tuple(column_sets),
            dynamic_row_builder_prepared=settings.dynamic_row_builder_prepared,
        )

        status = (
            ComparativeColumnBuildStatus.BUILT
            if column_sets
            else ComparativeColumnBuildStatus.SKIPPED
        )
        observations.extend(
            (
                "structure_catalog_preserved=True",
                "domain_model_preserved=True",
                "source_files_unaccessed=True",
                "columns_built=" + str(total_columns),
            ),
        )

        return ComparativeColumnBuildResult(
            process_id=catalog_view.process_id,
            document_id=catalog_view.document_id,
            model_id=catalog_view.model_id,
            catalog=catalog,
            status=status,
            incidents=tuple(incidents),
            structure_catalog_preserved=True,
            domain_model_preserved=catalog_view.domain_model_preserved,
            builders_executed=self._registry.count(),
            technical_observations=tuple(observations),
        )
