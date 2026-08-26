from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Iterable, Sequence

from .models import (
    PdfSemanticTable,
    PdfTable,
    PdfTableColumn,
    PdfTextBlock,
)


@dataclass(frozen=True)
class _ColumnCandidate:
    key: str
    label: str
    index: int
    confidence: float
    x_center: float | None = None
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True)
class _LayoutWord:
    text: str
    x0: float
    x1: float
    top: float
    bottom: float

    @property
    def center_x(self) -> float:
        return (self.x0 + self.x1) / 2.0

    @property
    def center_y(self) -> float:
        return (self.top + self.bottom) / 2.0


@dataclass(frozen=True)
class _HeaderMatch:
    key: str
    label: str
    words: tuple[_LayoutWord, ...]
    confidence: float

    @property
    def x_center(self) -> float:
        if not self.words:
            return 0.0

        return sum(
            word.center_x
            for word in self.words
        ) / len(self.words)


class PdfSemanticTableAnalyzer:
    """
    Analizador semántico de tablas PDF.

    Convierte una representación física de una tabla en una
    representación semántica sin imponer una estructura fija
    de cotización.

    La semántica se determina a partir de:
    - etiquetas;
    - contenido real;
    - posición de los elementos;
    - estructura de filas;
    - evidencia disponible en el documento.
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

    _HEADER_SEARCH_LIMIT = 60
    _LINE_Y_TOLERANCE = 3.0
    _HEADER_MERGE_Y_TOLERANCE = 8.0
    _MIN_HEADER_MATCHES = 2

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
                "source:physical_table",
            ),
        )

    def analyze_page(
        self,
        *,
        page_number: int,
        text_blocks: Sequence[PdfTextBlock],
        page_width: float,
        page_height: float,
    ) -> list[PdfSemanticTable]:
        """
        Analiza una página utilizando palabras y coordenadas.

        Esta ruta complementa el análisis de tablas físicas y permite
        reconstruir una tabla a partir del layout textual de la página.

        Utiliza:
        - posición horizontal;
        - posición vertical;
        - encabezados;
        - contenido;
        - tipos de valores;
        - unidades;
        - códigos;
        - precios;
        - descripciones.
        """
        words = self._layout_words(text_blocks)

        if len(words) < self._MIN_HEADER_MATCHES:
            return []

        lines = self._group_words_into_lines(words)

        if not lines:
            return []

        header = self._find_layout_header(lines)

        if header is None:
            return []

        columns = self._infer_layout_columns(header)

        if len(columns) < self._MIN_HEADER_MATCHES:
            return []

        header_y = max(
            word.center_y
            for match in header
            for word in match.words
        )

        data_lines = self._collect_data_lines(
            lines=lines,
            header_y=header_y,
            columns=columns,
            page_height=page_height,
        )

        if not data_lines:
            return []

        rows = self._assign_layout_lines_to_columns(
            data_lines=data_lines,
            columns=columns,
        )

        rows = self._normalize_semantic_rows(rows)

        if not rows:
            return []

        bbox = self._calculate_layout_bbox(
            header=header,
            data_lines=data_lines,
        )

        confidence = self._calculate_layout_confidence(
            columns=columns,
            rows=rows,
            page_width=page_width,
            page_height=page_height,
        )

        semantic_table = PdfSemanticTable(
            table_id=(
                f"page-{page_number}-"
                "semantic-table-1"
            ),
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
            rows=tuple(rows),
            confidence=confidence,
            source_table_id="",
            source_page_number=page_number,
            evidence=(
                f"page:{page_number}",
                "source:layout_words",
                f"header_columns:{len(columns)}",
                f"bbox:{bbox}",
            ),
        )

        return [semantic_table]

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

        for index, row in enumerate(
            rows[: self._HEADER_SEARCH_LIMIT]
        ):
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
        used_keys: set[str] = set()

        for index, header in enumerate(headers):
            key, confidence = self._classify_header(header)

            if key is None:
                key = f"attribute_{index + 1}"
                confidence = 0.35

            if key in used_keys:
                key = f"{key}_{index + 1}"

            used_keys.add(key)

            columns.append(
                _ColumnCandidate(
                    key=key,
                    label=header.strip(),
                    index=index,
                    confidence=confidence,
                    evidence=(
                        f"header:{header.strip()}",
                        "source:physical_table",
                    ),
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
            normalized_aliases = {
                self._normalize_label(alias)
                for alias in aliases
            }

            if normalized in normalized_aliases:
                exact_matches.append(key)

        if len(exact_matches) == 1:
            return exact_matches[0], 1.0

        for key, aliases in self._COLUMN_ALIASES.items():
            for alias in aliases:
                normalized_alias = self._normalize_label(alias)

                if (
                    normalized_alias in normalized
                    or normalized in normalized_alias
                ):
                    return key, 0.82

        return None, 0.0

    @staticmethod
    def _normalize_label(
        value: str,
    ) -> str:
        normalized = unicodedata.normalize(
            "NFKD",
            value.strip().lower(),
        )

        normalized = "".join(
            char
            for char in normalized
            if not unicodedata.combining(char)
        )

        normalized = normalized.replace("/", " ")
        normalized = normalized.replace(".", " ")
        normalized = normalized.replace(":", " ")
        normalized = normalized.replace("_", " ")
        normalized = normalized.replace("-", " ")

        normalized = re.sub(
            r"\s+",
            " ",
            normalized,
        )

        return normalized.strip()

    def _build_rows(
        self,
        data_rows: Iterable[Sequence[str]],
        columns: Sequence[_ColumnCandidate],
    ) -> list[dict[str, Any]]:
        """
        Construye filas semánticas sin descartar información adicional.

        Si una fila física contiene más valores que columnas reconocidas,
        los valores sobrantes se conservan bajo claves unmapped_N.
        """
        semantic_rows: list[dict[str, Any]] = []

        width = len(columns)

        for raw_row in data_rows:
            values = [
                str(value).strip()
                for value in raw_row
            ]

            if not any(values):
                continue

            row: dict[str, Any] = {}

            for index, value in enumerate(values):
                if index < width:
                    key = columns[index].key
                else:
                    key = f"unmapped_{index + 1}"

                row[key] = value

            if any(
                str(value).strip()
                for value in row.values()
            ):
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

    def _find_layout_header(
        self,
        lines: Sequence[Sequence[_LayoutWord]],
    ) -> tuple[_HeaderMatch, ...] | None:
        best: tuple[_HeaderMatch, ...] | None = None
        best_score = -1.0

        search_lines = list(
            lines[: self._HEADER_SEARCH_LIMIT]
        )

        candidates: list[
            Sequence[_LayoutWord]
        ] = list(search_lines)

        for index in range(
            len(search_lines) - 1
        ):
            first = search_lines[index]
            second = search_lines[index + 1]

            if not first or not second:
                continue

            first_y = (
                sum(
                    word.center_y
                    for word in first
                )
                / len(first)
            )

            second_y = (
                sum(
                    word.center_y
                    for word in second
                )
                / len(second)
            )

            if (
                abs(second_y - first_y)
                <= self._HEADER_MERGE_Y_TOLERANCE
            ):
                candidates.append(
                    tuple(first)
                    + tuple(second)
                )

        for line in candidates:
            matches = self._match_header_line(line)

            if len(matches) < self._MIN_HEADER_MATCHES:
                continue

            distinct_keys = len(
                {match.key for match in matches}
            )

            x_span = (
                max(
                    match.x_center
                    for match in matches
                )
                - min(
                    match.x_center
                    for match in matches
                )
            )

            score = (
                len(matches) * 2.0
                + distinct_keys * 1.5
                + min(
                    x_span / 100.0,
                    5.0,
                )
                + sum(
                    match.confidence
                    for match in matches
                )
            )

            if score > best_score:
                best_score = score
                best = tuple(matches)

        return best

    def _match_header_line(
        self,
        words: Sequence[_LayoutWord],
    ) -> list[_HeaderMatch]:
        matches: list[_HeaderMatch] = []

        if not words:
            return matches

        normalized_words = [
            self._normalize_label(word.text)
            for word in words
        ]

        aliases = [
            (key, alias)
            for key, values in self._COLUMN_ALIASES.items()
            for alias in values
        ]

        single_word_aliases = [
            item
            for item in aliases
            if len(
                self._normalize_label(
                    item[1]
                ).split()
            ) == 1
        ]

        multi_word_aliases = [
            item
            for item in aliases
            if len(
                self._normalize_label(
                    item[1]
                ).split()
            ) > 1
        ]

        aliases = (
            single_word_aliases
            + sorted(
                multi_word_aliases,
                key=lambda item: len(
                    self._normalize_label(
                        item[1]
                    ).split()
                ),
                reverse=True,
            )
        )

        index = 0

        while index < len(words):
            best_match: (
                tuple[str, str, int, float] | None
            ) = None

            current = normalized_words[index]

            for key, alias in aliases:
                normalized_alias = self._normalize_label(alias)
                alias_tokens = normalized_alias.split()

                if len(alias_tokens) == 1:
                    if current == normalized_alias:
                        best_match = (
                            key,
                            alias,
                            index + 1,
                            1.0,
                        )
                        break

                    continue

                end = index + len(alias_tokens)

                if (
                    end <= len(words)
                    and normalized_words[index:end]
                    == alias_tokens
                ):
                    best_match = (
                        key,
                        alias,
                        end,
                        1.0,
                    )
                    break

            if best_match is None:
                index += 1
                continue

            key, alias, end, confidence = best_match

            matched_words = tuple(
                words[index:end]
            )

            label = " ".join(
                word.text
                for word in matched_words
            )

            matches.append(
                _HeaderMatch(
                    key=key,
                    label=label,
                    words=matched_words,
                    confidence=confidence,
                )
            )

            index = end

        return self._deduplicate_header_matches(matches)

    @staticmethod
    def _deduplicate_header_matches(
        matches: Sequence[_HeaderMatch],
    ) -> list[_HeaderMatch]:
        result: list[_HeaderMatch] = []
        used_keys: set[str] = set()

        for match in sorted(
            matches,
            key=lambda item: item.x_center,
        ):
            if match.key in used_keys:
                continue

            result.append(match)
            used_keys.add(match.key)

        return result

    def _infer_layout_columns(
        self,
        header: Sequence[_HeaderMatch],
    ) -> list[_ColumnCandidate]:
        columns: list[_ColumnCandidate] = []

        ordered_header = sorted(
            header,
            key=lambda item: item.x_center,
        )

        for index, match in enumerate(
            ordered_header
        ):
            columns.append(
                _ColumnCandidate(
                    key=match.key,
                    label=match.label,
                    index=index,
                    confidence=match.confidence,
                    x_center=match.x_center,
                    evidence=(
                        f"header:{match.label}",
                        (
                            f"x_center:"
                            f"{match.x_center:.2f}"
                        ),
                        "source:layout_words",
                    ),
                )
            )

        return columns

    def _collect_data_lines(
        self,
        *,
        lines: Sequence[Sequence[_LayoutWord]],
        header_y: float,
        columns: Sequence[_ColumnCandidate],
        page_height: float,
    ) -> list[Sequence[_LayoutWord]]:
        if not columns:
            return []

        centers = [
            column.x_center
            for column in columns
            if column.x_center is not None
        ]

        if not centers:
            return []

        min_x = min(centers)
        max_x = max(centers)

        data_lines: list[
            Sequence[_LayoutWord]
        ] = []

        started = False

        for line in lines:
            if not line:
                continue

            line_y = (
                sum(
                    word.center_y
                    for word in line
                )
                / len(line)
            )

            if (
                line_y
                <= header_y
                + self._LINE_Y_TOLERANCE
            ):
                continue

            if (
                page_height
                and line_y > page_height * 0.92
            ):
                break

            text = " ".join(
                word.text
                for word in line
            ).strip()

            if not text:
                continue

            if self._looks_like_summary_or_footer(text):
                if started:
                    break

                continue

            line_min_x = min(
                word.x0
                for word in line
            )

            line_max_x = max(
                word.x1
                for word in line
            )

            if (
                line_max_x < min_x - 80
                or line_min_x > max_x + 150
            ):
                if started:
                    break

                continue

            evidence_score = self._line_data_evidence(
                line=line,
                columns=columns,
            )

            if evidence_score >= 2:
                data_lines.append(line)
                started = True

            elif started and evidence_score >= 1:
                data_lines.append(line)

            elif started:
                break

        return data_lines

    def _assign_layout_lines_to_columns(
        self,
        *,
        data_lines: Sequence[Sequence[_LayoutWord]],
        columns: Sequence[_ColumnCandidate],
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []

        for line in data_lines:
            row: dict[str, list[str]] = {
                column.key: []
                for column in columns
            }

            for word in line:
                column = self._best_column_for_word(
                    word=word,
                    columns=columns,
                )

                if column is None:
                    continue

                row[column.key].append(
                    word.text
                )

            normalized_row = {
                key: " ".join(values).strip()
                for key, values in row.items()
            }

            if self._is_valid_data_row(normalized_row):
                rows.append(normalized_row)

        return rows

    def _best_column_for_word(
        self,
        *,
        word: _LayoutWord,
        columns: Sequence[_ColumnCandidate],
    ) -> _ColumnCandidate | None:
        if not columns:
            return None

        centers = [
            column.x_center
            for column in columns
            if column.x_center is not None
        ]

        if not centers:
            return None

        min_center = min(centers)
        max_center = max(centers)

        span = max(
            max_center - min_center,
            1.0,
        )

        best_column: _ColumnCandidate | None = None
        best_score = float("-inf")

        for index, column in enumerate(columns):
            center = column.x_center

            if center is None:
                continue

            distance = (
                abs(word.center_x - center)
                / span
            )

            score = -distance
            key = column.key

            if key == "description":
                next_center = (
                    columns[index + 1].x_center
                    if index + 1 < len(columns)
                    else None
                )

                previous_center = (
                    columns[index - 1].x_center
                    if index > 0
                    else None
                )

                if next_center is not None:
                    if (
                        word.center_x
                        < (
                            center + next_center
                        ) / 2
                    ):
                        score += 1.5

                if previous_center is not None:
                    if (
                        word.center_x
                        > (
                            previous_center + center
                        ) / 2
                    ):
                        score += 1.5

                if re.search(
                    r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]",
                    word.text,
                ):
                    score += 1.5

            if (
                key == "quantity"
                and self._looks_numeric(word.text)
                and abs(
                    word.center_x - center
                ) <= 90.0
            ):
                score += 2.5

            elif (
                key == "unit"
                and self._looks_like_unit(word.text)
                and abs(
                    word.center_x - center
                ) <= 100.0
            ):
                score += 3.0

            elif (
                key == "code"
                and self._looks_like_code(word.text)
                and abs(
                    word.center_x - center
                ) <= 110.0
            ):
                score += 3.5

            elif (
                key in {
                    "unit_price",
                    "total",
                }
                and (
                    self._looks_currency(word.text)
                    or self._looks_numeric(word.text)
                )
                and abs(
                    word.center_x - center
                ) <= 110.0
            ):
                score += 2.5

            if score > best_score:
                best_score = score
                best_column = column

        return best_column

    @staticmethod
    def _looks_numeric(
        value: str,
    ) -> bool:
        normalized = (
            value
            .strip()
            .replace(",", "")
            .replace("$", "")
            .replace("€", "")
            .replace("S/", "")
            .replace("Bs.", "")
            .replace("Bs", "")
        )

        if not normalized:
            return False

        return bool(
            re.fullmatch(
                r"-?\d+(?:\.\d+)?",
                normalized,
            )
        )

    @staticmethod
    def _looks_currency(
        value: str,
    ) -> bool:
        normalized = value.strip()

        if not normalized:
            return False

        if any(
            symbol in normalized
            for symbol in (
                "$",
                "S/",
                "Bs",
                "€",
                "£",
            )
        ):
            return True

        return bool(
            re.fullmatch(
                r"-?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})",
                normalized,
            )
        )

    @staticmethod
    def _looks_like_unit(
        value: str,
    ) -> bool:
        normalized = (
            PdfSemanticTableAnalyzer
            ._normalize_label(value)
        )

        return normalized in {
            "unidad",
            "und",
            "u",
            "mt2",
            "m2",
            "m3",
            "kg",
            "g",
            "ml",
            "lt",
            "l",
            "cm",
            "mm",
            "pza",
            "pieza",
            "rollo",
            "metro",
            "metros",
            "unidades",
        }

    @staticmethod
    def _looks_like_code(
        value: str,
    ) -> bool:
        normalized = value.strip()

        if not normalized:
            return False

        if normalized.isdigit():
            return len(normalized) >= 6

        return bool(
            re.fullmatch(
                r"[A-Za-z]*\d+[A-Za-z0-9_-]*",
                normalized,
            )
        )

    @staticmethod
    def _looks_like_summary_or_footer(
        text: str,
    ) -> bool:
        normalized = (
            PdfSemanticTableAnalyzer
            ._normalize_label(text)
        )

        return normalized.startswith(
            (
                "sub total",
                "subtotal",
                "total a pagar",
                "igv",
                "iva",
                "son ",
                "forma de pago",
                "tiempo de culminacion",
                "terminos y condiciones",
            )
        )

    @staticmethod
    def _is_valid_data_row(
        row: dict[str, Any],
    ) -> bool:
        values = [
            str(value).strip()
            for value in row.values()
        ]

        return (
            sum(
                bool(value)
                for value in values
            )
            >= 2
        )

    def _normalize_semantic_rows(
        self,
        rows: Sequence[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        normalized_rows: list[
            dict[str, Any]
        ] = []

        for row in rows:
            normalized: dict[str, Any] = {}

            for key, value in row.items():
                if value is None:
                    normalized[key] = ""
                else:
                    normalized[key] = str(
                        value
                    ).strip()

            if any(
                str(value).strip()
                for value in normalized.values()
            ):
                normalized_rows.append(
                    normalized
                )

        return normalized_rows

    @staticmethod
    def _calculate_layout_bbox(
        *,
        header: Sequence[_HeaderMatch],
        data_lines: Sequence[Sequence[_LayoutWord]],
    ) -> tuple[float, float, float, float]:
        words = [
            word
            for match in header
            for word in match.words
        ]

        words.extend(
            word
            for line in data_lines
            for word in line
        )

        if not words:
            return (
                0.0,
                0.0,
                0.0,
                0.0,
            )

        return (
            min(word.x0 for word in words),
            min(word.top for word in words),
            max(word.x1 for word in words),
            max(word.bottom for word in words),
        )

    @staticmethod
    def _calculate_layout_confidence(
        *,
        columns: Sequence[_ColumnCandidate],
        rows: Sequence[dict[str, Any]],
        page_width: float,
        page_height: float,
    ) -> float:
        if not columns or not rows:
            return 0.0

        header_confidence = (
            sum(
                column.confidence
                for column in columns
            )
            / len(columns)
        )

        populated_ratio = (
            sum(
                sum(
                    bool(str(value).strip())
                    for value in row.values()
                )
                / len(columns)
                for row in rows
            )
            / len(rows)
        )

        geometry_confidence = (
            1.0
            if page_width > 0
            and page_height > 0
            else 0.7
        )

        return round(
            min(
                1.0,
                header_confidence * 0.55
                + min(
                    populated_ratio,
                    1.0,
                ) * 0.30
                + geometry_confidence * 0.15,
            ),
            4,
        )

    @staticmethod
    def _layout_words(
        text_blocks: Sequence[PdfTextBlock],
    ) -> list[_LayoutWord]:
        result: list[_LayoutWord] = []

        for block in text_blocks:
            if not block.bbox:
                continue

            x0, top, x1, bottom = block.bbox

            text = block.text.strip()

            if not text:
                continue

            result.append(
                _LayoutWord(
                    text=text,
                    x0=float(x0),
                    x1=float(x1),
                    top=float(top),
                    bottom=float(bottom),
                )
            )

        return sorted(
            result,
            key=lambda word: (
                word.top,
                word.x0,
            ),
        )

    def _group_words_into_lines(
        self,
        words: Sequence[_LayoutWord],
    ) -> list[list[_LayoutWord]]:
        lines: list[list[_LayoutWord]] = []

        for word in words:
            placed = False

            for line in reversed(lines[-3:]):
                if not line:
                    continue

                line_y = (
                    sum(
                        item.center_y
                        for item in line
                    )
                    / len(line)
                )

                if (
                    abs(
                        word.center_y - line_y
                    )
                    <= self._LINE_Y_TOLERANCE
                ):
                    line.append(word)
                    placed = True
                    break

            if not placed:
                lines.append([word])

        for line in lines:
            line.sort(
                key=lambda item: item.x0
            )

        return lines

    def _line_data_evidence(
        self,
        *,
        line: Sequence[_LayoutWord],
        columns: Sequence[_ColumnCandidate],
    ) -> int:
        text = " ".join(
            word.text
            for word in line
        )

        score = 0

        if any(
            self._looks_numeric(word.text)
            for word in line
        ):
            score += 1

        if any(
            self._looks_like_unit(word.text)
            for word in line
        ):
            score += 1

        if any(
            self._looks_currency(word.text)
            for word in line
        ):
            score += 1

        if any(
            self._looks_like_code(word.text)
            for word in line
        ):
            score += 1

        if len(text.split()) >= 2:
            score += 1

        if any(
            column.key == "description"
            for column in columns
        ) and re.search(
            r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]",
            text,
        ):
            score += 1

        return score