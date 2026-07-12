"""Utilidades de construcción del Modelo Comparativo Definitivo."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comparative_tables.comparative_model_builder.gateway import (
    ColumnSetView,
    EnrichedTableView,
    ModelBuildInputView,
    ProviderSetView,
    RowSetView,
    StructureView,
)
from zovrake_motor.comparative_tables.comparative_model_builder.governance import (
    PM6_DEFINITIVE_OUTPUT_CONTRACT_VERSION,
    PM7_INPUT_CONTRACT_PREPARED,
)
from zovrake_motor.comparative_tables.comparative_model_builder.models import (
    DefinitiveCommercialInformation,
    DefinitiveComparativeModel,
    DefinitiveComparativeModelCatalog,
    DefinitiveTechnicalInformation,
)
from zovrake_motor.config.categories.comparative_tables import ComparativeModelBuilderSettings


def build_public_definitive_model_id(sequence: int, *, prefix: str, padding: int) -> str:
    return f"{prefix}-{sequence:0{padding}d}"


def _extract_group_commercial(structure: StructureView | None) -> dict[str, Any]:
    if structure is None:
        return {}
    attrs = dict(structure.metadata_prepared.get("available_attributes", {}))
    return dict(attrs.get("commercial", {}))


def _extract_group_technical(structure: StructureView | None) -> tuple[dict[str, Any], tuple[str, ...]]:
    if structure is None:
        return {}, ()
    attrs = dict(structure.metadata_prepared.get("available_attributes", {}))
    fields = dict(attrs.get("technical", {}))
    specs_raw = attrs.get("specifications", [])
    specs = tuple(str(item) for item in specs_raw) if isinstance(specs_raw, list) else ()
    return fields, specs


def _extract_provider_commercial_fields(providers: tuple[dict[str, Any], ...]) -> tuple[dict[str, Any], ...]:
    result: list[dict[str, Any]] = []
    for provider in providers:
        commercial = provider.get("commercial_information", {})
        if isinstance(commercial, dict):
            result.append(dict(commercial.get("fields", {})))
    return tuple(result)


def _extract_provider_technical_fields(
    providers: tuple[dict[str, Any], ...],
) -> tuple[dict[str, Any], ...]:
    result: list[dict[str, Any]] = []
    for provider in providers:
        technical = provider.get("technical_information", {})
        if isinstance(technical, dict):
            result.append(dict(technical.get("fields", {})))
    return tuple(result)


def build_definitive_model(
    *,
    enriched_table: EnrichedTableView,
    structure: StructureView | None,
    column_set: ColumnSetView | None,
    row_set: RowSetView | None,
    provider_set: ProviderSetView | None,
    input_view: ModelBuildInputView,
    definitive_model_id: str,
    integrity_valid: bool,
    builder_name: str,
    settings: ComparativeModelBuilderSettings,
) -> DefinitiveComparativeModel:
    providers = provider_set.providers if provider_set is not None else ()
    columns = column_set.columns if column_set is not None else ()
    rows = row_set.rows if row_set is not None else ()

    group_commercial = _extract_group_commercial(structure)
    group_technical_fields, group_specs = _extract_group_technical(structure)

    commercial = DefinitiveCommercialInformation(
        fields=group_commercial,
        provider_fields=_extract_provider_commercial_fields(providers),
    )
    technical = DefinitiveTechnicalInformation(
        fields=group_technical_fields,
        specifications=group_specs,
        provider_fields=_extract_provider_technical_fields(providers),
    )

    integrity_status = "valid" if integrity_valid else "invalid"
    metadata = {
        "definitive_model_id": definitive_model_id,
        "enrichment_id": enriched_table.enrichment_id,
        "contract_version": PM6_DEFINITIVE_OUTPUT_CONTRACT_VERSION,
        "builder_name": builder_name,
        "pm7_input_contract_prepared": PM7_INPUT_CONTRACT_PREPARED,
        "inherited_metadata": dict(enriched_table.metadata),
    }

    motor_refs = {
        "enriched_catalog_id": input_view.enriched_catalog.catalog_id,
        "structure_catalog_id": input_view.structure_catalog.catalog_id,
        "column_catalog_id": input_view.column_catalog.catalog_id,
        "row_catalog_id": input_view.row_catalog.catalog_id,
        "provider_catalog_id": input_view.provider_catalog.catalog_id,
        "integrity_report_id": input_view.integrity_report.report_id,
        "enrichment_id": enriched_table.enrichment_id,
    }

    return DefinitiveComparativeModel(
        definitive_model_id=definitive_model_id,
        comparative_table_id=enriched_table.table_id,
        group_id=enriched_table.group_id,
        group_type=enriched_table.group_type,
        dynamic_columns=columns,
        dynamic_rows=rows,
        provider_organization=providers,
        commercial_information=commercial,
        technical_information=technical,
        inherited_context=dict(enriched_table.inherited_context),
        confidence_level_available=enriched_table.confidence_level_available,
        metadata=metadata,
        traceability=dict(enriched_table.traceability),
        motor_internal_references=motor_refs,
        integrity_status=integrity_status,
        source_data_preserved=True,
        domain_model_preserved=input_view.structure_catalog.domain_model_preserved,
    )


def build_definitive_catalog(
    *,
    input_view: ModelBuildInputView,
    models: tuple[DefinitiveComparativeModel, ...],
    settings: ComparativeModelBuilderSettings,
) -> DefinitiveComparativeModelCatalog:
    return DefinitiveComparativeModelCatalog(
        catalog_id=f"cmb-catalog://{input_view.enriched_catalog.model_id}",
        process_id=input_view.enriched_catalog.process_id,
        model_id=input_view.enriched_catalog.model_id,
        document_id=input_view.enriched_catalog.document_id,
        source_enriched_catalog_id=input_view.enriched_catalog.catalog_id,
        source_structure_catalog_id=input_view.structure_catalog.catalog_id,
        source_column_catalog_id=input_view.column_catalog.catalog_id,
        source_row_catalog_id=input_view.row_catalog.catalog_id,
        source_provider_catalog_id=input_view.provider_catalog.catalog_id,
        source_integrity_report_id=input_view.integrity_report.report_id,
        models=models,
        pm6_definitive_output_contract=True,
        pm7_input_contract_prepared=PM7_INPUT_CONTRACT_PREPARED,
        comparative_validation_framework_prepared=(
            settings.comparative_validation_framework_prepared
        ),
        enriched_catalog_preserved=True,
        structure_catalog_preserved=True,
        column_catalog_preserved=True,
        row_catalog_preserved=True,
        provider_catalog_preserved=True,
        integrity_report_preserved=True,
        domain_model_preserved=input_view.structure_catalog.domain_model_preserved,
        source_data_preserved=True,
    )
