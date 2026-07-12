"""Constructores especializados del Comparative Model Builder."""

from __future__ import annotations

from zovrake_motor.comparative_tables.comparative_model_builder.builders import (
    build_definitive_model,
    build_public_definitive_model_id,
)
from zovrake_motor.comparative_tables.comparative_model_builder.enums import (
    ModelBuilderStrategyType,
)
from zovrake_motor.comparative_tables.comparative_model_builder.gateway import ModelBuildInputView
from zovrake_motor.comparative_tables.comparative_model_builder.models import (
    DefinitiveComparativeModel,
    ModelBuilderResult,
)
from zovrake_motor.comparative_tables.comparative_model_builder.port import ModelBuilderPort
from zovrake_motor.config.categories.comparative_tables import ComparativeModelBuilderSettings


class GroupComparativeModelBuilder(ModelBuilderPort):
    """
    Construye un Modelo Comparativo Definitivo por cada Grupo Comparable.

    Consolida estructura, columnas, filas, proveedores, contexto,
    confianza, metadatos y trazabilidad sin modificar orígenes.
    """

    @property
    def builder_name(self) -> str:
        return "group_comparative_model_builder"

    @property
    def builder_label(self) -> str:
        return "Constructor de Modelo Comparativo — Grupo Comparable"

    @property
    def builder_type(self) -> ModelBuilderStrategyType:
        return ModelBuilderStrategyType.COMPARATIVE_TABLE

    def build(
        self,
        input_view: ModelBuildInputView,
        *,
        settings: ComparativeModelBuilderSettings,
        start_sequence: int,
    ) -> ModelBuilderResult:
        structures_by_table = {
            structure.table_id: structure
            for structure in input_view.structure_catalog.structures
        }
        columns_by_table = {
            column_set.table_id: column_set
            for column_set in input_view.column_catalog.column_sets
        }
        rows_by_table = {
            row_set.table_id: row_set for row_set in input_view.row_catalog.row_sets
        }
        providers_by_table = {
            provider_set.table_id: provider_set
            for provider_set in input_view.provider_catalog.provider_sets
        }
        integrity_by_table = {
            check_set.table_id: check_set.is_valid
            for check_set in input_view.integrity_report.check_sets
        }

        models: list[DefinitiveComparativeModel] = []
        sequence = start_sequence

        for enriched_table in input_view.enriched_catalog.enriched_tables:
            definitive_model_id = build_public_definitive_model_id(
                sequence,
                prefix=settings.definitive_model_id_prefix,
                padding=settings.definitive_model_id_padding,
            )
            sequence += 1

            models.append(
                build_definitive_model(
                    enriched_table=enriched_table,
                    structure=structures_by_table.get(enriched_table.table_id),
                    column_set=columns_by_table.get(enriched_table.table_id),
                    row_set=rows_by_table.get(enriched_table.table_id),
                    provider_set=providers_by_table.get(enriched_table.table_id),
                    input_view=input_view,
                    definitive_model_id=definitive_model_id,
                    integrity_valid=integrity_by_table.get(enriched_table.table_id, True),
                    builder_name=self.builder_name,
                    settings=settings,
                ),
            )

        return ModelBuilderResult(
            builder_type=self.builder_type.value,
            builder_name=self.builder_name,
            models=tuple(models),
            technical_observations=(
                f"builder_type={self.builder_type.value}",
                f"models_built={len(models)}",
                f"enriched_tables_processed={len(input_view.enriched_catalog.enriched_tables)}",
            ),
        )
