"""Procesador documental profundo para archivos PDF."""

from __future__ import annotations

from dataclasses import replace
from io import BytesIO
from typing import Any

import pdfplumber
from pypdf import PdfReader

from zovrake_motor.comprehension.pdf_processing.exceptions import (
    PdfExtractionError,
    PdfInvalidDocumentError,
)
from zovrake_motor.comprehension.pdf_processing.models import (
    PdfImage,
    PdfOcrBlock,
    PdfPageAnalysis,
    PdfSemanticTable,
    PdfTable,
    PdfTextBlock,
    ProcessedPdfDocument,
)
from zovrake_motor.comprehension.pdf_processing.semantic_tables import (
    PdfSemanticTableAnalyzer,
)
from zovrake_motor.comprehension.pdf_processing.ocr import OcrProcessor


class PDFDocumentProcessor:
    """
    Procesa físicamente un PDF y construye una representación documental
    estructurada para las siguientes etapas de comprensión.

    Esta clase realiza extracción física del PDF y OCR selectivo
    para las páginas que lo requieren.

    No realiza:
    - clasificación de materiales;
    - comparación de proveedores;
    - selección de ganador;
    - análisis inteligente.

    Su responsabilidad es construir la representación documental
    física y enriquecerla con OCR cuando es necesario.
    """

    OCR_TEXT_THRESHOLD = 20

    def __init__(
        self,
        *,
        ocr_processor: OcrProcessor | None = None,
        ocr_visual_pages: bool = False,
    ) -> None:
        self._ocr_processor = ocr_processor or OcrProcessor()
        self._ocr_visual_pages = bool(ocr_visual_pages)

    def process(
        self,
        *,
        document_id: str,
        file_name: str,
        pdf_bytes: bytes,
    ) -> ProcessedPdfDocument:
        if not pdf_bytes:
            raise PdfInvalidDocumentError(
                "El documento PDF no contiene datos."
            )

        reader = self._open_reader(pdf_bytes)

        try:
            with pdfplumber.open(BytesIO(pdf_bytes)) as plumber_pdf:
                return self._process_document(
                    document_id=document_id,
                    file_name=file_name,
                    pdf_bytes=pdf_bytes,
                    reader=reader,
                    plumber_pdf=plumber_pdf,
                )
        except PdfInvalidDocumentError:
            raise
        except Exception as exc:
            raise PdfExtractionError(
                f"No fue posible procesar el PDF '{file_name}': {exc}"
            ) from exc

    @staticmethod
    def _open_reader(pdf_bytes: bytes) -> PdfReader:
        try:
            return PdfReader(BytesIO(pdf_bytes))
        except Exception as exc:
            raise PdfInvalidDocumentError(
                f"El archivo no pudo abrirse como PDF: {exc}"
            ) from exc

    def _process_document(
        self,
        *,
        document_id: str,
        file_name: str,
        pdf_bytes: bytes,
        reader: PdfReader,
        plumber_pdf: pdfplumber.PDF,
    ) -> ProcessedPdfDocument:
        pages: list[PdfPageAnalysis] = []
        all_tables: list[PdfTable] = []
        all_semantic_tables: list[PdfSemanticTable] = []
        all_images: list[PdfImage] = []
        full_text_parts: list[str] = []
        document_warnings: list[str] = []
        document_errors: list[str] = []

        page_count = len(reader.pages)

        if page_count == 0:
            return ProcessedPdfDocument(
                document_id=document_id,
                file_name=file_name,
                page_count=0,
                pages=(),
                full_text="",
                tables=(),
                semantic_tables=(),
                images=(),
                errors=("El PDF no contiene páginas.",),
            )

        for index in range(page_count):
            page_number = index + 1

            try:
                page_result = self._process_page(
                    page_number=page_number,
                    reader_page=reader.pages[index],
                    plumber_page=plumber_pdf.pages[index],
                    pdf_bytes=pdf_bytes,
                )

                pages.append(page_result)
                all_tables.extend(page_result.tables)
                all_semantic_tables.extend(page_result.semantic_tables)
                all_images.extend(page_result.images)

                if page_result.text.strip():
                    full_text_parts.append(
                        f"[Página {page_number}]\n"
                        f"{page_result.text}"
                    )

                document_warnings.extend(page_result.warnings)

            except Exception as exc:
                error_message = (
                    f"Página {page_number}: "
                    f"no pudo analizarse completamente: {exc}"
                )

                document_errors.append(error_message)

                try:
                    page_width = float(
                        getattr(
                            plumber_pdf.pages[index],
                            "width",
                            0.0,
                        )
                        or 0.0
                    )
                except Exception:
                    page_width = 0.0

                try:
                    page_height = float(
                        getattr(
                            plumber_pdf.pages[index],
                            "height",
                            0.0,
                        )
                        or 0.0
                    )
                except Exception:
                    page_height = 0.0

                pages.append(
                    PdfPageAnalysis(
                        page_number=page_number,
                        width=page_width,
                        height=page_height,
                        text="",
                        requires_ocr=True,
                        warnings=(error_message,),
                    )
                )

        full_text = "\n\n".join(
            part
            for part in full_text_parts
            if part.strip()
        ).strip()

        ocr_required = any(
            page.requires_ocr
            for page in pages
        )

        metadata = self._extract_pdf_metadata(reader)

        ocr_pages_executed = tuple(
            page.page_number
            for page in pages
            if page.ocr_executed
        )
        ocr_executed = bool(ocr_pages_executed)
        ocr_confidences = [
            page.ocr_confidence
            for page in pages
            if page.ocr_executed and page.ocr_confidence > 0.0
        ]
        ocr_confidence = (
            sum(ocr_confidences) / len(ocr_confidences)
            if ocr_confidences
            else 0.0
        )
        ocr_languages = tuple(
            dict.fromkeys(
                page.ocr_language
                for page in pages
                if page.ocr_language
            )
        )
        ocr_language = "+".join(ocr_languages)
        ocr_dpis = tuple(
            dict.fromkeys(
                page.ocr_dpi
                for page in pages
                if page.ocr_dpi is not None
            )
        )
        ocr_dpi = ocr_dpis[0] if len(ocr_dpis) == 1 else None

        if ocr_required and not ocr_executed:
            document_warnings.append(
                "Una o más páginas requieren OCR, pero no se obtuvo "
                "ningún resultado OCR."
            )

        if document_errors:
            document_warnings.append(
                "El documento fue procesado parcialmente. "
                "Una o más páginas presentaron errores."
            )

        return ProcessedPdfDocument(
            document_id=document_id,
            file_name=file_name,
            page_count=page_count,
            pages=tuple(pages),
            full_text=full_text,
            tables=tuple(all_tables),
            semantic_tables=tuple(all_semantic_tables),
            images=tuple(all_images),
            pdf_metadata=metadata,
            ocr_required=ocr_required,
            ocr_executed=ocr_executed,
            ocr_pages_executed=ocr_pages_executed,
            ocr_confidence=round(ocr_confidence, 4),
            ocr_language=ocr_language,
            ocr_dpi=ocr_dpi,
            extraction_method=(
                "native_pdf+ocr"
                if ocr_executed
                else "native_pdf"
            ),
            warnings=tuple(
                dict.fromkeys(document_warnings)
            ),
            errors=tuple(
                dict.fromkeys(document_errors)
            ),
        )

    def _process_page(
        self,
        *,
        page_number: int,
        reader_page: Any,
        plumber_page: pdfplumber.page.Page,
        pdf_bytes: bytes,
    ) -> PdfPageAnalysis:
        warnings: list[str] = []

        width = float(
            getattr(plumber_page, "width", 0.0) or 0.0
        )

        height = float(
            getattr(plumber_page, "height", 0.0) or 0.0
        )

        text = self._extract_page_text(
            plumber_page,
            warnings,
        )

        text_blocks = self._extract_text_blocks(
            page_number,
            plumber_page,
            text,
            warnings,
        )

        tables = self._extract_tables(
            page_number,
            plumber_page,
            warnings,
        )

        tables, semantic_tables = self._analyze_page_semantics(
            page_number=page_number,
            tables=tables,
            text_blocks=text_blocks,
            page_width=width,
            page_height=height,
            warnings=warnings,
        )

        images = self._extract_images(
            page_number,
            reader_page,
            plumber_page,
            warnings,
        )

        has_text = bool(text.strip())
        has_tables = bool(tables) or bool(semantic_tables)
        has_images = bool(images)

        requires_ocr = self._requires_ocr(
            has_text=has_text,
            has_images=has_images,
            text_length=len(text.strip()),
        )

        # En cotizaciones, una página digital puede tener texto suficiente
        # para evitar OCR aunque el proveedor esté presente exclusivamente
        # dentro de una imagen/logo. Cuando la integración visual está
        # habilitada, también se procesa la capa visual y se conserva el OCR
        # como evidencia adicional sin sustituir el texto nativo.
        if self._ocr_visual_pages and has_images:
            requires_ocr = True

        ocr_executed = False
        ocr_text = ""
        ocr_blocks: tuple[PdfOcrBlock, ...] = ()
        ocr_confidence = 0.0
        ocr_language = ""
        ocr_dpi: int | None = None

        if requires_ocr:
            try:
                ocr_result = self._ocr_processor.process_page(
                    pdf_bytes=pdf_bytes,
                    page_number=page_number,
                )

                ocr_executed = True
                ocr_text = ocr_result.text
                ocr_confidence = ocr_result.confidence
                ocr_language = ocr_result.language
                ocr_dpi = ocr_result.dpi
                ocr_blocks = tuple(
                    PdfOcrBlock(
                        block_id=(
                            f"page-{page_number}-"
                            f"ocr-{index + 1}"
                        ),
                        page_number=page_number,
                        text=block.text,
                        bbox=block.bbox,
                        confidence=block.confidence,
                    )
                    for index, block in enumerate(
                        ocr_result.blocks
                    )
                )

                if ocr_text.strip():
                    text = self._merge_text(
                        native_text=text,
                        ocr_text=ocr_text,
                    )

                    ocr_layout_blocks = [
                        PdfTextBlock(
                            block_id=block.block_id,
                            page_number=block.page_number,
                            text=block.text,
                            bbox=block.bbox,
                        )
                        for block in ocr_blocks
                    ]

                    layout_blocks = self._select_layout_blocks_for_ocr(
                        native_blocks=text_blocks,
                        ocr_blocks=ocr_layout_blocks,
                        native_text=self._extract_page_text_value(text_blocks),
                        ocr_text=ocr_text,
                    )

                    # La representación de bloques expuesta por la página
                    # debe coincidir con la que se utilizó para el análisis
                    # semántico. La procedencia OCR se conserva además en
                    # ``ocr_blocks``.
                    text_blocks = layout_blocks

                    tables, semantic_tables = self._analyze_page_semantics(
                        page_number=page_number,
                        tables=tables,
                        text_blocks=layout_blocks,
                        page_width=width,
                        page_height=height,
                        warnings=warnings,
                    )

                else:
                    warnings.append(
                        f"Página {page_number}: OCR ejecutado sin texto reconocido."
                    )

            except Exception as exc:
                warnings.append(
                    f"Página {page_number}: no fue posible ejecutar OCR: {exc}"
                )

        has_text = bool(text.strip())
        has_tables = bool(tables) or bool(semantic_tables)
        has_images = bool(images)

        return PdfPageAnalysis(
            page_number=page_number,
            width=width,
            height=height,
            text=text,
            text_blocks=tuple(text_blocks),
            tables=tuple(tables),
            semantic_tables=tuple(semantic_tables),
            images=tuple(images),
            has_text=has_text,
            has_tables=has_tables,
            has_images=has_images,
            requires_ocr=requires_ocr,
            ocr_executed=ocr_executed,
            ocr_text=ocr_text,
            ocr_blocks=ocr_blocks,
            ocr_confidence=ocr_confidence,
            ocr_language=ocr_language,
            ocr_dpi=ocr_dpi,
            warnings=tuple(warnings),
        )

    @staticmethod
    def _analyze_page_semantics(
        *,
        page_number: int,
        tables: list[PdfTable],
        text_blocks: list[PdfTextBlock],
        page_width: float,
        page_height: float,
        warnings: list[str],
    ) -> tuple[list[PdfTable], list[PdfSemanticTable]]:
        """
        Construye la semántica de una página utilizando dos evidencias
        complementarias: tablas físicas y geometría textual.

        La tabla física se intenta primero porque conserva la estructura
        tabular descubierta por el extractor. El análisis de layout se
        utiliza como evidencia complementaria cuando la representación
        física es insuficiente o menos confiable.

        La semántica seleccionada se mantiene también dentro de
        ``PdfTable.semantic`` cuando existe una tabla física compatible,
        evitando crear dos representaciones independientes del mismo
        contenido.
        """
        analyzer = PdfSemanticTableAnalyzer()

        enriched_tables: list[PdfTable] = []
        physical_semantics: list[PdfSemanticTable] = []

        for table in tables:
            try:
                semantic = analyzer.analyze(table)
            except Exception as exc:
                warnings.append(
                    f"No se pudo analizar semánticamente la tabla "
                    f"'{table.table_id}' de la página {page_number}: {exc}"
                )
                semantic = None

            if semantic is not None:
                physical_semantics.append(semantic)

            enriched_tables.append(
                replace(
                    table,
                    semantic=semantic,
                )
            )

        layout_semantics: list[PdfSemanticTable] = []

        if text_blocks:
            try:
                layout_semantics = analyzer.analyze_page(
                    page_number=page_number,
                    text_blocks=tuple(text_blocks),
                    page_width=page_width,
                    page_height=page_height,
                )
            except Exception as exc:
                warnings.append(
                    f"No se pudo analizar el layout semántico "
                    f"de la página {page_number}: {exc}"
                )

        selected_semantics = PDFDocumentProcessor._select_semantic_tables(
            physical_semantics=physical_semantics,
            layout_semantics=layout_semantics,
        )

        # Si el análisis de layout supera a una tabla física existente,
        # actualizamos la tabla física con la representación semántica
        # más fuerte. Esto conserva la trazabilidad de origen.
        if selected_semantics and enriched_tables:
            enriched_tables = PDFDocumentProcessor._attach_best_semantics(
                tables=enriched_tables,
                selected_semantics=selected_semantics,
            )

            selected_semantics = (
                PDFDocumentProcessor._synchronize_selected_semantics(
                    tables=enriched_tables,
                    selected_semantics=selected_semantics,
                )
            )

        return enriched_tables, selected_semantics

    @staticmethod
    def _select_semantic_tables(
        *,
        physical_semantics: list[PdfSemanticTable],
        layout_semantics: list[PdfSemanticTable],
    ) -> list[PdfSemanticTable]:
        """
        Selecciona la mejor evidencia semántica sin duplicar una misma
        tabla descubierta por dos rutas de extracción.

        La ruta física conserva la estructura tabular del extractor.
        La ruta de layout puede representar mejor la tabla visual completa.
        Cuando ambas describen la misma tabla, se conserva la de mayor
        confianza.
        """
        selected_physical = list(physical_semantics)

        for layout in layout_semantics:
            matches = [
                physical
                for physical in selected_physical
                if PDFDocumentProcessor._is_semantic_match(
                    physical,
                    layout,
                    physical_count=len(selected_physical),
                )
            ]

            if not matches:
                selected_physical.append(layout)
                continue

            best_physical = max(
                matches,
                key=lambda table: table.confidence,
            )

            if layout.confidence > best_physical.confidence:
                selected_physical.remove(best_physical)
                selected_physical.append(layout)

        return sorted(
            selected_physical,
            key=lambda table: (
                table.source_page_number or 0,
                table.table_id,
            ),
        )

    @staticmethod
    def _is_semantic_match(
        physical: PdfSemanticTable,
        layout: PdfSemanticTable,
        *,
        physical_count: int,
    ) -> bool:
        """Determina si dos representaciones describen la misma tabla."""
        if physical.source_page_number != layout.source_page_number:
            return False

        physical_keys = {column.key for column in physical.columns}
        layout_keys = {column.key for column in layout.columns}

        if not physical_keys or not layout_keys:
            return False

        common_keys = len(physical_keys & layout_keys)
        key_coverage = common_keys / max(
            len(physical_keys),
            len(layout_keys),
        )

        if key_coverage < 0.60:
            return False

        # Si solo existe una tabla física semánticamente válida en la
        # página, la coincidencia de columnas es suficiente para tratar
        # el resultado de layout como una segunda representación de ella.
        if physical_count == 1:
            return True

        physical_values = {
            str(value).strip().lower()
            for row in physical.rows
            for value in row.values()
            if str(value).strip()
        }
        layout_values = {
            str(value).strip().lower()
            for row in layout.rows
            for value in row.values()
            if str(value).strip()
        }

        if not physical_values or not layout_values:
            return False

        common_values = len(
            physical_values & layout_values
        )

        return (
            common_values / max(
                min(
                    len(physical_values),
                    len(layout_values),
                ),
                1,
            )
            >= 0.20
        )

    @staticmethod
    def _attach_best_semantics(
        *,
        tables: list[PdfTable],
        selected_semantics: list[PdfSemanticTable],
    ) -> list[PdfTable]:
        """
        Vincula una semántica seleccionada con una tabla física solamente
        cuando existe evidencia suficiente para demostrar la relación.

        Una semántica obtenida exclusivamente mediante layout puede
        permanecer sin ``source_table_id``. Eso no es un error: significa
        que el motor comprendió una estructura visual que el extractor
        físico no pudo representar como la misma tabla.

        Nunca se asigna una tabla física por posición, orden o proximidad
        solamente.
        """
        result: list[PdfTable] = []

        for table in tables:
            exact = [
                semantic
                for semantic in selected_semantics
                if semantic.source_table_id == table.table_id
            ]

            if exact:
                semantic = max(
                    exact,
                    key=lambda item: item.confidence,
                )

                result.append(
                    replace(
                        table,
                        semantic=semantic,
                    )
                )
                continue

            candidates: list[
                tuple[float, PdfSemanticTable]
            ] = []

            for semantic in selected_semantics:
                if (
                    semantic.source_table_id
                    or semantic.source_page_number
                    != table.page_number
                ):
                    continue

                score = PDFDocumentProcessor._semantic_table_match_score(
                    table=table,
                    semantic=semantic,
                )

                if score >= 0.60:
                    candidates.append(
                        (score, semantic)
                    )

            if candidates:
                _, semantic = max(
                    candidates,
                    key=lambda item: (
                        item[0],
                        item[1].confidence,
                    ),
                )

                traced = replace(
                    semantic,
                    table_id=f"{table.table_id}-semantic",
                    source_table_id=table.table_id,
                    source_page_number=table.page_number,
                    evidence=tuple(
                        dict.fromkeys(
                            (
                                *semantic.evidence,
                                f"source_table:{table.table_id}",
                                "source_resolution:physical_match",
                            )
                        )
                    ),
                )

                result.append(
                    replace(
                        table,
                        semantic=traced,
                    )
                )
                continue

            # No existe evidencia suficiente para relacionar esta tabla
            # física con una semántica seleccionada. No inventamos la
            # procedencia.
            result.append(
                replace(
                    table,
                    semantic=None,
                )
                if table.semantic is not None
                else table
            )

        return result

    @staticmethod
    def _synchronize_selected_semantics(
        *,
        tables: list[PdfTable],
        selected_semantics: list[PdfSemanticTable],
    ) -> list[PdfSemanticTable]:
        """
        Garantiza que ``ProcessedPdfDocument.semantic_tables`` utilice
        exactamente la misma representación semántica que fue colocada
        dentro de ``PdfTable.semantic`` cuando existe una relación física.

        Las semánticas exclusivamente de layout se conservan sin
        ``source_table_id`` y mantienen su evidencia original.
        """
        by_source_table = {
            table.semantic.source_table_id: table.semantic
            for table in tables
            if table.semantic is not None
            and table.semantic.source_table_id
        }

        synchronized: list[PdfSemanticTable] = []

        for semantic in selected_semantics:
            if semantic.source_table_id:
                canonical = by_source_table.get(
                    semantic.source_table_id
                )

                if canonical is not None:
                    synchronized.append(canonical)
                    continue

            synchronized.append(semantic)

        unique: dict[str, PdfSemanticTable] = {}

        for semantic in synchronized:
            unique[semantic.table_id] = semantic

        return sorted(
            unique.values(),
            key=lambda item: (
                item.source_page_number or 0,
                item.table_id,
            ),
        )

    @staticmethod
    def _semantic_table_match_score(
        *,
        table: PdfTable,
        semantic: PdfSemanticTable,
    ) -> float:
        """
        Calcula evidencia de correspondencia entre una tabla física y una
        semántica de layout.

        La puntuación combina:
        - coincidencia exacta de valores;
        - cobertura de valores;
        - compatibilidad del ancho físico;
        - compatibilidad del número de filas.

        No utiliza únicamente el hecho de estar en la misma página.
        """
        if semantic.source_page_number != table.page_number:
            return 0.0

        if not table.rows or not semantic.rows:
            return 0.0

        physical_values = {
            PDFDocumentProcessor._normalize_evidence_value(value)
            for row in table.rows
            for value in row
            if str(value).strip()
        }

        semantic_values = {
            PDFDocumentProcessor._normalize_evidence_value(value)
            for row in semantic.rows
            for value in row.values()
            if str(value).strip()
        }

        physical_values.discard("")
        semantic_values.discard("")

        if not physical_values or not semantic_values:
            return 0.0

        common_values = physical_values & semantic_values

        if not common_values:
            return 0.0

        value_precision = len(common_values) / len(semantic_values)
        value_recall = len(common_values) / len(physical_values)

        value_score = (
            value_precision * 0.65
            + value_recall * 0.35
        )

        physical_width = max(
            len(row)
            for row in table.rows
        )

        semantic_width = len(semantic.columns)

        if semantic_width <= 0:
            return 0.0

        width_distance = abs(
            physical_width - semantic_width
        )

        width_score = max(
            0.0,
            1.0
            - (
                width_distance
                / max(
                    physical_width,
                    semantic_width,
                    1,
                )
            ),
        )

        physical_row_count = len(table.rows)
        semantic_row_count = len(semantic.rows)

        row_distance = abs(
            physical_row_count
            - semantic_row_count
        )

        row_score = max(
            0.0,
            1.0
            - (
                row_distance
                / max(
                    physical_row_count,
                    semantic_row_count,
                    1,
                )
            ),
        )

        return round(
            value_score * 0.70
            + width_score * 0.15
            + row_score * 0.15,
            4,
        )

    @staticmethod
    def _normalize_evidence_value(
        value: Any,
    ) -> str:
        """
        Normaliza valores únicamente para comparar evidencia de origen.

        No modifica el valor almacenado en la tabla.
        """
        text = str(value).strip().lower()

        if not text:
            return ""

        return " ".join(text.split())

    @classmethod
    @staticmethod
    def _normalize_comparison_text(value: str) -> str:
        return " ".join(value.lower().split())

    @staticmethod
    def _token_overlap(
        left: str,
        right: str,
    ) -> float:
        left_tokens = {
            token
            for token in left.split()
            if token
        }
        right_tokens = {
            token
            for token in right.split()
            if token
        }

        if not left_tokens or not right_tokens:
            return 0.0

        intersection = len(
            left_tokens & right_tokens
        )
        denominator = min(
            len(left_tokens),
            len(right_tokens),
        )

        return intersection / denominator

    @classmethod
    def _merge_text(
        cls,
        *,
        native_text: str,
        ocr_text: str,
    ) -> str:
        native = native_text.strip()
        ocr = ocr_text.strip()

        if not native:
            return ocr
        if not ocr:
            return native

        native_normalized = cls._normalize_comparison_text(native)
        ocr_normalized = cls._normalize_comparison_text(ocr)

        if native_normalized in ocr_normalized:
            return ocr

        if ocr_normalized in native_normalized:
            return native

        # En documentos escaneados puede existir una pequeña cantidad
        # de texto nativo residual o incorrectamente extraído. Si el OCR
        # contiene prácticamente los mismos tokens y aporta más contenido,
        # utilizamos el OCR como representación textual principal para
        # evitar duplicaciones.
        if (
            len(ocr_normalized) >= len(native_normalized)
            and cls._token_overlap(
                native_normalized,
                ocr_normalized,
            ) >= 0.60
        ):
            return ocr

        return f"{native}\n{ocr}".strip()

    @staticmethod
    def _extract_page_text_value(
        blocks: list[PdfTextBlock],
    ) -> str:
        return " ".join(
            block.text.strip()
            for block in blocks
            if block.text.strip()
        ).strip()

    @classmethod
    def _select_layout_blocks_for_ocr(
        cls,
        *,
        native_blocks: list[PdfTextBlock],
        ocr_blocks: list[PdfTextBlock],
        native_text: str,
        ocr_text: str,
    ) -> list[PdfTextBlock]:
        if not ocr_blocks:
            return native_blocks
        if not native_blocks:
            return ocr_blocks

        native_normalized = cls._normalize_comparison_text(native_text)
        ocr_normalized = cls._normalize_comparison_text(ocr_text)

        if native_normalized and native_normalized in ocr_normalized:
            return ocr_blocks

        if ocr_normalized and ocr_normalized in native_normalized:
            return native_blocks

        return [*native_blocks, *ocr_blocks]

    def _requires_ocr(
        cls,
        *,
        has_text: bool,
        has_images: bool,
        text_length: int,
    ) -> bool:
        """
        Determina si una página requiere OCR.

        No basta con tener poco texto para asumir que una página
        es un escaneo. Una página válida puede contener solamente
        una cantidad pequeña de texto.

        En esta etapa se marca OCR como requerido principalmente cuando:
        - no existe texto extraíble y existen imágenes;
        - existe muy poco texto y además existen imágenes.

        La ejecución OCR se realiza mediante ``OcrProcessor`` cuando la
        página cumple los criterios de necesidad de OCR.
        """
        if not has_text and has_images:
            return True

        if (
            has_text
            and text_length < cls.OCR_TEXT_THRESHOLD
            and has_images
        ):
            return True

        return False

    @staticmethod
    def _extract_page_text(
        page: pdfplumber.page.Page,
        warnings: list[str],
    ) -> str:
        try:
            text = page.extract_text(
                x_tolerance=2,
                y_tolerance=3,
            ) or ""

            return text.strip()

        except Exception as exc:
            warnings.append(
                f"No se pudo extraer texto de la página: {exc}"
            )
            return ""

    @staticmethod
    def _extract_text_blocks(
        page_number: int,
        page: pdfplumber.page.Page,
        fallback_text: str,
        warnings: list[str],
    ) -> list[PdfTextBlock]:
        blocks: list[PdfTextBlock] = []

        try:
            words = page.extract_words(
                x_tolerance=2,
                y_tolerance=3,
                keep_blank_chars=False,
            )

            for index, word in enumerate(words):
                text = str(
                    word.get("text") or ""
                ).strip()

                if not text:
                    continue

                bbox = (
                    float(word["x0"]),
                    float(word["top"]),
                    float(word["x1"]),
                    float(word["bottom"]),
                )

                blocks.append(
                    PdfTextBlock(
                        block_id=(
                            f"page-{page_number}-"
                            f"text-{index + 1}"
                        ),
                        page_number=page_number,
                        text=text,
                        bbox=bbox,
                    )
                )

        except Exception as exc:
            warnings.append(
                f"No se pudieron obtener bloques de texto: {exc}"
            )

        if not blocks and fallback_text:
            blocks.append(
                PdfTextBlock(
                    block_id=f"page-{page_number}-text-1",
                    page_number=page_number,
                    text=fallback_text,
                )
            )

        return blocks

    @staticmethod
    def _extract_tables(
        page_number: int,
        page: pdfplumber.page.Page,
        warnings: list[str],
    ) -> list[PdfTable]:
        tables: list[PdfTable] = []

        try:
            extracted = page.extract_tables()

            for index, raw_table in enumerate(extracted):
                rows: list[tuple[str, ...]] = []

                for raw_row in raw_table or []:
                    row = tuple(
                        str(cell or "").strip()
                        for cell in raw_row
                    )

                    if any(row):
                        rows.append(row)

                if rows:
                    bbox = None

                    try:
                        physical_tables = page.find_tables()
                        if index < len(physical_tables):
                            raw_bbox = physical_tables[index].bbox
                            if raw_bbox and len(raw_bbox) == 4:
                                bbox = tuple(
                                    float(value)
                                    for value in raw_bbox
                                )
                    except Exception as exc:
                        warnings.append(
                            f"No se pudo obtener la geometría de la tabla "
                            f"{index + 1}: {exc}"
                        )

                    tables.append(
                        PdfTable(
                            table_id=(
                                f"page-{page_number}-"
                                f"table-{index + 1}"
                            ),
                            page_number=page_number,
                            rows=tuple(rows),
                            bbox=bbox,
                        )
                    )

        except Exception as exc:
            warnings.append(
                f"No se pudieron extraer tablas: {exc}"
            )

        return tables

    @staticmethod
    def _extract_images(
        page_number: int,
        reader_page: Any,
        plumber_page: pdfplumber.page.Page,
        warnings: list[str],
    ) -> list[PdfImage]:
        images: list[PdfImage] = []

        try:
            page_images = getattr(
                reader_page,
                "images",
                (),
            )

            for index, image in enumerate(page_images):
                data = getattr(
                    image,
                    "data",
                    b"",
                ) or b""

                width = getattr(
                    image,
                    "width",
                    None,
                )

                height = getattr(
                    image,
                    "height",
                    None,
                )

                name = str(
                    getattr(
                        image,
                        "name",
                        f"image-{index + 1}",
                    )
                )

                images.append(
                    PdfImage(
                        image_id=(
                            f"page-{page_number}-"
                            f"{name}"
                        ),
                        page_number=page_number,
                        width=(
                            int(width)
                            if width is not None
                            else None
                        ),
                        height=(
                            int(height)
                            if height is not None
                            else None
                        ),
                        image_format="",
                        byte_size=len(data),
                    )
                )

        except Exception as exc:
            warnings.append(
                f"No se pudieron inspeccionar las imágenes: {exc}"
            )

        # pdfplumber permite detectar imágenes aunque pypdf
        # no haya podido exponerlas como objetos de imagen.
        try:
            plumber_images = getattr(
                plumber_page,
                "images",
                (),
            )

            if plumber_images and not images:
                for index, image in enumerate(
                    plumber_images
                ):
                    images.append(
                        PdfImage(
                            image_id=(
                                f"page-{page_number}-"
                                f"detected-image-{index + 1}"
                            ),
                            page_number=page_number,
                            width=(
                                int(image["width"])
                                if image.get("width")
                                else None
                            ),
                            height=(
                                int(image["height"])
                                if image.get("height")
                                else None
                            ),
                        )
                    )

        except Exception as exc:
            warnings.append(
                f"No se pudieron inspeccionar "
                f"elementos visuales: {exc}"
            )

        return images

    @staticmethod
    def _extract_pdf_metadata(
        reader: PdfReader,
    ) -> dict[str, Any]:
        metadata = reader.metadata

        if metadata is None:
            return {}

        result: dict[str, Any] = {}

        for key, value in metadata.items():
            normalized_key = str(key).lstrip("/")

            result[normalized_key] = (
                str(value)
                if value is not None
                else ""
            )

        return result