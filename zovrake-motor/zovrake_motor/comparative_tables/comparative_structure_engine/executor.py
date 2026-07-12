"""Ejecutor de constructores del Comparative Structure Engine."""

from __future__ import annotations

from zovrake_motor.comparative_tables.comparative_structure_engine.builders import build_structure_catalog
from zovrake_motor.comparative_tables.comparative_structure_engine.enums import (
    ComparativeTableStructureStatus,
)
from zovrake_motor.comparative_tables.comparative_structure_engine.gateway import DomainModelCatalogView
from zovrake_motor.comparative_tables.comparative_structure_engine.models import (
    ComparativeStructureBuildIncident,
    ComparativeStructureBuildResult,
    ComparativeTableBaseStructure,
)
from zovrake_motor.comparative_tables.comparative_structure_engine.registry import StructureBuilderRegistry
from zovrake_motor.config.categories.comparative_tables import ComparativeStructureEngineSettings


class ComparativeStructureBuildExecutor:
    """Coordina la ejecución secuencial de constructores sin modificar el modelo de dominio."""

    def __init__(self, registry: StructureBuilderRegistry) -> None:
        self._registry = registry

    def execute(
        self,
        catalog_view: DomainModelCatalogView,
        *,
        settings: ComparativeStructureEngineSettings,
    ) -> ComparativeStructureBuildResult:
        structures: list[ComparativeTableBaseStructure] = []
        incidents: list[ComparativeStructureBuildIncident] = []
        observations: list[str] = []
        sequence = 1

        for builder in self._registry.all_builders():
            result = builder.build(
                catalog_view,
                settings=settings,
                start_sequence=sequence,
            )
            structures.extend(result.structures)
            incidents.extend(result.incidents)
            observations.extend(result.technical_observations)
            sequence += len(result.structures)

        if len(structures) > settings.max_structures_per_process:
            incidents.append(
                ComparativeStructureBuildIncident(
                    builder_name="comparative_structure_build_executor",
                    message=(
                        f"Se construyeron {len(structures)} estructuras; "
                        f"límite configurado: {settings.max_structures_per_process}"
                    ),
                    severity="warning",
                ),
            )
            structures = structures[: settings.max_structures_per_process]

        catalog = build_structure_catalog(
            catalog_view=catalog_view,
            structures=tuple(structures),
            dynamic_column_builder_prepared=settings.dynamic_column_builder_prepared,
            dynamic_row_builder_prepared=settings.dynamic_row_builder_prepared,
        )

        status = (
            ComparativeTableStructureStatus.STRUCTURED
            if structures
            else ComparativeTableStructureStatus.SKIPPED
        )
        observations.extend(
            (
                "domain_model_preserved=True",
                "source_files_unaccessed=True",
                "structures_built=" + str(len(structures)),
            ),
        )

        return ComparativeStructureBuildResult(
            process_id=catalog_view.process_id,
            document_id=catalog_view.document_id,
            model_id=catalog_view.model_id,
            catalog=catalog,
            status=status,
            incidents=tuple(incidents),
            domain_model_preserved=True,
            builders_executed=self._registry.count(),
            technical_observations=tuple(observations),
        )
