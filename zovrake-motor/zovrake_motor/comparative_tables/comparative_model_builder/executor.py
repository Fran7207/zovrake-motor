"""Ejecutor de constructores del Comparative Model Builder."""

from __future__ import annotations

from zovrake_motor.comparative_tables.comparative_model_builder.builders import (
    build_definitive_catalog,
)
from zovrake_motor.comparative_tables.comparative_model_builder.enums import (
    ComparativeModelBuildStatus,
)
from zovrake_motor.comparative_tables.comparative_model_builder.gateway import ModelBuildInputView
from zovrake_motor.comparative_tables.comparative_model_builder.models import (
    ComparativeModelBuildResult,
    DefinitiveComparativeModel,
)
from zovrake_motor.comparative_tables.comparative_model_builder.registry import ModelBuilderRegistry
from zovrake_motor.config.categories.comparative_tables import ComparativeModelBuilderSettings


class ComparativeModelBuildExecutor:
    """Coordina constructores sin modificar catálogos de entrada."""

    def __init__(self, registry: ModelBuilderRegistry) -> None:
        self._registry = registry

    def execute(
        self,
        input_view: ModelBuildInputView,
        *,
        settings: ComparativeModelBuilderSettings,
    ) -> ComparativeModelBuildResult:
        models: list[DefinitiveComparativeModel] = []
        observations: list[str] = []
        sequence = 1

        for builder in self._registry.all_builders():
            result = builder.build(
                input_view,
                settings=settings,
                start_sequence=sequence,
            )
            models.extend(result.models)
            observations.extend(result.technical_observations)
            sequence += len(result.models)

        if models:
            status = ComparativeModelBuildStatus.BUILT
        elif self._registry.count():
            status = ComparativeModelBuildStatus.PARTIAL
        else:
            status = ComparativeModelBuildStatus.SKIPPED

        catalog = build_definitive_catalog(
            input_view=input_view,
            models=tuple(models),
            settings=settings,
        )

        observations.extend(
            (
                "enriched_catalog_preserved=True",
                "structure_catalog_preserved=True",
                "column_catalog_preserved=True",
                "row_catalog_preserved=True",
                "provider_catalog_preserved=True",
                "integrity_report_preserved=True",
                "domain_model_preserved=True",
                "source_files_unaccessed=True",
                "pm6_definitive_output_contract=True",
                "models_built_count=" + str(len(models)),
            ),
        )

        return ComparativeModelBuildResult(
            process_id=input_view.enriched_catalog.process_id,
            document_id=input_view.enriched_catalog.document_id,
            model_id=input_view.enriched_catalog.model_id,
            catalog=catalog,
            status=status,
            models_built_count=len(models),
            enriched_catalog_preserved=True,
            structure_catalog_preserved=True,
            column_catalog_preserved=True,
            row_catalog_preserved=True,
            provider_catalog_preserved=True,
            integrity_report_preserved=True,
            domain_model_preserved=input_view.structure_catalog.domain_model_preserved,
            builders_executed=self._registry.count(),
            technical_observations=tuple(observations),
        )
