"""Transformador de la sección Ítems."""

from __future__ import annotations

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
        self.build_items(extraction_result, traceability=traceability)
        return prepared_section_result(
            transformer_name=self.transformer_name,
            section_type=self.section_type,
            observation="Ítems transformados desde tablas y listas de extracción",
        )

    def build_items(
        self,
        extraction_result: ContentExtractionResult,
        *,
        traceability: CanonicalTraceability,
    ) -> tuple[CanonicalItem, ...]:
        items: list[CanonicalItem] = []
        section_ref = source_reference(traceability.extraction_reference_id, self.section_type)

        for index, table in enumerate(extraction_result.tables):
            rows = list(table.rows)
            start = 0
            if rows:
                header_text = " ".join(str(cell) for cell in rows[0]).lower()
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
                hits = sum(1 for marker in header_markers if marker in header_text)
                if hits >= 2:
                    start = 1
            for row_index, row in enumerate(rows[start:]):
                if not row:
                    continue
                description = row[0] if len(row) > 0 else ""
                quantity = row[1] if len(row) > 1 else ""
                unit_price = row[2] if len(row) > 2 else ""
                unit = row[3] if len(row) > 3 else ""
                items.append(
                    CanonicalItem(
                        item_id=f"{table.table_id}-row-{row_index}",
                        description=str(description),
                        source_reference=f"{section_ref}/{table.table_id}/{row_index}",
                        quantity=str(quantity),
                        unit_price=str(unit_price),
                        unit=str(unit),
                        fields={"table_id": table.table_id},
                    ),
                )

        raw_items = metadata_value(extraction_result, "items", ())
        if isinstance(raw_items, (list, tuple)):
            for index, item_data in enumerate(raw_items):
                if isinstance(item_data, dict):
                    items.append(
                        CanonicalItem(
                            item_id=str(item_data.get("item_id", f"meta-item-{index}")),
                            description=str(item_data.get("description", "")),
                            source_reference=f"{section_ref}/metadata/{index}",
                            quantity=str(item_data.get("quantity", "")),
                            unit_price=str(item_data.get("unit_price", "")),
                            unit=str(item_data.get("unit", "")),
                            fields=item_data,
                        ),
                    )

        return tuple(items)
