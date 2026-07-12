"""Extractor de tablas."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comprehension.extraction.enums import ExtractorType
from zovrake_motor.comprehension.extraction.extractors.base import metadata_value, prepared_result, result_with_tables
from zovrake_motor.comprehension.extraction.models import ContentExtractionRequest, ExtractedTable, ExtractorResult
from zovrake_motor.comprehension.extraction.port import ContentExtractorPort


class TablesExtractor(ContentExtractorPort):
    """Responsabilidad: detectar y extraer tablas del documento."""

    @property
    def extractor_name(self) -> str:
        return "tables_extractor"

    @property
    def extractor_label(self) -> str:
        return "Extractor de Tablas"

    @property
    def extractor_type(self) -> ExtractorType:
        return ExtractorType.TABLES

    def extract(self, request: ContentExtractionRequest) -> ExtractorResult:
        raw_tables = metadata_value(request, "tables", ())
        tables = self._parse_tables(raw_tables)
        if tables:
            return result_with_tables(
                extractor_name=self.extractor_name,
                extractor_type=self.extractor_type,
                tables=tables,
                observation="Tablas obtenidas desde metadatos del adaptador",
            )
        return prepared_result(
            extractor_name=self.extractor_name,
            extractor_type=self.extractor_type,
        )

    def _parse_tables(self, raw_tables: Any) -> tuple[ExtractedTable, ...]:
        if not raw_tables:
            return ()
        parsed: list[ExtractedTable] = []
        for index, item in enumerate(raw_tables):
            if isinstance(item, ExtractedTable):
                parsed.append(item)
                continue
            if isinstance(item, dict):
                rows = tuple(tuple(str(cell) for cell in row) for row in item.get("rows", ()))
                parsed.append(ExtractedTable(table_id=str(item.get("table_id", f"table_{index}")), rows=rows))
        return tuple(parsed)
