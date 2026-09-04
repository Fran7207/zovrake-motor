"""Utilidades de construcción de estructuras base de cuadros comparativos."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comparative_tables.comparative_structure_engine.enums import (
    ComparativeTableStructureStatus,
)
from zovrake_motor.comparative_tables.comparative_structure_engine.gateway import (
    DomainModelCatalogView,
    DomainModelGroupView,
)
from zovrake_motor.comparative_tables.comparative_structure_engine.models import (
    ComparativeTableBaseStructure,
    ComparativeTableDomainReference,
    ComparativeTableStructureCatalog,
    ComparativeTableStructureTraceability,
)
from zovrake_motor.config.categories.comparative_tables import ComparativeStructureEngineSettings


def build_public_table_id(sequence: int, *, prefix: str, padding: int) -> str:
    return f"{prefix}-{sequence:0{padding}d}"


def build_internal_table_id(model_id: str, sequence: int) -> str:
    return f"cse://{model_id}/table-{sequence:04d}"


def build_structure_traceability(
    *,
    catalog_view: DomainModelCatalogView,
    group_view: DomainModelGroupView,
) -> ComparativeTableStructureTraceability:
    return ComparativeTableStructureTraceability(
        process_id=catalog_view.process_id,
        document_id=catalog_view.document_id,
        model_id=catalog_view.model_id,
        source_domain_catalog_id=catalog_view.catalog_id,
        source_comparative_model_id=group_view.comparative_model_id,
        group_id=group_view.group_id,
        lineage=dict(group_view.traceability),
        source_data_preserved=catalog_view.source_data_preserved,
        domain_model_preserved=True,
    )


def build_comparative_table_base_structure(
    *,
    catalog_view: DomainModelCatalogView,
    group_view: DomainModelGroupView,
    public_table_id: str,
    internal_sequence: int,
    settings: ComparativeStructureEngineSettings,
) -> ComparativeTableBaseStructure:
    domain_reference = ComparativeTableDomainReference(
        catalog_id=catalog_view.catalog_id,
        process_id=catalog_view.process_id,
        model_id=catalog_view.model_id,
        document_id=catalog_view.document_id,
        comparative_model_id=group_view.comparative_model_id,
        pm6_output_contract=catalog_view.pm6_output_contract,
        source_data_preserved=catalog_view.source_data_preserved,
    )

    # El conocimiento semántico ya preservado por PM5/CDMB cruza el límite
    # PM5 -> PM6 como snapshot de solo lectura. CSE no vuelve a interpretar
    # el contenido; únicamente lo conserva para las capas posteriores.
    group_metadata = dict(group_view.metadata)
    semantic_knowledge = group_metadata.get(
        "semantic_knowledge",
        {},
    )
    if not isinstance(semantic_knowledge, dict):
        semantic_knowledge = {}

    concept_source_map = group_metadata.get(
        "concept_source_map",
        {},
    )
    if not isinstance(concept_source_map, dict):
        concept_source_map = {}

    semantic_fact_ids = semantic_knowledge.get(
        "semantic_fact_ids",
        (),
    ) or ()
    semantic_attribute_ids = semantic_knowledge.get(
        "semantic_attribute_ids",
        (),
    ) or ()
    semantic_entity_ids = semantic_knowledge.get(
        "semantic_entity_ids",
        (),
    ) or ()
    semantic_evidence_ids = semantic_knowledge.get(
        "semantic_evidence_ids",
        (),
    ) or ()
    semantic_facts = semantic_knowledge.get(
        "semantic_facts",
        (),
    ) or ()

    return ComparativeTableBaseStructure(
        table_id=public_table_id,
        internal_table_id=build_internal_table_id(catalog_view.model_id, internal_sequence),
        group_id=group_view.group_id,
        group_type=group_view.group_type,
        table_status=ComparativeTableStructureStatus.STRUCTURED,
        domain_reference=domain_reference,
        columns_prepared=(),
        rows_prepared=(),
        providers_prepared=(),
        validation_prepared={},
        traceability=build_structure_traceability(
            catalog_view=catalog_view,
            group_view=group_view,
        ),
        metadata_prepared={
            "available_attributes": {
                "commercial": dict(group_view.commercial_fields),
                "technical": dict(group_view.technical_fields),
                "specifications": list(group_view.technical_specifications),
                "primary_item": group_view.primary_item,
            },
            "available_providers": list(group_view.providers),
            "inherited_context": dict(group_view.related_context),
            "confidence_level_available": group_view.confidence_level_available,
            "attribute_snapshot_version": "1.0",
            "provider_snapshot_version": "1.0",
            "organization_snapshot_version": "1.0",
            "semantic_knowledge": dict(semantic_knowledge),
            "semantic_knowledge_available": bool(
                semantic_knowledge.get(
                    "semantic_knowledge_available",
                    False,
                )
            ),
            "semantic_fact_ids": [str(value) for value in semantic_fact_ids],
            "semantic_attribute_ids": [str(value) for value in semantic_attribute_ids],
            "semantic_entity_ids": [str(value) for value in semantic_entity_ids],
            "semantic_evidence_ids": [str(value) for value in semantic_evidence_ids],
            "semantic_facts": list(semantic_facts)
            if isinstance(semantic_facts, (list, tuple))
            else [],
            "concept_source_map": {
                str(key): dict(value)
                for key, value in concept_source_map.items()
                if isinstance(value, dict)
            },
        },
        metadata={
            "table_id_prefix": settings.structure_id_prefix,
            "table_id_immutable": settings.structure_id_immutable,
            "primary_item": group_view.primary_item,
            "equivalent_concepts_count": len(group_view.equivalent_concepts),
            "providers_count": len(group_view.providers),
            "related_context_id": group_view.related_context.get("context_id", ""),
            "dynamic_column_builder_prepared": settings.dynamic_column_builder_prepared,
            "dynamic_row_builder_prepared": settings.dynamic_row_builder_prepared,
        },
    )


def build_structure_catalog(
    *,
    catalog_view: DomainModelCatalogView,
    structures: tuple[ComparativeTableBaseStructure, ...],
    dynamic_column_builder_prepared: bool,
    dynamic_row_builder_prepared: bool,
) -> ComparativeTableStructureCatalog:
    return ComparativeTableStructureCatalog(
        catalog_id=f"cse-catalog://{catalog_view.model_id}",
        process_id=catalog_view.process_id,
        model_id=catalog_view.model_id,
        document_id=catalog_view.document_id,
        source_domain_catalog_id=catalog_view.catalog_id,
        structures=structures,
        dynamic_column_builder_prepared=dynamic_column_builder_prepared,
        dynamic_row_builder_prepared=dynamic_row_builder_prepared,
        domain_model_preserved=True,
    )
