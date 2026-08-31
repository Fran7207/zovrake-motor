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


def _extract_semantic_knowledge(
    structure: StructureView | None,
) -> dict[str, Any]:
    """
    Conserva el conocimiento semántico que CSE ya preparó para el grupo.

    CMB no vuelve a interpretar el documento: únicamente transporta la
    procedencia semántica al Modelo Comparativo Definitivo.
    """
    if structure is None:
        return {}

    metadata_prepared = dict(
        structure.metadata_prepared
    )

    raw = metadata_prepared.get(
        "semantic_knowledge",
        {},
    )

    if not isinstance(
        raw,
        dict,
    ):
        return {}

    return {
        "semantic_knowledge_available": bool(
            raw.get(
                "semantic_knowledge_available",
                False,
            )
        ),
        "semantic_fact_ids": list(
            raw.get(
                "semantic_fact_ids",
                (),
            )
            or ()
        ),
        "semantic_attribute_ids": list(
            raw.get(
                "semantic_attribute_ids",
                (),
            )
            or ()
        ),
        "semantic_entity_ids": list(
            raw.get(
                "semantic_entity_ids",
                (),
            )
            or ()
        ),
        "semantic_evidence_ids": list(
            raw.get(
                "semantic_evidence_ids",
                (),
            )
            or ()
        ),
        "semantic_facts": list(
            raw.get(
                "semantic_facts",
                (),
            )
            or ()
        ),
    }


def _extract_provider_semantic_knowledge(
    rows: tuple[dict[str, Any], ...],
) -> tuple[dict[str, Any], ...]:
    """
    Conserva el snapshot semántico específico de cada fila/proveedor.

    DRB ya asoció esta información de forma conservadora; CMB no la
    recalcula.
    """
    result: list[dict[str, Any]] = []

    for row in rows:
        if not isinstance(
            row,
            dict,
        ):
            continue

        metadata = row.get(
            "metadata",
            {},
        )

        if not isinstance(
            metadata,
            dict,
        ):
            continue

        if not (
            metadata.get(
                "semantic_knowledge_available",
                False,
            )
            or metadata.get(
                "semantic_knowledge_matched",
                False,
            )
        ):
            continue

        result.append(
            {
                "provider_id": str(
                    row.get(
                        "provider_id",
                        "",
                    )
                ),
                "semantic_knowledge_available": bool(
                    metadata.get(
                        "semantic_knowledge_available",
                        False,
                    )
                ),
                "semantic_knowledge_matched": bool(
                    metadata.get(
                        "semantic_knowledge_matched",
                        False,
                    )
                ),
                "semantic_entity_ids": list(
                    metadata.get(
                        "semantic_entity_ids",
                        (),
                    )
                    or ()
                ),
                "semantic_fact_ids": list(
                    metadata.get(
                        "semantic_fact_ids",
                        (),
                    )
                    or ()
                ),
                "semantic_evidence_ids": list(
                    metadata.get(
                        "semantic_evidence_ids",
                        (),
                    )
                    or ()
                ),
                "semantic_facts": list(
                    metadata.get(
                        "semantic_facts",
                        (),
                    )
                    or ()
                ),
            }
        )

    return tuple(result)


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


def _resolve_document_ids(
    *,
    enriched_table: EnrichedTableView,
    provider_set: ProviderSetView | None,
) -> tuple[str, ...]:
    """Recupera todos los documentos origen sin colapsarlos en uno solo."""
    document_ids: list[str] = []

    def add_many(values: Any) -> None:
        if isinstance(values, (list, tuple, set)):
            for value in values:
                text = str(value).strip()
                if text and text not in document_ids:
                    document_ids.append(text)
        elif values:
            text = str(values).strip()
            if text and text not in document_ids:
                document_ids.append(text)

    traceability = dict(enriched_table.traceability)
    add_many(traceability.get("document_ids", []))

    lineage = traceability.get("lineage", {})
    if isinstance(lineage, dict):
        add_many(lineage.get("document_ids", []))
        comparable_group = lineage.get("comparable_group", {})
        if isinstance(comparable_group, dict):
            add_many(comparable_group.get("document_ids", []))

    if provider_set is not None:
        for provider in provider_set.providers:
            provider_traceability = provider.get("traceability", {})
            if isinstance(provider_traceability, dict):
                add_many(provider_traceability.get("document_ids", []))
                if provider_traceability.get("document_id"):
                    add_many(provider_traceability.get("document_id"))

    if not document_ids and traceability.get("document_id"):
        add_many(traceability.get("document_id"))

    return tuple(document_ids)


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
    document_ids = _resolve_document_ids(
        enriched_table=enriched_table,
        provider_set=provider_set,
    )

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

    semantic_knowledge = _extract_semantic_knowledge(
        structure
    )
    provider_semantic_knowledge = (
        _extract_provider_semantic_knowledge(
            rows
        )
    )

    metadata = {
        "definitive_model_id": definitive_model_id,
        "enrichment_id": enriched_table.enrichment_id,
        "contract_version": PM6_DEFINITIVE_OUTPUT_CONTRACT_VERSION,
        "builder_name": builder_name,
        "pm7_input_contract_prepared": PM7_INPUT_CONTRACT_PREPARED,
        "inherited_metadata": dict(enriched_table.metadata),
        "semantic_knowledge": semantic_knowledge,
        "semantic_knowledge_available": bool(
            semantic_knowledge.get(
                "semantic_knowledge_available",
                False,
            )
        ),
        "semantic_fact_ids": list(
            semantic_knowledge.get(
                "semantic_fact_ids",
                (),
            )
            or ()
        ),
        "semantic_attribute_ids": list(
            semantic_knowledge.get(
                "semantic_attribute_ids",
                (),
            )
            or ()
        ),
        "semantic_entity_ids": list(
            semantic_knowledge.get(
                "semantic_entity_ids",
                (),
            )
            or ()
        ),
        "semantic_evidence_ids": list(
            semantic_knowledge.get(
                "semantic_evidence_ids",
                (),
            )
            or ()
        ),
        "semantic_facts": list(
            semantic_knowledge.get(
                "semantic_facts",
                (),
            )
            or ()
        ),
        "provider_semantic_knowledge": list(
            provider_semantic_knowledge
        ),
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
        document_ids=document_ids,
    )


def build_definitive_catalog(
    *,
    input_view: ModelBuildInputView,
    models: tuple[DefinitiveComparativeModel, ...],
    settings: ComparativeModelBuilderSettings,
) -> DefinitiveComparativeModelCatalog:
    document_ids = tuple(
        dict.fromkeys(
            document_id
            for model in models
            for document_id in model.document_ids
            if document_id
        )
    )
    if not document_ids and input_view.enriched_catalog.document_id:
        document_ids = (input_view.enriched_catalog.document_id,)

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
        document_ids=document_ids,
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