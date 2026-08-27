"""Transformador de la sección Ítems."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comprehension.canonical.enums import CanonicalSectionType
from zovrake_motor.comprehension.canonical.models import (
    CanonicalItem,
    CanonicalTraceability,
    SectionTransformationResult,
)
from zovrake_motor.comprehension.canonical.port import ItemsTransformerPort
from zovrake_motor.comprehension.canonical.transformers.base import (
    metadata_value,
    prepared_section_result,
    source_reference,
)
from zovrake_motor.comprehension.extraction.models import ContentExtractionResult


class ItemsTransformer(ItemsTransformerPort):
    """Responsabilidad: transformar ítems detectados."""

    @property
    def transformer_name(self) -> str:
        return "items_transformer"

    @property
    def transformer_label(self) -> str:
        return "Transformador de Ítems"

    @property
    def section_type(self) -> CanonicalSectionType:
        return CanonicalSectionType.ITEMS

    def transform(
        self,
        extraction_result: ContentExtractionResult,
        *,
        traceability: CanonicalTraceability,
    ) -> SectionTransformationResult:
        self.build_items(
            extraction_result,
            traceability=traceability,
        )

        return prepared_section_result(
            transformer_name=self.transformer_name,
            section_type=self.section_type,
            observation=(
                "Ítems transformados desde tablas y listas de extracción"
            ),
        )

    def build_items(
        self,
        extraction_result: ContentExtractionResult,
        *,
        traceability: CanonicalTraceability,
    ) -> tuple[CanonicalItem, ...]:
        """
        Construye ítems priorizando la semántica descubierta del documento.

        La estructura de la tabla no se considera fija. Todas las columnas
        semánticas descubiertas se conservan en ``fields`` y solamente se
        proyectan a los campos canónicos aquellos atributos reconocidos.

        Orden de prioridad:

        1. semantic_tables
        2. tablas físicas
        3. items entregados por metadata

        Nunca se fabrican ítems cuando no existe evidencia.
        """
        items: list[CanonicalItem] = []

        section_ref = source_reference(
            traceability.extraction_reference_id,
            self.section_type,
        )

        semantic_tables = metadata_value(
            extraction_result,
            "semantic_tables",
            (),
        )

        if isinstance(semantic_tables, (list, tuple)):
            for table_index, semantic_table in enumerate(
                semantic_tables
            ):
                if not isinstance(semantic_table, dict):
                    continue

                table_id = str(
                    semantic_table.get(
                        "table_id",
                        f"semantic-table-{table_index + 1}",
                    )
                ).strip()

                if not table_id:
                    table_id = (
                        f"semantic-table-{table_index + 1}"
                    )

                columns = semantic_table.get(
                    "columns",
                    (),
                )

                rows = semantic_table.get(
                    "rows",
                    (),
                )

                if not isinstance(
                    columns,
                    (list, tuple),
                ):
                    continue

                if not isinstance(
                    rows,
                    (list, tuple),
                ):
                    continue

                column_keys: list[str] = []

                for column in columns:
                    if not isinstance(column, dict):
                        continue

                    key = str(
                        column.get(
                            "key",
                            "",
                        )
                    ).strip()

                    if key and key not in column_keys:
                        column_keys.append(key)

                if not column_keys:
                    continue

                table_confidence = semantic_table.get(
                    "confidence",
                    0.0,
                )

                source_page_number = semantic_table.get(
                    "source_page_number",
                )

                table_evidence = semantic_table.get(
                    "evidence",
                    [],
                )

                if not isinstance(
                    table_evidence,
                    (list, tuple),
                ):
                    table_evidence = [str(table_evidence)]

                for row_index, raw_row in enumerate(
                    rows
                ):
                    if not isinstance(
                        raw_row,
                        dict,
                    ):
                        continue

                    fields: dict[str, Any] = {
                        key: raw_row.get(
                            key,
                            "",
                        )
                        for key in column_keys
                    }

                    if not any(
                        str(value).strip()
                        for value in fields.values()
                    ):
                        continue

                    description = str(
                        fields.get(
                            "description",
                            "",
                        )
                    ).strip()

                    quantity = str(
                        fields.get(
                            "quantity",
                            "",
                        )
                    ).strip()

                    unit_price = str(
                        fields.get(
                            "unit_price",
                            "",
                        )
                    ).strip()

                    unit = str(
                        fields.get(
                            "unit",
                            "",
                        )
                    ).strip()

                    source_table_id = str(
                        semantic_table.get(
                            "source_table_id",
                            "",
                        )
                    ).strip()

                    evidence_source = (
                        source_table_id
                        or table_id
                    )

                    item_fields: dict[str, Any] = {
                        "semantic_table_id": table_id,
                        "semantic_table_confidence": (
                            table_confidence
                        ),
                        "semantic_table_source_page_number": (
                            source_page_number
                        ),
                        "semantic_table_evidence": list(
                            table_evidence
                        ),
                        "semantic_columns": list(
                            column_keys
                        ),
                        "values": fields,
                    }

                    if source_table_id:
                        item_fields[
                            "source_table_id"
                        ] = source_table_id

                    items.append(
                        CanonicalItem(
                            item_id=(
                                f"{table_id}"
                                f"-row-{row_index}"
                            ),
                            description=description,
                            source_reference=(
                                f"{section_ref}/"
                                f"{evidence_source}/"
                                f"{row_index}"
                            ),
                            quantity=quantity,
                            unit_price=unit_price,
                            unit=unit,
                            fields=item_fields,
                        ),
                    )

        # -------------------------------------------------------------
        # Fallback controlado:
        # utilizar tablas físicas únicamente cuando no existe una
        # representación semántica utilizable.
        # -------------------------------------------------------------
        if not items:
            for table_index, table in enumerate(
                extraction_result.tables
            ):
                rows = list(table.rows)

                if not rows:
                    continue

                start = 0

                header_text = " ".join(
                    str(cell)
                    for cell in rows[0]
                ).lower()

                header_markers = (
                    "descripcion",
                    "descripción",
                    "item",
                    "ítem",
                    "cantidad",
                    "precio",
                    "unidad",
                    "total",
                    "concepto",
                )

                hits = sum(
                    1
                    for marker in header_markers
                    if marker in header_text
                )

                if hits >= 2:
                    start = 1

                for row_index, row in enumerate(
                    rows[start:]
                ):
                    if not row:
                        continue

                    values = [
                        str(value).strip()
                        for value in row
                    ]

                    if not any(values):
                        continue

                    description = (
                        values[0]
                        if len(values) > 0
                        else ""
                    )

                    quantity = (
                        values[1]
                        if len(values) > 1
                        else ""
                    )

                    unit_price = (
                        values[2]
                        if len(values) > 2
                        else ""
                    )

                    unit = (
                        values[3]
                        if len(values) > 3
                        else ""
                    )

                    items.append(
                        CanonicalItem(
                            item_id=(
                                f"{table.table_id}"
                                f"-row-{row_index}"
                            ),
                            description=description,
                            source_reference=(
                                f"{section_ref}/"
                                f"{table.table_id}/"
                                f"{row_index}"
                            ),
                            quantity=quantity,
                            unit_price=unit_price,
                            unit=unit,
                            fields={
                                "table_id": table.table_id,
                                "fallback": (
                                    "physical_table"
                                ),
                                "table_index": table_index,
                                "values": values,
                            },
                        ),
                    )

        # -------------------------------------------------------------
        # Último fallback:
        # utilizar únicamente ítems que ya hayan sido entregados por
        # metadata externa.
        # -------------------------------------------------------------
        if not items:
            raw_items = metadata_value(
                extraction_result,
                "items",
                (),
            )

            if isinstance(
                raw_items,
                (list, tuple),
            ):
                for index, item_data in enumerate(
                    raw_items
                ):
                    if not isinstance(
                        item_data,
                        dict,
                    ):
                        continue

                    items.append(
                        CanonicalItem(
                            item_id=str(
                                item_data.get(
                                    "item_id",
                                    f"meta-item-{index}",
                                )
                            ),
                            description=str(
                                item_data.get(
                                    "description",
                                    "",
                                )
                            ),
                            source_reference=(
                                f"{section_ref}/"
                                f"metadata/{index}"
                            ),
                            quantity=str(
                                item_data.get(
                                    "quantity",
                                    "",
                                )
                            ),
                            unit_price=str(
                                item_data.get(
                                    "unit_price",
                                    "",
                                )
                            ),
                            unit=str(
                                item_data.get(
                                    "unit",
                                    "",
                                )
                            ),
                            fields=dict(
                                item_data
                            ),
                        ),
                    )

        return tuple(items)