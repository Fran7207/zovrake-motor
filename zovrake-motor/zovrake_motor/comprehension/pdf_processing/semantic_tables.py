from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Sequence

from .models import (
    PdfSemanticTable,
    PdfTable,
    PdfTableColumn,
)


@dataclass(frozen=True)
class _ColumnCandidate:
    key: str
    label: str
    index: int
    confidence: float
    evidence: tuple[str, ...] = ()


class PdfSemanticTableAnalyzer:
    """
    Analizador semántico de tablas PDF.

    Convierte una representación física de una tabla en una
    representación semántica sin imponer una estructura fija
    de cotización.

    La semántica se determina a partir de las etiquetas y del
    contenido real de las columnas.
    """

    _COLUMN_ALIASES: dict[str, tuple[str, ...]] = {
        "code": (
            "codigo",
            "código",
            "cod",
            "item",
            "ítem",
            "sku",
            "partida",
        ),
        "description": (
            "descripcion",
            "descripción",
            "producto",
            "concepto",
            "detalle",
            "material",
            "servicio",
        ),
        "quantity": (
            "cantidad",
            "cant",
            "cant.",
            "qty",
            "volumen",
        ),
        "unit": (
            "unidad",
            "und",
            "und.",
            "u.m.",
            "u.medida",
            "umedida",
        ),
        "unit_price": (
            "precio unitario",
            "p. unitario",
            "p.unitario",
            "p.u.",
            "pu",
            "p/u",
            "precio",
        ),
        "total": (
            "total",
            "importe",
            "monto",
            "subtotal",
            "valor total",
        ),
        "brand": (
            "marca",
        ),
        "model": (
            "modelo",
        ),
        "currency": (
            "moneda",
        ),
        "discount": (
            "descuento",
            "desc.",
        ),
        "tax": (
            "igv",
            "iva",
            "impuesto",
        ),
    }

    def analyze(
        self,
        table: PdfTable,
    ) -> PdfSemanticTable | None:
        """
        Analiza una tabla física y devuelve su representación semántica.

        Si no existe suficiente información para identificar una
        estructura semántica confiable, devuelve None.
        """
        rows = self._clean_rows(table.rows)

        if not rows:
            return None

        header_index = self._find_header_row(rows)

        if header_index is None:
            return None

        headers = rows[header_index]

        columns = self._infer_columns(headers)

        if not columns:
            return None

        data_rows = rows[header_index + 1:]

        semantic_rows = self._build_rows(
            data_rows=data_rows,
            columns=columns,
        )

        if not semantic_rows:
            return None

        confidence = self._calculate_confidence(
            columns=columns,
            rows=semantic_rows,
        )

        return PdfSemanticTable(
            table_id=f"{table.table_id}-semantic",
            columns=tuple(
                PdfTableColumn(
                    key=column.key,
                    label=column.label,
                    index=column.index,
                    confidence=column.confidence,
                    evidence=column.evidence,
                )
                for column in columns
            ),
            rows=tuple(semantic_rows),
            confidence=confidence,
            source_table_id=table.table_id,
            source_page_number=table.page_number,
            evidence=(
                f"page:{table.page_number}",
                f"table:{table.table_id}",
                f"header_row:{header_index}",
            ),
        )

    @staticmethod
    def _clean_rows(
        rows: Sequence[Sequence[Any]],
    ) -> list[tuple[str, ...]]:
        cleaned: list[tuple[str, ...]] = []

        for row in rows:
            normalized = tuple(
                str(value).strip()
                if value is not None
                else ""
                for value in row
            )

            if any(normalized):
                cleaned.append(normalized)

        return cleaned

    def _find_header_row(
        self,
        rows: Sequence[tuple[str, ...]],
    ) -> int | None:
        best_index: int | None = None
        best_score = 0.0

        for index, row in enumerate(rows[:8]):
            score = self._header_score(row)

            if score > best_score:
                best_score = score
                best_index = index

        if best_score < 0.40:
            return None

        return best_index

    def _header_score(
        self,
        row: Sequence[str],
    ) -> float:
        if not row:
            return 0.0

        recognized = 0

        for cell in row:
            normalized = self._normalize_label(cell)

            if any(
                alias == normalized
                or alias in normalized
                for aliases in self._COLUMN_ALIASES.values()
                for alias in aliases
            ):
                recognized += 1

        return recognized / len(row)

    def _infer_columns(
        self,
        headers: Sequence[str],
    ) -> list[_ColumnCandidate]:
        columns: list[_ColumnCandidate] = []

        for index, header in enumerate(headers):
            key, confidence = self._classify_header(header)

            if key is None:
                key = f"attribute_{index + 1}"
                confidence = 0.35

            columns.append(
                _ColumnCandidate(
                    key=key,
                    label=header.strip(),
                    index=index,
                    confidence=confidence,
                    evidence=(f"header:{header.strip()}",),
                )
            )

        return columns

    def _classify_header(
        self,
        header: str,
    ) -> tuple[str | None, float]:
        normalized = self._normalize_label(header)

        if not normalized:
            return None, 0.0

        exact_matches: list[str] = []

        for key, aliases in self._COLUMN_ALIASES.items():
            if normalized in aliases:
                exact_matches.append(key)

        if len(exact_matches) == 1:
            return exact_matches[0], 1.0

        for key, aliases in self._COLUMN_ALIASES.items():
            for alias in aliases:
                if alias in normalized or normalized in alias:
                    return key, 0.82

        return None, 0.0

    @staticmethod
    def _normalize_label(value: str) -> str:
        return (
            value.strip()
            .lower()
            .replace(".", "")
            .replace(":", "")
            .replace("_", " ")
            .replace("-", " ")
        )

    def _build_rows(
        self,
        data_rows: Iterable[Sequence[str]],
        columns: Sequence[_ColumnCandidate],
    ) -> list[dict[str, Any]]:
        semantic_rows: list[dict[str, Any]] = []

        width = len(columns)

        for raw_row in data_rows:
            values = list(raw_row)

            if not any(value.strip() for value in values):
                continue

            if len(values) < width:
                values.extend([""] * (width - len(values)))

            if len(values) > width:
                values = values[:width]

            row: dict[str, Any] = {}

            for column, value in zip(columns, values):
                row[column.key] = value.strip()

            if any(str(value).strip() for value in row.values()):
                semantic_rows.append(row)

        return semantic_rows

    @staticmethod
    def _calculate_confidence(
        columns: Sequence[_ColumnCandidate],
        rows: Sequence[dict[str, Any]],
    ) -> float:
        if not columns:
            return 0.0

        column_confidence = sum(
            column.confidence
            for column in columns
        ) / len(columns)

        row_confidence = (
            1.0
            if rows
            else 0.0
        )

        return round(
            (column_confidence * 0.75)
            + (row_confidence * 0.25),
            4,
        )