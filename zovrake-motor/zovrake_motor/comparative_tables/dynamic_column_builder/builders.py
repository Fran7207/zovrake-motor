"""Utilidades de construcción de columnas dinámicas."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comparative_tables.dynamic_column_builder.enums import ColumnDataType
from zovrake_motor.comparative_tables.dynamic_column_builder.gateway import (
    StructureCatalogView,
    StructureView,
)
from zovrake_motor.comparative_tables.dynamic_column_builder.models import (
    ComparativeTableColumnCatalog,
    ComparativeTableColumnDefinition,
    ComparativeTableColumnSet,
    ComparativeTableColumnTraceability,
)
from zovrake_motor.config.categories.comparative_tables import DynamicColumnBuilderSettings


_SEMANTIC_NON_COLUMN_LABELS = {
    "",
    "monetary_value",
    "percentage",
    "date",
    "email",
    "url",
    "measurement",
    "identifier",
    "ruc",
    "dni",
    "nit",
    "cuit",
    "rif",
    "rfc",
    "id",
}


def infer_data_type(value: Any) -> ColumnDataType:
    if isinstance(value, bool):
        return ColumnDataType.BOOLEAN
    if isinstance(value, int) and not isinstance(value, bool):
        return ColumnDataType.INTEGER
    if isinstance(value, float):
        return ColumnDataType.NUMBER
    if isinstance(value, (list, tuple)):
        return ColumnDataType.LIST
    return ColumnDataType.STRING


def _normalize_attribute_name(name: Any) -> str:
    return " ".join(
        str(name).strip().casefold().split()
    )


def _semantic_fact_column_candidate(
    fact: dict[str, Any],
) -> tuple[str, str, ColumnDataType, Any] | None:
    """
    Convierte un hecho semántico en candidato de columna únicamente cuando
    el hecho contiene una etiqueta útil para comparación.

    Los hechos genéricos (moneda aislada, fecha aislada, medición aislada,
    identificador aislado, etc.) no se convierten automáticamente en columnas.
    Un hecho etiquetado sí puede hacerlo, por ejemplo:

        quantity=138
        unit=UNIDAD
        description=CEMENTO PORTLAND TIPO I
        unit_price=19.90
    """
    label = str(
        fact.get(
            "label",
            fact.get(
                "normalized_label",
                "",
            ),
        )
    ).strip()

    normalized_label = _normalize_attribute_name(
        label
    )

    if (
        not normalized_label
        or normalized_label in _SEMANTIC_NON_COLUMN_LABELS
    ):
        return None

    fact_type = _normalize_attribute_name(
        fact.get(
            "fact_type",
            "",
        )
    )

    # Solo los hechos con semántica de campo/atributo aportan una columna.
    if fact_type not in {
        "labeled_value",
        "table_field",
    }:
        return None

    value = fact.get(
        "value",
        fact.get(
            "raw_value",
            "",
        ),
    )

    return (
        label,
        "semantic",
        infer_data_type(value),
        value,
    )


def extract_attribute_candidates(
    available_attributes: dict[str, Any],
    semantic_knowledge: dict[str, Any] | None = None,
    concept_source_map: dict[str, Any] | None = None,
) -> list[tuple[str, str, ColumnDataType, Any]]:
    """
    Extrae candidatos de columnas desde dos fuentes:

    1. atributos estructurados tradicionales del CSE;
    2. hechos semánticos ya preservados por PM5/CDMB.

    La segunda fuente es complementaria. Nunca reemplaza la primera.

    Retorna tuplas:
        (nombre, fuente, tipo, valor_referencia)

    Las dos fuentes se deduplican por nombre normalizado.
    """
    candidates: list[tuple[str, str, ColumnDataType, Any]] = []
    seen_names: set[str] = set()

    commercial = dict(
        available_attributes.get(
            "commercial",
            {},
        )
    )

    for name, value in sorted(
        commercial.items()
    ):
        normalized = _normalize_attribute_name(
            name
        )

        if (
            not normalized
            or normalized in seen_names
        ):
            continue

        seen_names.add(
            normalized
        )

        candidates.append(
            (
                str(name),
                "commercial",
                infer_data_type(value),
                value,
            )
        )

    technical = dict(
        available_attributes.get(
            "technical",
            {},
        )
    )

    for name, value in sorted(
        technical.items()
    ):
        normalized = _normalize_attribute_name(
            name
        )

        if (
            not normalized
            or normalized in seen_names
        ):
            continue

        seen_names.add(
            normalized
        )

        candidates.append(
            (
                str(name),
                "technical",
                infer_data_type(value),
                value,
            )
        )

    specifications = available_attributes.get(
        "specifications",
        [],
    )

    if isinstance(
        specifications,
        (list, tuple),
    ):
        for specification in specifications:
            name = str(
                specification
            ).strip()

            normalized = _normalize_attribute_name(
                name
            )

            if (
                not normalized
                or normalized in seen_names
            ):
                continue

            seen_names.add(
                normalized
            )

            candidates.append(
                (
                    name,
                    "specification",
                    ColumnDataType.SPECIFICATION,
                    specification,
                )
            )

    primary_item = str(
        available_attributes.get(
            "primary_item",
            "",
        )
    ).strip()

    if primary_item:
        normalized = _normalize_attribute_name(
            primary_item
        )

        if (
            normalized
            and normalized not in seen_names
        ):
            seen_names.add(
                normalized
            )

            candidates.append(
                (
                    primary_item,
                    "primary_item",
                    ColumnDataType.STRING,
                    primary_item,
                )
            )

    # -------------------------------------------------------------
    # Campos observados en los ítems fuente.
    #
    # CSE conserva concept_source_map por concepto. DCB puede usarlo para
    # descubrir la unión de atributos realmente presentes en las ofertas,
    # sin imponer una plantilla fija. Los campos desconocidos se conservan
    # con su nombre original para que PM6 pueda compararlos después.
    # -------------------------------------------------------------
    if isinstance(concept_source_map, dict):
        observed_fields: dict[str, Any] = {}

        standard_item_fields = (
            ("description", "Descripción"),
            ("quantity", "Cantidad"),
            ("unit", "Unidad"),
            ("unit_price", "Precio Unitario"),
            ("total", "Total"),
            ("code", "Código"),
            ("brand", "Marca"),
        )

        def add_observed(
            raw_name: Any,
            value: Any,
        ) -> None:
            name = str(raw_name).strip()
            if not name:
                return
            normalized = _normalize_attribute_name(name)
            if not normalized or normalized in seen_names:
                return
            if normalized not in observed_fields:
                observed_fields[normalized] = value

        visible_by_normalized: dict[str, str] = {}

        for source in concept_source_map.values():
            if not isinstance(source, dict):
                continue

            for key, display_name in standard_item_fields:
                value = source.get(key, "")
                if value not in (None, ""):
                    add_observed(display_name, value)
                    visible_by_normalized.setdefault(
                        _normalize_attribute_name(display_name),
                        display_name,
                    )

            raw_fields = source.get("fields", {})
            if isinstance(raw_fields, dict):
                for key, value in raw_fields.items():
                    if value in (None, ""):
                        continue
                    add_observed(key, value)
                    visible_by_normalized.setdefault(
                        _normalize_attribute_name(key),
                        str(key).strip(),
                    )

        for normalized_name, value in sorted(observed_fields.items()):
            if normalized_name in seen_names:
                continue
            visible_name = visible_by_normalized.get(
                normalized_name,
                normalized_name,
            )
            seen_names.add(normalized_name)
            candidates.append(
                (
                    visible_name,
                    "source_item",
                    infer_data_type(value),
                    value,
                )
            )

    # -------------------------------------------------------------
    # Conocimiento semántico.
    #
    # Se agrega después de los atributos estructurados para que, si
    # "Precio" ya existe en CSE, el hecho semántico equivalente no cree
    # una segunda columna.
    # -------------------------------------------------------------
    if isinstance(
        semantic_knowledge,
        dict,
    ):
        semantic_facts = semantic_knowledge.get(
            "semantic_facts",
            (),
        )

        if isinstance(
            semantic_facts,
            (list, tuple),
        ):
            for fact in semantic_facts:
                if not isinstance(
                    fact,
                    dict,
                ):
                    continue

                candidate = _semantic_fact_column_candidate(
                    fact
                )

                if candidate is None:
                    continue

                name, source, data_type, reference_value = candidate

                normalized = _normalize_attribute_name(
                    name
                )

                if (
                    not normalized
                    or normalized in seen_names
                ):
                    continue

                seen_names.add(
                    normalized
                )

                candidates.append(
                    (
                        name,
                        source,
                        data_type,
                        reference_value,
                    )
                )

    return candidates


def build_public_column_id(
    sequence: int,
    *,
    prefix: str,
    padding: int,
) -> str:
    return f"{prefix}-{sequence:0{padding}d}"


def build_internal_column_id(
    table_id: str,
    sequence: int,
) -> str:
    return f"dcb://{table_id}/column-{sequence:04d}"


def build_column_traceability(
    *,
    catalog_view: StructureCatalogView,
    structure_view: StructureView,
    attribute_source: str,
) -> ComparativeTableColumnTraceability:
    return ComparativeTableColumnTraceability(
        process_id=catalog_view.process_id,
        document_id=catalog_view.document_id,
        model_id=catalog_view.model_id,
        source_structure_catalog_id=catalog_view.catalog_id,
        source_table_id=structure_view.table_id,
        source_group_id=structure_view.group_id,
        source_comparative_model_id=structure_view.comparative_model_id,
        attribute_source=attribute_source,
        structure_catalog_preserved=True,
        domain_model_preserved=catalog_view.domain_model_preserved,
    )


def build_column_definition(
    *,
    catalog_view: StructureCatalogView,
    structure_view: StructureView,
    attribute_name: str,
    attribute_source: str,
    data_type: ColumnDataType,
    logical_position: int,
    public_column_id: str,
    internal_sequence: int,
    reference_value: Any,
    settings: DynamicColumnBuilderSettings,
) -> ComparativeTableColumnDefinition:
    semantic_knowledge = structure_view.semantic_knowledge

    semantic_fact_ids = []
    semantic_evidence_ids = []
    semantic_entity_ids = []
    semantic_attribute_ids = []

    if isinstance(
        semantic_knowledge,
        dict,
    ):
        semantic_fact_ids = list(
            semantic_knowledge.get(
                "semantic_fact_ids",
                (),
            )
            or ()
        )
        semantic_evidence_ids = list(
            semantic_knowledge.get(
                "semantic_evidence_ids",
                (),
            )
            or ()
        )
        semantic_entity_ids = list(
            semantic_knowledge.get(
                "semantic_entity_ids",
                (),
            )
            or ()
        )
        semantic_attribute_ids = list(
            semantic_knowledge.get(
                "semantic_attribute_ids",
                (),
            )
            or ()
        )

    return ComparativeTableColumnDefinition(
        column_id=public_column_id,
        internal_column_id=build_internal_column_id(
            structure_view.table_id,
            internal_sequence,
        ),
        attribute_name=attribute_name,
        data_type=data_type,
        logical_position=logical_position,
        group_id=structure_view.group_id,
        table_id=structure_view.table_id,
        traceability=build_column_traceability(
            catalog_view=catalog_view,
            structure_view=structure_view,
            attribute_source=attribute_source,
        ),
        metadata={
            "column_id_prefix": settings.column_id_prefix,
            "column_id_immutable": settings.column_id_immutable,
            "attribute_source": attribute_source,
            "reference_value_type": type(reference_value).__name__,
            "provider_values_prepared": False,
            "semantic_knowledge_used": (
                attribute_source == "semantic"
            ),
            "semantic_fact_ids": semantic_fact_ids
            if attribute_source == "semantic"
            else [],
            "semantic_attribute_ids": semantic_attribute_ids
            if attribute_source == "semantic"
            else [],
            "semantic_entity_ids": semantic_entity_ids
            if attribute_source == "semantic"
            else [],
            "semantic_evidence_ids": semantic_evidence_ids
            if attribute_source == "semantic"
            else [],
        },
    )


def build_column_set_for_structure(
    *,
    catalog_view: StructureCatalogView,
    structure_view: StructureView,
    settings: DynamicColumnBuilderSettings,
    start_sequence: int,
) -> tuple[ComparativeTableColumnSet, int]:
    candidates = extract_attribute_candidates(
        structure_view.available_attributes,
        structure_view.semantic_knowledge,
        structure_view.concept_source_map,
    )

    columns: list[
        ComparativeTableColumnDefinition
    ] = []

    sequence = start_sequence

    for position, (
        name,
        source,
        data_type,
        reference_value,
    ) in enumerate(
        candidates,
        start=1,
    ):
        public_column_id = build_public_column_id(
            sequence,
            prefix=settings.column_id_prefix,
            padding=settings.column_id_padding,
        )

        columns.append(
            build_column_definition(
                catalog_view=catalog_view,
                structure_view=structure_view,
                attribute_name=name,
                attribute_source=source,
                data_type=data_type,
                logical_position=position,
                public_column_id=public_column_id,
                internal_sequence=sequence,
                reference_value=reference_value,
                settings=settings,
            )
        )

        sequence += 1

    column_set = ComparativeTableColumnSet(
        table_id=structure_view.table_id,
        group_id=structure_view.group_id,
        columns=tuple(
            columns
        ),
        source_structure_catalog_id=catalog_view.catalog_id,
    )

    return column_set, sequence


def build_column_catalog(
    *,
    catalog_view: StructureCatalogView,
    column_sets: tuple[
        ComparativeTableColumnSet,
        ...,
    ],
    dynamic_row_builder_prepared: bool,
) -> ComparativeTableColumnCatalog:
    return ComparativeTableColumnCatalog(
        catalog_id=(
            f"dcb-catalog://"
            f"{catalog_view.model_id}"
        ),
        process_id=catalog_view.process_id,
        model_id=catalog_view.model_id,
        document_id=catalog_view.document_id,
        source_structure_catalog_id=(
            catalog_view.catalog_id
        ),
        column_sets=column_sets,
        dynamic_row_builder_prepared=(
            dynamic_row_builder_prepared
        ),
        structure_catalog_preserved=True,
        domain_model_preserved=(
            catalog_view.domain_model_preserved
        ),
    )
