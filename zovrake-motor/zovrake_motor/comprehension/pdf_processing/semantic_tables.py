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


@dataclass(frozen=True)
class _LayoutHeaderCandidate:
    """Candidato de encabezado localizado dentro del layout de una página."""

    matches: tuple[_HeaderMatch, ...]
    start_line_index: int
    end_line_index: int
    score: float

    @property
    def header_y(self) -> float:
        return max(
            word.center_y
            for match in self.matches
            for word in match.words
        )

    @property
    def header_word_count(self) -> int:
        return sum(
            len(match.words)
            for match in self.matches
        )


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

        A diferencia de una implementación de una sola tabla por página,
        esta ruta localiza todos los encabezados semánticamente plausibles,
        separa sus regiones verticales y construye una tabla independiente
        para cada región con evidencia suficiente.

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

        headers = self._find_layout_headers(lines)

        if not headers:
            return []

        semantic_tables: list[PdfSemanticTable] = []

        for table_index, header_candidate in enumerate(
            headers,
            start=1,
        ):
            columns = self._infer_layout_columns(
                header_candidate.matches
            )

            if len(columns) < self._MIN_HEADER_MATCHES:
                continue

            next_header_y = (
                headers[table_index].header_y
                if table_index < len(headers)
                else None
            )

            data_lines = self._collect_data_lines(
                lines=lines,
                header_y=header_candidate.header_y,
                columns=columns,
                page_height=page_height,
                end_y=next_header_y,
            )

            if not data_lines:
                continue

            rows = self._assign_layout_lines_to_columns(
                data_lines=data_lines,
                columns=columns,
            )

            rows = self._normalize_semantic_rows(rows)

            if not rows:
                continue

            bbox = self._calculate_layout_bbox(
                header=header_candidate.matches,
                data_lines=data_lines,
            )

            confidence = self._calculate_layout_confidence(
                columns=columns,
                rows=rows,
                page_width=page_width,
                page_height=page_height,
                header_word_count=header_candidate.header_word_count,
                matched_header_word_count=header_candidate.header_word_count,
            )

            semantic_tables.append(
                PdfSemanticTable(
                    table_id=(
                        f"page-{page_number}-"
                        f"semantic-table-{len(semantic_tables) + 1}"
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
                        f"header_line_start:{header_candidate.start_line_index}",
                        f"header_line_end:{header_candidate.end_line_index}",
                        f"bbox:{bbox}",
                    ),
                )
            )

        return semantic_tables

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

    def _find_layout_headers(
        self,
        lines: Sequence[Sequence[_LayoutWord]],
    ) -> list[_LayoutHeaderCandidate]:
        """
        Encuentra múltiples encabezados semánticos independientes.

        Se consideran tanto líneas individuales como encabezados
        fragmentados en dos líneas próximas. Los candidatos solapados
        representan normalmente la misma cabecera y se reducen al de
        mayor puntuación.
        """
        # Para soportar varias tablas distribuidas a lo largo de una
        # página, la búsqueda de encabezados no se limita a las primeras
        # líneas. El límite histórico se mantiene para _find_layout_header,
        # que conserva su comportamiento original.
        search_lines = list(lines)

        candidates: list[_LayoutHeaderCandidate] = []

        for index, line in enumerate(search_lines):
            if not line:
                continue

            matches = self._match_header_line(line)

            if len(matches) >= self._MIN_HEADER_MATCHES:
                candidates.append(
                    _LayoutHeaderCandidate(
                        matches=tuple(matches),
                        start_line_index=index,
                        end_line_index=index,
                        score=self._score_layout_header(matches),
                    )
                )

            if index + 1 >= len(search_lines):
                continue

            next_line = search_lines[index + 1]

            if not next_line:
                continue

            first_y = (
                sum(word.center_y for word in line)
                / len(line)
            )
            second_y = (
                sum(word.center_y for word in next_line)
                / len(next_line)
            )

            if (
                abs(second_y - first_y)
                > self._HEADER_MERGE_Y_TOLERANCE
            ):
                continue

            merged = tuple(line) + tuple(next_line)
            merged_matches = self._match_header_line(merged)

            if len(merged_matches) < self._MIN_HEADER_MATCHES:
                continue

            candidates.append(
                _LayoutHeaderCandidate(
                    matches=tuple(merged_matches),
                    start_line_index=index,
                    end_line_index=index + 1,
                    score=self._score_layout_header(
                        merged_matches
                    ),
                )
            )

        if not candidates:
            return []

        candidates.sort(
            key=lambda candidate: (
                candidate.start_line_index,
                -candidate.score,
            )
        )

        selected: list[_LayoutHeaderCandidate] = []

        for candidate in candidates:
            overlapping = [
                existing
                for existing in selected
                if not (
                    candidate.start_line_index
                    > existing.end_line_index
                    or candidate.end_line_index
                    < existing.start_line_index
                )
            ]

            if not overlapping:
                selected.append(candidate)
                continue

            best = max(
                [candidate, *overlapping],
                key=lambda item: item.score,
            )

            selected = [
                existing
                for existing in selected
                if existing not in overlapping
            ]
            selected.append(best)

        selected.sort(
            key=lambda candidate: candidate.start_line_index
        )

        return selected

    @staticmethod
    def _score_layout_header(
        matches: Sequence[_HeaderMatch],
    ) -> float:
        if not matches:
            return 0.0

        distinct_keys = len(
            {match.key for match in matches}
        )

        x_span = (
            max(match.x_center for match in matches)
            - min(match.x_center for match in matches)
        )

        return (
            len(matches) * 2.0
            + distinct_keys * 1.5
            + min(x_span / 100.0, 5.0)
            + sum(match.confidence for match in matches)
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
        """
        Identifica encabezados incluso cuando el PDF los entrega
        fragmentados en varios objetos de texto.

        Ejemplos:
        - ``U.MEDIDA`` -> unit
        - ``P.`` + ``UNIT.`` -> unit_price
        - ``TOTAL`` + ``Bs.`` -> total

        La posición de cada fragmento se conserva para que la etapa
        posterior pueda reconstruir las columnas mediante geometría.
        """
        if not words:
            return []

        normalized_words = [
            self._normalize_label(word.text)
            for word in words
        ]

        aliases: list[tuple[str, str]] = []

        for key, values in self._COLUMN_ALIASES.items():
            for alias in values:
                aliases.append(
                    (
                        key,
                        self._normalize_label(alias),
                    )
                )

        aliases.extend(
            (
                ("unit", "u medida"),
                ("unit_price", "p unit"),
                ("unit_price", "p unitario"),
                ("unit_price", "precio unitario"),
                ("total", "total bs"),
                ("total", "total bs."),
            )
        )

        aliases = list(dict.fromkeys(aliases))

        index = 0
        matches: list[_HeaderMatch] = []

        while index < len(words):
            current = normalized_words[index]

            exact_candidates = [
                item
                for item in aliases
                if item[1] == current
            ]

            if exact_candidates:
                key, _ = max(
                    exact_candidates,
                    key=lambda item: len(item[1]),
                )

                matches.append(
                    _HeaderMatch(
                        key=key,
                        label=words[index].text,
                        words=(words[index],),
                        confidence=1.0,
                    )
                )

                index += 1
                continue

            best_match: tuple[str, str, int] | None = None

            for key, alias in aliases:
                tokens = alias.split()

                if len(tokens) <= 1:
                    continue

                end = index + len(tokens)

                if (
                    end <= len(words)
                    and normalized_words[index:end] == tokens
                ):
                    if (
                        best_match is None
                        or len(tokens)
                        > len(best_match[1].split())
                    ):
                        best_match = (
                            key,
                            alias,
                            end,
                        )

            if best_match is None:
                index += 1
                continue

            key, alias, end = best_match
            matched_words = tuple(words[index:end])

            matches.append(
                _HeaderMatch(
                    key=key,
                    label=" ".join(
                        word.text
                        for word in matched_words
                    ),
                    words=matched_words,
                    confidence=1.0,
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
        end_y: float | None = None,
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
                end_y is not None
                and line_y >= end_y - self._LINE_Y_TOLERANCE
            ):
                break

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
        """
        Asigna una palabra a una columna utilizando primero evidencia
        semántica y después geometría.

        La geometría se interpreta como intervalos entre centros de
        columnas. Las columnas de descripción reciben un intervalo
        amplio porque su contenido normalmente ocupa mucho más espacio
        que su encabezado.
        """
        if not columns:
            return None

        ordered = sorted(
            (
                column
                for column in columns
                if column.x_center is not None
            ),
            key=lambda column: column.x_center or 0.0,
        )

        if not ordered:
            return None

        x = word.center_x

        column_keys = {column.key for column in ordered}

        if "unit" in column_keys and self._looks_like_unit(word.text):
            unit_column = next(
                column for column in ordered if column.key == "unit"
            )
            if abs(x - (unit_column.x_center or 0.0)) <= 110.0:
                return unit_column

        if "code" in column_keys and self._looks_like_code(word.text):
            code_column = next(
                column for column in ordered if column.key == "code"
            )
            if abs(x - (code_column.x_center or 0.0)) <= 120.0:
                return code_column

        if self._looks_currency(word.text):
            price_columns = [
                column
                for column in ordered
                if column.key in {"unit_price", "total"}
            ]
            if price_columns:
                return min(
                    price_columns,
                    key=lambda column: abs(
                        x - (column.x_center or 0.0)
                    ),
                )

        description = next(
            (
                column
                for column in ordered
                if column.key == "description"
            ),
            None,
        )

        if description is not None and self._looks_numeric(word.text):
            description_index = ordered.index(description)

            left_boundary = float("-inf")
            right_boundary = float("inf")

            if description_index > 0:
                previous_center = ordered[description_index - 1].x_center
                if previous_center is not None:
                    left_boundary = previous_center + 12.0

            if description_index < len(ordered) - 1:
                next_center = ordered[description_index + 1].x_center
                if next_center is not None:
                    right_boundary = next_center - 12.0

            if left_boundary <= x <= right_boundary:
                return description

        if self._looks_numeric(word.text):
            numeric_columns = [
                column
                for column in ordered
                if column.key in {
                    "quantity",
                    "unit_price",
                    "total",
                }
            ]
            if numeric_columns:
                return min(
                    numeric_columns,
                    key=lambda column: abs(
                        x - (column.x_center or 0.0)
                    ),
                )

        if description is not None:
            description_index = ordered.index(description)

            left_boundary = float("-inf")
            right_boundary = float("inf")

            if description_index > 0:
                previous_center = ordered[description_index - 1].x_center
                if previous_center is not None:
                    left_boundary = previous_center + 12.0

            if description_index < len(ordered) - 1:
                next_center = ordered[description_index + 1].x_center
                if next_center is not None:
                    right_boundary = next_center - 12.0

            if left_boundary <= x <= right_boundary:
                return description

        return min(
            ordered,
            key=lambda column: abs(
                x - (column.x_center or 0.0)
            ),
        )

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
        header_word_count: int,
        matched_header_word_count: int,
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

        header_coverage = (
            matched_header_word_count / header_word_count
            if header_word_count > 0
            else 0.0
        )

        geometry_confidence = (
            1.0
            if page_width > 0 and page_height > 0
            else 0.7
        )

        return round(
            min(
                1.0,
                header_confidence * 0.45
                + min(populated_ratio, 1.0) * 0.25
                + min(header_coverage, 1.0) * 0.20
                + geometry_confidence * 0.10,
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