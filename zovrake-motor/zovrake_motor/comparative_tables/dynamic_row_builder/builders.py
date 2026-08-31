"""Utilidades de construcción de filas dinámicas."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comparative_tables.dynamic_row_builder.gateway import (
    ColumnCatalogView,
    ColumnSetView,
    RowBuildInputView,
    StructureCatalogView,
    StructureView,
)
from zovrake_motor.comparative_tables.dynamic_row_builder.models import (
    ComparativeTableCellPlaceholder,
    ComparativeTableRowCatalog,
    ComparativeTableRowDefinition,
    ComparativeTableRowSet,
    ComparativeTableRowTraceability,
)
from zovrake_motor.config.categories.comparative_tables import (
    DynamicRowBuilderSettings,
)


def build_public_row_id(
    sequence: int,
    *,
    prefix: str,
    padding: int,
) -> str:
    return f"{prefix}-{sequence:0{padding}d}"


def build_internal_row_id(
    table_id: str,
    sequence: int,
) -> str:
    return f"drb://{table_id}/row-{sequence:04d}"


def _structure_by_table_id(
    structure_catalog: StructureCatalogView,
) -> dict[str, StructureView]:
    return {
        structure.table_id: structure
        for structure in structure_catalog.structures
    }


def build_row_traceability(
    *,
    input_view: RowBuildInputView,
    column_set: ColumnSetView,
    provider_id: str,
) -> ComparativeTableRowTraceability:
    return ComparativeTableRowTraceability(
        process_id=input_view.column_catalog.process_id,
        document_id=input_view.column_catalog.document_id,
        model_id=input_view.column_catalog.model_id,
        source_column_catalog_id=(
            input_view.column_catalog.catalog_id
        ),
        source_structure_catalog_id=(
            input_view.structure_catalog.catalog_id
        ),
        source_table_id=column_set.table_id,
        source_group_id=column_set.group_id,
        source_provider_id=provider_id,
        column_catalog_preserved=True,
        structure_catalog_preserved=True,
        domain_model_preserved=(
            input_view.column_catalog.domain_model_preserved
        ),
    )


def build_cell_placeholders(
    column_set: ColumnSetView,
) -> tuple[ComparativeTableCellPlaceholder, ...]:
    return tuple(
        ComparativeTableCellPlaceholder(
            column_id=column.column_id,
            attribute_name=column.attribute_name,
            logical_position=column.logical_position,
            value_prepared=False,
        )
        for column in column_set.columns
    )


def _normalize_text(
    value: Any,
) -> str:
    return " ".join(
        str(value)
        .casefold()
        .split()
    )


def _as_string_tuple(
    value: Any,
) -> tuple[str, ...]:
    if not isinstance(
        value,
        (list, tuple, set, frozenset),
    ):
        return ()

    return tuple(
        dict.fromkeys(
            str(item).strip()
            for item in value
            if str(item).strip()
        )
    )


def _provider_semantic_context(
    *,
    structure_view: StructureView,
    provider_id: str,
) -> dict[str, Any]:
    """
    Obtiene únicamente la parte del conocimiento semántico que puede
    asociarse de forma conservadora al proveedor de la fila.

    No crea una fila nueva ni decide equivalencias. La finalidad es conservar
    trazabilidad ya calculada aguas arriba.
    """
    semantic = structure_view.semantic_knowledge

    if not isinstance(
        semantic,
        dict,
    ):
        return {
            "available": False,
            "matched": False,
            "entity_ids": (),
            "fact_ids": (),
            "evidence_ids": (),
            "facts": (),
        }

    provider_normalized = _normalize_text(
        provider_id
    )

    raw_entity_ids = _as_string_tuple(
        semantic.get(
            "semantic_entity_ids",
            (),
        )
    )

    raw_evidence_ids = _as_string_tuple(
        semantic.get(
            "semantic_evidence_ids",
            (),
        )
    )

    raw_facts = semantic.get(
        "semantic_facts",
        (),
    )

    facts: list[dict[str, Any]] = []

    if isinstance(
        raw_facts,
        (list, tuple),
    ):
        for raw_fact in raw_facts:
            if not isinstance(
                raw_fact,
                dict,
            ):
                continue

            facts.append(
                dict(raw_fact)
            )

    # Algunas versiones pueden conservar directamente el linked_entity_id.
    # Cuando existe, es la evidencia más fuerte para asociar el hecho a una
    # fila/proveedor concreto.
    matched_entity_ids: list[str] = []
    matched_fact_ids: list[str] = []
    matched_evidence_ids: list[str] = []
    matched_facts: list[dict[str, Any]] = []

    for fact in facts:
        linked_entity_id = str(
            fact.get(
                "linked_entity_id",
                "",
            )
        ).strip()

        if (
            linked_entity_id
            and linked_entity_id in raw_entity_ids
        ):
            # Todavía debemos conocer el nombre/identificador de la entidad.
            # Esa información no siempre viaja en semantic_facts, por lo que
            # dejamos el vínculo explícito y conservador.
            matched_entity_ids.append(
                linked_entity_id
            )
            matched_fact_ids.append(
                str(
                    fact.get(
                        "fact_id",
                        "",
                    )
                ).strip()
            )
            evidence_id = str(
                fact.get(
                    "evidence_id",
                    "",
                )
            ).strip()

            if evidence_id:
                matched_evidence_ids.append(
                    evidence_id
                )

            matched_facts.append(
                fact
            )
            continue

        # Fallback textual conservador: solo aceptamos una coincidencia
        # completa entre el provider_id y un valor textual del hecho.
        raw_value = _normalize_text(
            fact.get(
                "raw_value",
                fact.get(
                    "value",
                    "",
                ),
            )
        )

        label = _normalize_text(
            fact.get(
                "label",
                "",
            )
        )

        if (
            provider_normalized
            and raw_value
            and raw_value == provider_normalized
            and label
            in {
                "nombre",
                "name",
                "razon social",
                "razón social",
                "legal name",
                "razon_social",
                "razón_social",
            }
        ):
            matched_fact_ids.append(
                str(
                    fact.get(
                        "fact_id",
                        "",
                    )
                ).strip()
            )

            evidence_id = str(
                fact.get(
                    "evidence_id",
                    "",
                )
            ).strip()

            if evidence_id:
                matched_evidence_ids.append(
                    evidence_id
                )

            matched_facts.append(
                fact
            )

    matched_fact_ids = [
        value
        for value in dict.fromkeys(
            matched_fact_ids
        )
        if value
    ]

    matched_evidence_ids = [
        value
        for value in dict.fromkeys(
            (
                *matched_evidence_ids,
            )
        )
        if value
    ]

    matched_entity_ids = [
        value
        for value in dict.fromkeys(
            matched_entity_ids
        )
        if value
    ]

    # Si no existe un vínculo específico, no atribuimos todos los hechos del
    # grupo al proveedor. Conservamos únicamente la disponibilidad general.
    return {
        "available": bool(
            semantic.get(
                "semantic_knowledge_available",
                False,
            )
        ),
        "matched": bool(
            matched_entity_ids
            or matched_fact_ids
        ),
        "entity_ids": tuple(
            matched_entity_ids
        ),
        "fact_ids": tuple(
            matched_fact_ids
        ),
        "evidence_ids": tuple(
            matched_evidence_ids
        ),
        "facts": tuple(
            matched_facts
        ),
        "group_entity_ids": raw_entity_ids,
        "group_evidence_ids": raw_evidence_ids,
    }


def build_row_definition(
    *,
    input_view: RowBuildInputView,
    column_set: ColumnSetView,
    provider_id: str,
    logical_position: int,
    public_row_id: str,
    internal_sequence: int,
    settings: DynamicRowBuilderSettings,
    structure_view: StructureView | None = None,
) -> ComparativeTableRowDefinition:
    column_references = tuple(
        column.column_id
        for column in column_set.columns
    )
    cells_reserved = build_cell_placeholders(
        column_set
    )

    semantic_context = (
        _provider_semantic_context(
            structure_view=structure_view,
            provider_id=provider_id,
        )
        if structure_view is not None
        else {
            "available": False,
            "matched": False,
            "entity_ids": (),
            "fact_ids": (),
            "evidence_ids": (),
            "facts": (),
            "group_entity_ids": (),
            "group_evidence_ids": (),
        }
    )

    return ComparativeTableRowDefinition(
        row_id=public_row_id,
        internal_row_id=build_internal_row_id(
            column_set.table_id,
            internal_sequence,
        ),
        provider_id=provider_id,
        logical_position=logical_position,
        group_id=column_set.group_id,
        table_id=column_set.table_id,
        column_references=column_references,
        cells_reserved=cells_reserved,
        traceability=build_row_traceability(
            input_view=input_view,
            column_set=column_set,
            provider_id=provider_id,
        ),
        metadata={
            "row_id_prefix": settings.row_id_prefix,
            "row_id_immutable": settings.row_id_immutable,
            "cell_values_prepared": False,
            "columns_linked": len(
                column_references
            ),
            "semantic_knowledge_available": (
                semantic_context[
                    "available"
                ]
            ),
            "semantic_knowledge_matched": (
                semantic_context[
                    "matched"
                ]
            ),
            "semantic_entity_ids": list(
                semantic_context[
                    "entity_ids"
                ]
            ),
            "semantic_fact_ids": list(
                semantic_context[
                    "fact_ids"
                ]
            ),
            "semantic_evidence_ids": list(
                semantic_context[
                    "evidence_ids"
                ]
            ),
            "semantic_facts": list(
                semantic_context[
                    "facts"
                ]
            ),
            "semantic_group_entity_ids": list(
                semantic_context[
                    "group_entity_ids"
                ]
            ),
            "semantic_group_evidence_ids": list(
                semantic_context[
                    "group_evidence_ids"
                ]
            ),
        },
    )


def build_row_set_for_column_set(
    *,
    input_view: RowBuildInputView,
    column_set: ColumnSetView,
    structure_view: StructureView,
    settings: DynamicRowBuilderSettings,
    start_sequence: int,
) -> tuple[
    ComparativeTableRowSet,
    int,
]:
    rows: list[
        ComparativeTableRowDefinition
    ] = []

    sequence = start_sequence
    providers = structure_view.available_providers

    for position, provider_id in enumerate(
        providers,
        start=1,
    ):
        public_row_id = build_public_row_id(
            sequence,
            prefix=settings.row_id_prefix,
            padding=settings.row_id_padding,
        )

        rows.append(
            build_row_definition(
                input_view=input_view,
                column_set=column_set,
                provider_id=provider_id,
                logical_position=position,
                public_row_id=public_row_id,
                internal_sequence=sequence,
                settings=settings,
                structure_view=structure_view,
            ),
        )

        sequence += 1

    row_set = ComparativeTableRowSet(
        table_id=column_set.table_id,
        group_id=column_set.group_id,
        rows=tuple(rows),
        source_column_catalog_id=(
            input_view.column_catalog.catalog_id
        ),
        source_structure_catalog_id=(
            input_view.structure_catalog.catalog_id
        ),
    )

    return row_set, sequence


def build_row_catalog(
    *,
    input_view: RowBuildInputView,
    row_sets: tuple[
        ComparativeTableRowSet,
        ...,
    ],
    provider_organization_engine_prepared: bool,
) -> ComparativeTableRowCatalog:
    return ComparativeTableRowCatalog(
        catalog_id=(
            f"drb-catalog://"
            f"{input_view.column_catalog.model_id}"
        ),
        process_id=(
            input_view.column_catalog.process_id
        ),
        model_id=(
            input_view.column_catalog.model_id
        ),
        document_id=(
            input_view.column_catalog.document_id
        ),
        source_column_catalog_id=(
            input_view.column_catalog.catalog_id
        ),
        source_structure_catalog_id=(
            input_view.structure_catalog.catalog_id
        ),
        row_sets=row_sets,
        provider_organization_engine_prepared=(
            provider_organization_engine_prepared
        ),
        column_catalog_preserved=True,
        structure_catalog_preserved=True,
        domain_model_preserved=(
            input_view.column_catalog.domain_model_preserved
        ),
    )


def resolve_structure_for_column_set(
    *,
    column_set: ColumnSetView,
    structures_by_table: dict[str, StructureView],
) -> StructureView | None:
    structure = structures_by_table.get(
        column_set.table_id
    )

    if (
        structure is not None
        and structure.group_id
        == column_set.group_id
    ):
        return structure

    return None
