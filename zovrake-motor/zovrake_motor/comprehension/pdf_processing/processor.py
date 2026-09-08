"""Procesador documental profundo para archivos PDF."""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
from io import BytesIO
from typing import Any
from difflib import SequenceMatcher

import pdfplumber
from pypdf import PdfReader

from zovrake_motor.comprehension.pdf_processing.exceptions import (
    PdfExtractionError,
    PdfInvalidDocumentError,
)
from zovrake_motor.comprehension.pdf_processing.models import (
    PdfImage,
    PdfReadingEntry,
    PdfStructuralObject,
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
from zovrake_motor.comprehension.pdf_processing.visual_understanding import (
    MultimodalVisualUnderstandingEngine,
)


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
        ocr_visual_pages: bool = True,
        ocr_all_pages: bool = True,
        ocr_embedded_images: bool = True,
    ) -> None:
        self._ocr_processor = ocr_processor or OcrProcessor()
        self._ocr_visual_pages = bool(ocr_visual_pages)
        self._ocr_all_pages = bool(ocr_all_pages)
        self._ocr_embedded_images = bool(ocr_embedded_images)
        self._visual_understanding = MultimodalVisualUnderstandingEngine()

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
            with pdfplumber.open(
                BytesIO(pdf_bytes),
                strict_metadata=False,
            ) as plumber_pdf:
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
            reader = PdfReader(BytesIO(pdf_bytes), strict=False)
        except Exception as exc:
            raise PdfInvalidDocumentError(
                f"El archivo no pudo abrirse como PDF: {exc}"
            ) from exc

        # Los PDF cifrados que no requieren contraseña sí pueden procesarse
        # de forma transparente. Un PDF protegido con contraseña real no se
        # puede leer legítimamente sin esa credencial y se informa como tal.
        if reader.is_encrypted:
            try:
                decrypted = reader.decrypt("")
            except Exception as exc:
                raise PdfInvalidDocumentError(
                    "El PDF está cifrado y no pudo desbloquearse sin contraseña."
                ) from exc
            if not decrypted:
                raise PdfInvalidDocumentError(
                    "El PDF está protegido con contraseña; se requiere la credencial para leer su contenido."
                )

        return reader

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
        all_structural_objects: list[PdfStructuralObject] = []
        full_text_parts: list[str] = []
        document_warnings: list[str] = []
        document_errors: list[str] = []
        visual_text_parts: list[str] = []

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
                reading_order=(),
                ordered_text="",
                capture_audit={
                    "status": "invalid",
                    "page_count": 0,
                    "reason": "document_without_pages",
                },
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
                all_structural_objects.extend(
                    self._extract_page_structural_objects(
                        page_number=page_number,
                        reader_page=reader.pages[index],
                        plumber_page=plumber_pdf.pages[index],
                        warnings=document_warnings,
                    )
                )

                if page_result.text.strip():
                    full_text_parts.append(
                        f"[Página {page_number}]\n"
                        f"{page_result.text}"
                    )

                document_warnings.extend(page_result.warnings)

                if page_result.visual_text.strip():
                    visual_text_parts.append(
                        f"[Página {page_number}]\n"
                        f"{page_result.visual_text}"
                    )

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

                # Aunque falle una etapa de comprensión de la página,
                # intentamos conservar su estructura física de forma
                # independiente para no perder evidencia documental.
                try:
                    all_structural_objects.extend(
                        self._extract_page_structural_objects(
                            page_number=page_number,
                            reader_page=reader.pages[index],
                            plumber_page=plumber_pdf.pages[index],
                            warnings=document_warnings,
                        )
                    )
                except Exception as structural_exc:
                    document_warnings.append(
                        f"Página {page_number}: tampoco fue posible "
                        f"inventariar la estructura tras el fallo principal: "
                        f"{structural_exc}"
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

        all_structural_objects.extend(
            self._extract_document_structural_objects(
                reader=reader,
                warnings=document_warnings,
            )
        )

        metadata = self._extract_pdf_metadata(reader)
        metadata["document_payload_sha256"] = sha256(pdf_bytes).hexdigest()
        metadata["document_payload_size_bytes"] = len(pdf_bytes)

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

        visual_ocr_pages_executed = tuple(
            page.page_number
            for page in pages
            if page.visual_ocr_attempted and page.ocr_executed
        )
        visual_rendered_page_hashes = tuple(
            page.visual_render_sha256
            for page in pages
            if page.visual_render_sha256
        )
        visual_ocr_complete = (
            bool(pages)
            and len(visual_ocr_pages_executed) == len(pages)
        )
        visual_text = "\n\n".join(
            part
            for part in visual_text_parts
            if part.strip()
        ).strip()

        if self._ocr_all_pages and not visual_ocr_complete:
            document_warnings.append(
                "La lectura visual no alcanzó cobertura completa en "
                "todas las páginas del PDF."
            )

        document_reading_order = self._build_document_reading_order(
            pages=pages,
            structural_objects=all_structural_objects,
        )
        ordered_text = self._build_ordered_text(document_reading_order)
        capture_audit = self._build_document_capture_audit(
            pages=pages,
            images=all_images,
            tables=all_tables,
            semantic_tables=all_semantic_tables,
            structural_objects=all_structural_objects,
            reading_order=document_reading_order,
            document_errors=document_errors,
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
            structural_objects=tuple(all_structural_objects),
            pdf_metadata=metadata,
            coverage=self._build_coverage_report(
                pages=pages,
                images=all_images,
                structural_objects=all_structural_objects,
                document_errors=document_errors,
            ),
            ocr_required=ocr_required,
            ocr_executed=ocr_executed,
            ocr_pages_executed=ocr_pages_executed,
            ocr_confidence=round(ocr_confidence, 4),
            ocr_language=ocr_language,
            ocr_dpi=ocr_dpi,
            visual_text=visual_text,
            visual_ocr_complete=visual_ocr_complete,
            visual_ocr_pages_executed=visual_ocr_pages_executed,
            visual_render_page_count=len(visual_rendered_page_hashes),
            visual_rendered_page_hashes=visual_rendered_page_hashes,
            reading_order=document_reading_order,
            ordered_text=ordered_text,
            capture_audit=capture_audit,
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
        native_text = text

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
            pdf_bytes,
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
        if self._ocr_all_pages:
            requires_ocr = True
        elif self._ocr_visual_pages and has_images:
            requires_ocr = True

        ocr_executed = False
        ocr_text = ""
        ocr_blocks: tuple[PdfOcrBlock, ...] = ()
        ocr_confidence = 0.0
        ocr_language = ""
        ocr_dpi: int | None = None
        visual_text = ""
        visual_ocr_attempted = False
        visual_ocr_complete = False
        visual_render_sha256 = ""
        visual_render_width_px: int | None = None
        visual_render_height_px: int | None = None
        ocr_passes_executed: tuple[int, ...] = ()
        visual_understanding: dict[str, Any] = {}

        if requires_ocr:
            visual_ocr_attempted = True
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

                visual_render_sha256 = ocr_result.render_sha256
                visual_render_width_px = ocr_result.render_width_px
                visual_render_height_px = ocr_result.render_height_px
                ocr_passes_executed = ocr_result.passes_executed

                visual_text = ocr_text
                visual_ocr_complete = True
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
                visual_ocr_complete = False
                warnings.append(
                    f"Página {page_number}: no fue posible ejecutar OCR: {exc}"
                )

        has_text = bool(text.strip())
        has_tables = bool(tables) or bool(semantic_tables)
        has_images = bool(images)

        visual_understanding = {
            "stage": "visual_capture",
            "visual_ocr_complete": visual_ocr_complete,
            "visual_text_length": len(visual_text.strip()),
            "ocr_block_count": len(ocr_blocks),
            "ocr_confidence": ocr_confidence,
            "image_count": len(images),
        }

        # La página completa se analiza visualmente independientemente de que
        # OCR haya reconocido texto. Esto cubre gráficos, logos vectoriales,
        # sellos, firmas, diagramas y composiciones que no existan como
        # imágenes embebidas independientes.
        try:
                rendered = self._ocr_processor.render_page(
                    pdf_bytes=pdf_bytes,
                    page_number=page_number,
                )
                try:
                    page_visual = self._visual_understanding.analyze_pil_image(
                        image=rendered,
                        detected_text=visual_text,
                        page_number=page_number,
                        source_id=f"page-{page_number}",
                    )
                    visual_understanding = page_visual.to_dict() | {
                        "stage": "page_visual_understanding",
                        "visual_ocr_complete": visual_ocr_complete,
                        "ocr_passes_executed": list(ocr_passes_executed),
                        "image_count": len(images),
                    }
                finally:
                    rendered.close()
        except Exception as exc:
            warnings.append(
                f"Página {page_number}: no pudo completarse la comprensión visual local: {exc}"
            )
            visual_understanding = {
                **visual_understanding,
                "analysis_status": "failed",
                "analysis_error": str(exc),
            }

        return PdfPageAnalysis(
            page_number=page_number,
            width=width,
            height=height,
            text=text,
            native_text=native_text,
            text_blocks=tuple(text_blocks),
            tables=tuple(tables),
            semantic_tables=tuple(semantic_tables),
            images=tuple(images),
            has_text=has_text,
            has_tables=has_tables,
            has_images=has_images,
            requires_ocr=requires_ocr,
            visual_text=visual_text,
            visual_ocr_complete=visual_ocr_complete,
            visual_ocr_attempted=visual_ocr_attempted,
            visual_render_sha256=visual_render_sha256,
            visual_render_width_px=visual_render_width_px,
            visual_render_height_px=visual_render_height_px,
            ocr_passes_executed=ocr_passes_executed,
            visual_understanding=visual_understanding,
            reading_order=self._build_page_reading_order(
                page_number=page_number,
                width=width,
                height=height,
                text_blocks=text_blocks,
                tables=tables,
                semantic_tables=semantic_tables,
                images=images,
                visual_understanding=visual_understanding,
            ),
            capture_audit=self._build_page_capture_audit(
                page_number=page_number,
                native_text=native_text,
                text=text,
                text_blocks=text_blocks,
                tables=tables,
                semantic_tables=semantic_tables,
                images=images,
                structural_objects=(),
                requires_ocr=requires_ocr,
                ocr_executed=ocr_executed,
                visual_ocr_attempted=visual_ocr_attempted,
                visual_ocr_complete=visual_ocr_complete,
                visual_render_sha256=visual_render_sha256,
                visual_understanding=visual_understanding,
                ocr_blocks=ocr_blocks,
                reading_order_count=len(
                    self._build_page_reading_order(
                        page_number=page_number,
                        width=width,
                        height=height,
                        text_blocks=text_blocks,
                        tables=tables,
                        semantic_tables=semantic_tables,
                        images=images,
                        visual_understanding=visual_understanding,
                    )
                ),
                warnings=warnings,
            ),
            ocr_executed=ocr_executed,
            ocr_text=ocr_text,
            ocr_blocks=ocr_blocks,
            ocr_confidence=ocr_confidence,
            ocr_language=ocr_language,
            ocr_dpi=ocr_dpi,
            warnings=tuple(warnings),
        )

    @staticmethod
    def _bbox_area(bbox: tuple[float, float, float, float] | None) -> float:
        if bbox is None or len(bbox) != 4:
            return 0.0
        x0, y0, x1, y1 = bbox
        return max(0.0, x1 - x0) * max(0.0, y1 - y0)

    @staticmethod
    def _block_lies_inside_table_vertical_span(
        block: PdfTextBlock,
        table_bbox: tuple[float, float, float, float],
    ) -> bool:
        if block.bbox is None:
            return False
        _, block_y0, _, block_y1 = block.bbox
        _, table_y0, _, table_y1 = table_bbox
        return block_y0 >= table_y0 - 4.0 and block_y1 <= table_y1 + 4.0

    @staticmethod
    def _text_block_belongs_to_table(
        text: str,
        table_values: set[str],
    ) -> bool:
        normalized = PDFDocumentProcessor._normalize_comparison_text(text)
        if not normalized:
            return False
        if normalized in table_values:
            return True
        if len(normalized) >= 4:
            return any(
                normalized in value or value in normalized
                for value in table_values
                if len(value) >= 4
            )
        return False

    @classmethod
    def _infer_table_bbox_from_text(
        cls,
        *,
        table: PdfTable,
        text_blocks: list[PdfTextBlock],
    ) -> tuple[float, float, float, float] | None:
        values = {
            cls._normalize_comparison_text(str(cell or ""))
            for row in table.rows
            for cell in row
            if str(cell or "").strip()
        }
        if not values:
            return None

        matched = [
            block.bbox
            for block in text_blocks
            if block.bbox is not None
            and cls._text_block_belongs_to_table(block.text, values)
        ]
        if not matched:
            return None

        return (
            min(box[0] for box in matched),
            min(box[1] for box in matched),
            max(box[2] for box in matched),
            max(box[3] for box in matched),
        )

    @staticmethod
    def _group_text_blocks_into_lines(
        blocks: list[PdfTextBlock],
    ) -> list[dict[str, Any]]:
        """Agrupa palabras/bloques próximos en líneas de lectura deterministas."""
        if not blocks:
            return []

        positioned = [
            block
            for block in blocks
            if block.bbox is not None
        ]
        unpositioned = [
            block
            for block in blocks
            if block.bbox is None
        ]

        lines: list[dict[str, Any]] = []
        for block in sorted(
            positioned,
            key=lambda item: (
                (item.bbox[1] + item.bbox[3]) / 2.0,
                item.bbox[0],
                item.block_id,
            ),
        ):
            x0, y0, x1, y1 = block.bbox
            center_y = (y0 + y1) / 2.0
            height = max(1.0, y1 - y0)
            target = None
            for line in reversed(lines[-8:]):
                tolerance = max(3.0, min(10.0, max(line['height'], height) * 0.65))
                if abs(center_y - line['center_y']) <= tolerance:
                    target = line
                    break

            if target is None:
                lines.append({
                    'center_y': center_y,
                    'height': height,
                    'words': [(x0, block.text.strip(), block)],
                    'source_block_ids': [block.block_id],
                    'confidence': [1.0],
                })
            else:
                target['words'].append((x0, block.text.strip(), block))
                target['source_block_ids'].append(block.block_id)
                target['height'] = max(target['height'], height)
                target['center_y'] = (target['center_y'] + center_y) / 2.0
                target['confidence'].append(1.0)

        lines.sort(key=lambda item: (item['center_y'], min(word[0] for word in item['words'])))
        result: list[dict[str, Any]] = []
        for line in lines:
            ordered_words = sorted(line['words'], key=lambda item: (item[0], item[2].block_id))
            texts = [word for _, word, _ in ordered_words if word]
            source_blocks = [block for _, _, block in ordered_words]
            x0 = min(block.bbox[0] for block in source_blocks)
            y0 = min(block.bbox[1] for block in source_blocks)
            x1 = max(block.bbox[2] for block in source_blocks)
            y1 = max(block.bbox[3] for block in source_blocks)
            result.append({
                'text': ' '.join(texts),
                'bbox': (x0, y0, x1, y1),
                'confidence': 1.0,
                'source_block_ids': tuple(block.block_id for block in source_blocks),
            })

        for block in unpositioned:
            result.append({
                'text': block.text.strip(),
                'bbox': None,
                'confidence': 1.0,
                'source_block_ids': (block.block_id,),
            })

        return result

    @classmethod
    def _bbox_intersection_ratio(
        cls,
        left: tuple[float, float, float, float] | None,
        right: tuple[float, float, float, float] | None,
    ) -> float:
        if left is None or right is None:
            return 0.0
        lx0, ly0, lx1, ly1 = left
        rx0, ry0, rx1, ry1 = right
        ix0, iy0 = max(lx0, rx0), max(ly0, ry0)
        ix1, iy1 = min(lx1, rx1), min(ly1, ry1)
        if ix1 <= ix0 or iy1 <= iy0:
            return 0.0
        intersection = (ix1 - ix0) * (iy1 - iy0)
        return intersection / max(cls._bbox_area(right), 1.0)

    @classmethod
    def _build_page_reading_order(
        cls,
        *,
        page_number: int,
        width: float,
        height: float,
        text_blocks: list[PdfTextBlock],
        tables: list[PdfTable],
        semantic_tables: list[PdfSemanticTable],
        images: list[PdfImage],
        visual_understanding: dict[str, Any],
    ) -> tuple[PdfReadingEntry, ...]:
        """Construye una única secuencia espacial sin destruir ninguna fuente."""
        candidates: list[tuple[float, float, int, PdfReadingEntry]] = []

        inferred_table_bboxes = [
            table.bbox
            or cls._infer_table_bbox_from_text(
                table=table,
                text_blocks=text_blocks,
            )
            for table in tables
        ]
        physical_table_bboxes = [
            bbox for bbox in inferred_table_bboxes if bbox is not None
        ]

        table_value_texts: list[set[str]] = [
            {
                cls._normalize_comparison_text(str(cell or ""))
                for row in table.rows
                for cell in row
                if str(cell or "").strip()
            }
            for table in tables
        ]

        # Texto: se reconstruye en líneas de lectura mediante coordenadas,
        # conservando además los IDs de cada bloque como evidencia.
        filtered_text_blocks = [
            block
            for block in text_blocks
            if block.text.strip()
            and not any(
                cls._bbox_intersection_ratio(block.bbox, bbox) >= 0.70
                for bbox in physical_table_bboxes
            )
            and not any(
                cls._text_block_belongs_to_table(block.text, values)
                for values in table_value_texts
                if values
            )
            and not any(
                cls._block_lies_inside_table_vertical_span(block, bbox)
                for bbox in inferred_table_bboxes
                if bbox is not None
            )
        ]
        for line_index, line in enumerate(
            cls._group_text_blocks_into_lines(filtered_text_blocks),
            start=1,
        ):
            text = line['text']
            bbox = line['bbox']
            entry = PdfReadingEntry(
                sequence=0,
                page_number=page_number,
                content_type='text_line',
                source_id=f'page-{page_number}-reading-line-{line_index}',
                text=text,
                bbox=bbox,
                confidence=float(line['confidence']),
                source_kind='document_text_ordered',
                metadata={
                    'source_block_ids': list(line['source_block_ids']),
                    'block_count': len(line['source_block_ids']),
                },
            )
            y = bbox[1] if bbox is not None else float(line_index)
            x = bbox[0] if bbox is not None else 0.0
            candidates.append((y, x, 10, entry))

        # Tablas físicas como unidades atómicas; todas sus celdas se
        # conservan en metadata para evitar perder estructura.
        for index, table in enumerate(tables):
            content = '\n'.join(' | '.join(str(cell or '') for cell in row) for row in table.rows)
            if not content.strip():
                continue
            bbox = inferred_table_bboxes[index]
            y = bbox[1] if bbox else float('inf')
            x = bbox[0] if bbox else 0.0
            entry = PdfReadingEntry(
                sequence=0,
                page_number=page_number,
                content_type='table',
                source_id=table.table_id,
                text=content,
                bbox=bbox,
                confidence=table.semantic.confidence if table.semantic else 1.0,
                source_kind='pdf_table',
                metadata={
                    'row_count': len(table.rows),
                    'column_count': max((len(row) for row in table.rows), default=0),
                    'semantic_table_id': table.semantic.table_id if table.semantic else '',
                    'table_role': table.semantic.table_role if table.semantic else 'unknown',
                },
            )
            candidates.append((y, x, 20, entry))

        # Tablas solo semánticas: también llegan, incluso cuando no existe
        # tabla física, y por eso siguen siendo parte de la lectura completa.
        for index, table in enumerate(semantic_tables):
            if table.source_table_id:
                continue
            content = '\n'.join(
                ' | '.join(f'{key}={value}' for key, value in row.items())
                for row in table.rows
            )
            if not content.strip():
                continue
            entry = PdfReadingEntry(
                sequence=0,
                page_number=page_number,
                content_type='semantic_table',
                source_id=table.table_id,
                text=content,
                bbox=None,
                confidence=table.confidence,
                source_kind='semantic_table',
                metadata={
                    'row_count': len(table.rows),
                    'table_role': table.table_role,
                    'table_roles': list(table.table_roles),
                },
            )
            candidates.append((float('inf'), float(index), 21, entry))

        # Imágenes: conservamos tipo visual, texto OCR, QR y pistas
        # semánticas como una sola evidencia que viaja junta.
        for index, image in enumerate(images):
            visual = dict(image.visual_understanding or {})
            image_text = str(image.ocr_text or '').strip()
            description = str(visual.get('description') or '').strip()
            parts = []
            if image_text:
                parts.append(f'[Texto OCR de imagen]\n{image_text}')
            if description:
                parts.append(f'[Descripción visual]\n{description}')
            if visual.get('object_type'):
                parts.append(f"[Tipo de imagen]\n{visual.get('object_type')}")
            if visual.get('semantic_hints'):
                parts.append('[Pistas semánticas]\n' + ', '.join(map(str, visual.get('semantic_hints', ()))) )
            content = '\n'.join(parts)
            if not content.strip() and not image.content_sha256:
                continue
            bbox = image.bbox
            y = bbox[1] if bbox else float('inf')
            x = bbox[0] if bbox else float(index)
            entry = PdfReadingEntry(
                sequence=0,
                page_number=page_number,
                content_type='image',
                source_id=image.image_id,
                text=content,
                bbox=bbox,
                confidence=float(visual.get('visual_confidence', image.ocr_confidence or 0.0) or 0.0),
                source_kind='pdf_image',
                metadata={
                    'image_format': image.image_format,
                    'width': image.width,
                    'height': image.height,
                    'content_sha256': image.content_sha256,
                    'ocr_attempted': image.ocr_attempted,
                    'ocr_confidence': image.ocr_confidence,
                    'ocr_blocks': list(image.ocr_blocks),
                    'visual_understanding': visual,
                },
            )
            candidates.append((y, x, 30, entry))

        if visual_understanding:
            entry = PdfReadingEntry(
                sequence=0,
                page_number=page_number,
                content_type='page_visual',
                source_id=f'page-{page_number}-visual',
                text=str(visual_understanding.get('description') or ''),
                bbox=None,
                confidence=float(visual_understanding.get('visual_confidence', 0.0) or 0.0),
                source_kind='visual_understanding',
                metadata=dict(visual_understanding),
            )
            # La descripción visual ocupa conceptualmente toda la página y
            # se ordena detrás del contenido situado en ella.
            candidates.append((float('inf'), float('inf'), 40, entry))

        candidates.sort(key=lambda item: (item[0], item[2], item[1], item[3].source_id))
        return tuple(
            PdfReadingEntry(
                sequence=index,
                page_number=item[3].page_number,
                content_type=item[3].content_type,
                source_id=item[3].source_id,
                text=item[3].text,
                bbox=item[3].bbox,
                confidence=item[3].confidence,
                source_kind=item[3].source_kind,
                metadata=item[3].metadata,
            )
            for index, item in enumerate(candidates, start=1)
        )

    @classmethod
    def _build_document_reading_order(
        cls,
        *,
        pages: list[PdfPageAnalysis],
        structural_objects: list[PdfStructuralObject],
    ) -> tuple[PdfReadingEntry, ...]:
        entries: list[PdfReadingEntry] = []
        for page in sorted(pages, key=lambda item: item.page_number):
            entries.extend(page.reading_order)

        # Objetos estructurales entran en la secuencia con coordenadas si las
        # tienen; si no, después del contenido de su página.
        for item in structural_objects:
            if not str(item.text or '').strip():
                continue
            entries.append(
                PdfReadingEntry(
                    sequence=0,
                    page_number=item.page_number or 1,
                    content_type='structural_object',
                    source_id=item.object_id,
                    text=item.text,
                    bbox=item.bbox,
                    confidence=1.0,
                    source_kind='pdf_structure',
                    metadata=item.to_dict(),
                )
            )

        entries.sort(
            key=lambda item: (
                item.page_number,
                item.bbox[1] if item.bbox is not None else float('inf'),
                item.bbox[0] if item.bbox is not None else float('inf'),
                item.content_type,
                item.source_id,
            )
        )

        return tuple(
            PdfReadingEntry(
                sequence=index,
                page_number=entry.page_number,
                content_type=entry.content_type,
                source_id=entry.source_id,
                text=entry.text,
                bbox=entry.bbox,
                confidence=entry.confidence,
                source_kind=entry.source_kind,
                metadata=entry.metadata,
            )
            for index, entry in enumerate(entries, start=1)
        )

    @staticmethod
    def _build_ordered_text(entries: tuple[PdfReadingEntry, ...]) -> str:
        parts: list[str] = []
        current_page: int | None = None
        for entry in entries:
            if entry.page_number != current_page:
                current_page = entry.page_number
                parts.append(f'[Página {current_page}]')
            if not entry.text.strip():
                continue
            parts.append(f'[{entry.content_type}:{entry.source_id}]\n{entry.text.strip()}')
        return '\n\n'.join(parts).strip()

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
            return cls._deduplicate_layout_blocks(native_blocks)
        if not native_blocks:
            return cls._deduplicate_layout_blocks(ocr_blocks)

        native_normalized = cls._normalize_comparison_text(native_text)
        ocr_normalized = cls._normalize_comparison_text(ocr_text)

        if native_normalized and native_normalized in ocr_normalized:
            return cls._deduplicate_layout_blocks(ocr_blocks)

        if ocr_normalized and ocr_normalized in native_normalized:
            return cls._deduplicate_layout_blocks(native_blocks)

        return cls._deduplicate_layout_blocks([*native_blocks, *ocr_blocks])

    @classmethod
    def _deduplicate_layout_blocks(
        cls,
        blocks: list[PdfTextBlock],
    ) -> list[PdfTextBlock]:
        """Elimina duplicados nativo/OCR respetando posición y texto."""
        result: list[PdfTextBlock] = []
        for block in blocks:
            text = cls._normalize_comparison_text(block.text)
            if not text:
                continue
            duplicate_index = None
            for index, existing in enumerate(result):
                existing_text = cls._normalize_comparison_text(existing.text)
                if not existing_text:
                    continue
                similarity = SequenceMatcher(None, existing_text, text).ratio()
                if similarity < 0.90:
                    continue
                if existing.bbox is None or block.bbox is None:
                    duplicate_index = index
                    break
                if cls._bbox_iou(existing.bbox, block.bbox) >= 0.30:
                    duplicate_index = index
                    break
            if duplicate_index is None:
                result.append(block)
                continue

            existing = result[duplicate_index]
            # Mantener el bloque con mejor representación textual; en empate
            # se conserva el primero para estabilidad determinista.
            if len(block.text.strip()) > len(existing.text.strip()):
                result[duplicate_index] = block
        return result

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

    def _extract_images(
        self,
        page_number: int,
        reader_page: Any,
        plumber_page: pdfplumber.page.Page,
        pdf_bytes: bytes,
        warnings: list[str],
    ) -> list[PdfImage]:
        images: list[PdfImage] = []

        plumber_by_name: dict[str, dict[str, Any]] = {}
        try:
            for image in getattr(plumber_page, "images", ()) or ():
                name = str(image.get("name") or "").strip()
                if name:
                    plumber_by_name[name] = image
        except Exception as exc:
            warnings.append(
                f"No se pudo construir el índice geométrico de imágenes de "
                f"la página {page_number}: {exc}"
            )

        try:
            page_images = getattr(
                reader_page,
                "images",
                (),
            )

            for index, image in enumerate(page_images):
                data = getattr(image, "data", b"") or b""
                name = str(
                    getattr(
                        image,
                        "name",
                        f"image-{index + 1}",
                    )
                )
                base_name = name.rsplit(".", 1)[0]

                image_obj = getattr(image, "image", None)
                width = getattr(image_obj, "width", None)
                height = getattr(image_obj, "height", None)
                image_format = str(
                    getattr(image_obj, "format", "") or ""
                )

                source_geometry = (
                    plumber_by_name.get(base_name)
                    or plumber_by_name.get(name)
                )

                bbox = None
                if source_geometry is not None:
                    try:
                        bbox = tuple(
                            float(source_geometry[key])
                            for key in (
                                "x0",
                                "top",
                                "x1",
                                "bottom",
                            )
                        )
                    except Exception:
                        bbox = None

                content_sha256 = (
                    sha256(data).hexdigest()
                    if data
                    else ""
                )

                ocr_attempted = False
                ocr_text = ""
                ocr_confidence = 0.0
                ocr_blocks: tuple[dict[str, Any], ...] = ()

                if data and self._ocr_embedded_images:
                    ocr_attempted = True
                    try:
                        ocr_result = self._ocr_processor.process_image_bytes(
                            image_bytes=data,
                            page_number=page_number,
                        )
                        ocr_text = ocr_result.text
                        ocr_confidence = ocr_result.confidence
                        ocr_blocks = tuple(
                            {
                                "text": block.text,
                                "bbox": list(block.bbox),
                                "confidence": block.confidence,
                                "source": "embedded_image_ocr",
                                "coordinate_space": "image",
                            }
                            for block in ocr_result.blocks
                        )
                    except Exception as exc:
                        warnings.append(
                            f"Página {page_number}, imagen '{name}': "
                            f"no pudo ejecutarse OCR directo sobre la imagen: {exc}"
                        )

                visual_result = self._visual_understanding.analyze_image_bytes(
                    image_bytes=data,
                    detected_text=ocr_text,
                    page_number=page_number,
                    source_id=name,
                ) if data else None

                images.append(
                    PdfImage(
                        image_id=(
                            f"page-{page_number}-{name}"
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
                        image_format=image_format,
                        byte_size=len(data),
                        bbox=bbox,
                        content_sha256=content_sha256,
                        ocr_attempted=ocr_attempted,
                        ocr_text=ocr_text,
                        ocr_confidence=ocr_confidence,
                        ocr_blocks=ocr_blocks,
                        visual_understanding=(
                            visual_result.to_dict()
                            if visual_result is not None
                            else {"analysis_status": "unavailable"}
                        ),
                    )
                )

        except Exception as exc:
            warnings.append(
                f"No se pudieron inspeccionar las imágenes de la página "
                f"{page_number}: {exc}"
            )

        # pdfplumber puede detectar las mismas imágenes que pypdf con un
        # identificador ligeramente distinto (por ejemplo ``IM39`` frente a
        # ``IM39.jpg``). Primero enriquecemos la imagen que ya tiene payload
        # y después agregamos únicamente objetos realmente nuevos.
        try:
            plumber_images = getattr(
                plumber_page,
                "images",
                (),
            )

            def image_key(name: str, size: Any = None) -> tuple[str, Any]:
                normalized_name = str(name or "").strip().rsplit("/", 1)[-1]
                if "." in normalized_name:
                    normalized_name = normalized_name.rsplit(".", 1)[0]
                normalized_size = tuple(size or ()) if size else None
                return normalized_name.casefold(), normalized_size

            known_by_key = {
                image_key(image.image_id.split(f"page-{page_number}-", 1)[-1], (image.width, image.height)): index
                for index, image in enumerate(images)
            }

            for index, image in enumerate(plumber_images or ()): 
                name = str(
                    image.get("name")
                    or f"detected-image-{index + 1}"
                )
                srcsize = image.get("srcsize") or ()
                key = image_key(name, srcsize)

                bbox = None
                try:
                    bbox = tuple(
                        float(image[key_name])
                        for key_name in (
                            "x0",
                            "top",
                            "x1",
                            "bottom",
                        )
                    )
                except Exception:
                    bbox = None

                existing_index = known_by_key.get(key)
                if existing_index is not None:
                    existing = images[existing_index]
                    if existing.bbox is None and bbox is not None:
                        images[existing_index] = replace(
                            existing,
                            bbox=bbox,
                        )
                    continue

                image_id = f"page-{page_number}-{name}"
                recovered_bytes = b""
                recovered_width: int | None = (
                    int(srcsize[0]) if len(srcsize) >= 1 else None
                )
                recovered_height: int | None = (
                    int(srcsize[1]) if len(srcsize) >= 2 else None
                )

                # pdfplumber puede conocer la posición de una imagen que
                # pypdf no expone como payload binario. En ese caso no
                # declaramos la imagen como "leída": la reconstruimos desde
                # el render completo de la página y la sometemos al mismo
                # OCR/entendimiento visual local.
                if bbox is not None:
                    try:
                        recovered_bytes, recovered_width, recovered_height = (
                            self._recover_image_bytes_from_page(
                                pdf_bytes=pdf_bytes,
                                page_number=page_number,
                                bbox=bbox,
                            )
                        )
                    except Exception as exc:
                        warnings.append(
                            f"Página {page_number}, imagen '{name}': "
                            f"no pudo materializarse desde el render de página: {exc}"
                        )

                recovered_ocr_attempted = False
                recovered_ocr_text = ""
                recovered_ocr_confidence = 0.0
                recovered_ocr_blocks: tuple[dict[str, Any], ...] = ()
                recovered_visual_understanding: dict[str, Any] = {}

                if recovered_bytes:
                    if self._ocr_embedded_images:
                        recovered_ocr_attempted = True
                        try:
                            ocr_result = self._ocr_processor.process_image_bytes(
                                image_bytes=recovered_bytes,
                                page_number=page_number,
                            )
                            recovered_ocr_text = ocr_result.text
                            recovered_ocr_confidence = ocr_result.confidence
                            recovered_ocr_blocks = tuple(
                                {
                                    "text": block.text,
                                    "bbox": list(block.bbox),
                                    "confidence": block.confidence,
                                    "source": "recovered_page_crop_ocr",
                                    "coordinate_space": "image",
                                }
                                for block in ocr_result.blocks
                            )
                        except Exception as exc:
                            warnings.append(
                                f"Página {page_number}, imagen '{name}': "
                                f"OCR sobre región recuperada falló: {exc}"
                            )

                    try:
                        visual_result = self._visual_understanding.analyze_image_bytes(
                            image_bytes=recovered_bytes,
                            detected_text=recovered_ocr_text,
                            page_number=page_number,
                            source_id=image_id,
                        )
                        recovered_visual_understanding = visual_result.to_dict()
                    except Exception as exc:
                        warnings.append(
                            f"Página {page_number}, imagen '{name}': "
                            f"comprensión visual de región recuperada falló: {exc}"
                        )
                        recovered_visual_understanding = {
                            "analysis_status": "failed",
                            "error": str(exc),
                        }

                images.append(
                    PdfImage(
                        image_id=image_id,
                        page_number=page_number,
                        width=recovered_width,
                        height=recovered_height,
                        image_format="PNG" if recovered_bytes else "",
                        byte_size=len(recovered_bytes),
                        bbox=bbox,
                        content_sha256=(
                            sha256(recovered_bytes).hexdigest()
                            if recovered_bytes
                            else ""
                        ),
                        ocr_attempted=recovered_ocr_attempted,
                        ocr_text=recovered_ocr_text,
                        ocr_confidence=recovered_ocr_confidence,
                        ocr_blocks=recovered_ocr_blocks,
                        visual_understanding=recovered_visual_understanding,
                    )
                )
                known_by_key[key] = len(images) - 1

        except Exception as exc:
            warnings.append(
                f"No se pudieron inspeccionar elementos visuales "
                f"de la página {page_number}: {exc}"
            )

        return images

    def _recover_image_bytes_from_page(
        self,
        *,
        pdf_bytes: bytes,
        page_number: int,
        bbox: tuple[float, float, float, float],
    ) -> tuple[bytes, int, int]:
        """Materializa una región visual desde el render completo de página.

        Sirve para PDFs donde un extractor reconoce la presencia/posición de
        una imagen pero no entrega su payload binario. El recorte conserva la
        evidencia visual real de la página y permite reutilizar OCR y visión
        local sobre esa región.
        """
        rendered = self._ocr_processor.render_page(
            pdf_bytes=pdf_bytes,
            page_number=page_number,
        )
        try:
            scale = self._ocr_processor.dpi / 72.0
            x0, top, x1, bottom = bbox
            left = max(0, min(rendered.width - 1, round(x0 * scale)))
            upper = max(0, min(rendered.height - 1, round(top * scale)))
            right = max(left + 1, min(rendered.width, round(x1 * scale)))
            lower = max(upper + 1, min(rendered.height, round(bottom * scale)))

            cropped = rendered.crop((left, upper, right, lower)).convert("RGB")
            try:
                buffer = BytesIO()
                cropped.save(buffer, format="PNG")
                return buffer.getvalue(), cropped.width, cropped.height
            finally:
                cropped.close()
        finally:
            rendered.close()

    def _extract_page_structural_objects(
        self,
        *,
        page_number: int,
        reader_page: Any,
        plumber_page: pdfplumber.page.Page,
        warnings: list[str],
    ) -> list[PdfStructuralObject]:
        """Captura estructura PDF que no cabe en texto/tablas/imágenes."""
        objects: list[PdfStructuralObject] = []

        page_keys = tuple(
            sorted(
                str(key).lstrip("/")
                for key in getattr(reader_page, "keys", lambda: ())()
            )
        )

        objects.append(
            PdfStructuralObject(
                object_id=f"page-{page_number}-structure",
                object_type="page_structure",
                page_number=page_number,
                metadata={
                    "dictionary_keys": list(page_keys),
                    "rotation": int(
                        getattr(reader_page, "rotation", 0) or 0
                    ),
                    "mediabox": self._safe_box(reader_page.get("/MediaBox")),
                    "cropbox": self._safe_box(reader_page.get("/CropBox")),
                },
            )
        )

        try:
            contents = reader_page.get_contents()
            if contents is not None:
                raw = contents.get_data()
                objects.append(
                    PdfStructuralObject(
                        object_id=f"page-{page_number}-content-stream",
                        object_type="content_stream",
                        page_number=page_number,
                        byte_size=len(raw),
                        content_sha256=sha256(raw).hexdigest(),
                        metadata={
                            "stream_present": True,
                        },
                    )
                )
        except Exception as exc:
            warnings.append(
                f"Página {page_number}: no se pudo inventariar el content stream: {exc}"
            )

        try:
            resources = reader_page.get("/Resources")
            if resources is not None:
                resource_keys = tuple(
                    sorted(
                        str(key).lstrip("/")
                        for key in resources.keys()
                    )
                )
                xobjects = resources.get("/XObject") or {}
                xobject_summary = []
                try:
                    for key, value in xobjects.items():
                        resolved = value.get_object()
                        xobject_summary.append(
                            {
                                "name": str(key),
                                "subtype": str(
                                    resolved.get("/Subtype", "")
                                ).lstrip("/"),
                                "width": resolved.get("/Width"),
                                "height": resolved.get("/Height"),
                            }
                        )
                except Exception as exc:
                    warnings.append(
                        f"Página {page_number}: no se pudo inspeccionar XObject: {exc}"
                    )

                objects.append(
                    PdfStructuralObject(
                        object_id=f"page-{page_number}-resources",
                        object_type="resources",
                        page_number=page_number,
                        metadata={
                            "resource_keys": list(resource_keys),
                            "xobjects": xobject_summary,
                        },
                    )
                )
        except Exception as exc:
            warnings.append(
                f"Página {page_number}: no se pudieron inspeccionar recursos: {exc}"
            )

        # Anotaciones y enlaces.
        try:
            annotations = reader_page.get("/Annots") or []
            for index, annotation_ref in enumerate(annotations):
                annotation = annotation_ref.get_object()
                subtype = str(
                    annotation.get("/Subtype", "")
                ).lstrip("/")
                action = annotation.get("/A")
                uri = ""
                if action is not None:
                    uri = str(action.get("/URI", "") or "")

                objects.append(
                    PdfStructuralObject(
                        object_id=f"page-{page_number}-annotation-{index + 1}",
                        object_type="annotation",
                        page_number=page_number,
                        subtype=subtype,
                        text=str(
                            annotation.get("/Contents", "") or ""
                        ),
                        bbox=self._safe_box(annotation.get("/Rect")),
                        metadata={
                            "flags": self._safe_pdf_value(annotation.get("/F")),
                            "uri": uri,
                            "destination": self._safe_pdf_value(
                                annotation.get("/Dest")
                            ),
                            "field_name": str(
                                annotation.get("/T", "") or ""
                            ),
                        },
                    )
                )
        except Exception as exc:
            warnings.append(
                f"Página {page_number}: no se pudieron inspeccionar anotaciones: {exc}"
            )

        # Geometría vectorial que pdfplumber puede reconstruir.
        for kind, attr in (
            ("vector_line", "lines"),
            ("vector_rect", "rects"),
            ("vector_curve", "curves"),
        ):
            try:
                elements = getattr(plumber_page, attr, ()) or ()
                for index, element in enumerate(elements):
                    bbox = self._safe_geometry_box(element)
                    metadata = {
                        key: self._json_safe(value)
                        for key, value in element.items()
                        if key not in {"object_type"}
                    }
                    objects.append(
                        PdfStructuralObject(
                            object_id=(
                                f"page-{page_number}-{kind}-{index + 1}"
                            ),
                            object_type=kind,
                            page_number=page_number,
                            bbox=bbox,
                            metadata=metadata,
                        )
                    )
            except Exception as exc:
                warnings.append(
                    f"Página {page_number}: no se pudieron inspeccionar {attr}: {exc}"
                )

        return objects

    def _extract_document_structural_objects(
        self,
        *,
        reader: PdfReader,
        warnings: list[str],
    ) -> list[PdfStructuralObject]:
        objects: list[PdfStructuralObject] = []

        # Campos AcroForm.
        try:
            fields = reader.get_fields() or {}
            for index, (name, field_obj) in enumerate(fields.items(), start=1):
                field_data = field_obj or {}
                objects.append(
                    PdfStructuralObject(
                        object_id=f"form-field-{index}",
                        object_type="form_field",
                        name=str(name),
                        subtype=str(field_data.get("/FT", "")).lstrip("/"),
                        text=str(field_data.get("/V", "") or ""),
                        metadata={
                            "tooltip": str(field_data.get("/TU", "") or ""),
                            "mapping_name": str(field_data.get("/TM", "") or ""),
                            "flags": self._safe_pdf_value(field_data.get("/Ff")),
                        },
                    )
                )
        except Exception as exc:
            warnings.append(
                f"No se pudieron inspeccionar campos de formulario: {exc}"
            )

        # Adjuntos embebidos.
        try:
            attachments = getattr(reader, "attachments", None)
            if attachments:
                for index, (name, data) in enumerate(attachments.items(), start=1):
                    values = data if isinstance(data, (list, tuple)) else [data]
                    for occurrence, payload in enumerate(values, start=1):
                        payload_bytes = bytes(payload or b"")
                        objects.append(
                            PdfStructuralObject(
                                object_id=f"attachment-{index}-{occurrence}",
                                object_type="embedded_attachment",
                                name=str(name),
                                byte_size=len(payload_bytes),
                                content_sha256=(
                                    sha256(payload_bytes).hexdigest()
                                    if payload_bytes
                                    else ""
                                ),
                                metadata={
                                    "occurrence": occurrence,
                                },
                            )
                        )
        except Exception as exc:
            warnings.append(
                f"No se pudieron inspeccionar adjuntos embebidos: {exc}"
            )

        # Marcadores / outline.
        try:
            outline = getattr(reader, "outline", ()) or ()
            counter = [0]

            def walk(entries: Any, parent_id: str = "") -> None:
                for entry in entries:
                    if isinstance(entry, list):
                        walk(entry, parent_id)
                        continue
                    counter[0] += 1
                    title = str(
                        getattr(entry, "title", None)
                        or getattr(entry, "get", lambda *_: "")("/Title", "")
                        or entry
                    )
                    objects.append(
                        PdfStructuralObject(
                            object_id=f"outline-{counter[0]}",
                            object_type="outline",
                            text=title,
                            metadata={
                                "parent_outline_id": parent_id,
                            },
                        )
                    )
                    current = f"outline-{counter[0]}"
                    children = getattr(entry, "children", None)
                    if callable(children):
                        try:
                            walk(list(children()), current)
                        except Exception:
                            pass

            walk(outline)
        except Exception as exc:
            warnings.append(
                f"No se pudieron inspeccionar marcadores del PDF: {exc}"
            )

        # Etiquetas de página, versión e indicios globales.
        try:
            page_labels = getattr(reader, "page_labels", None)
            if page_labels:
                objects.append(
                    PdfStructuralObject(
                        object_id="document-page-labels",
                        object_type="page_labels",
                        metadata={
                            "labels": [str(label) for label in page_labels],
                        },
                    )
                )
        except Exception as exc:
            warnings.append(
                f"No se pudieron inspeccionar etiquetas de página: {exc}"
            )

        try:
            header = getattr(reader, "pdf_header", "")
            objects.append(
                PdfStructuralObject(
                    object_id="document-structure",
                    object_type="document_structure",
                    metadata={
                        "pdf_header": str(header),
                        "is_encrypted": bool(getattr(reader, "is_encrypted", False)),
                        "metadata_keys": [
                            str(key).lstrip("/")
                            for key in (reader.metadata or {}).keys()
                        ],
                    },
                )
            )
        except Exception as exc:
            warnings.append(
                f"No se pudo inspeccionar estructura global del PDF: {exc}"
            )

        return objects

    @staticmethod
    def _safe_box(value: Any) -> tuple[float, float, float, float] | None:
        try:
            if value is None or len(value) != 4:
                return None
            return tuple(float(item) for item in value)
        except Exception:
            return None

    @classmethod
    def _safe_pdf_value(cls, value: Any) -> Any:
        if value is None:
            return None
        try:
            resolved = value.get_object()
            if resolved is not value:
                return cls._safe_pdf_value(resolved)
        except Exception:
            resolved = value

        if isinstance(resolved, (str, int, float, bool)):
            return resolved
        if isinstance(resolved, (list, tuple)):
            return [cls._safe_pdf_value(item) for item in resolved[:20]]
        return str(resolved)

    @staticmethod
    def _safe_geometry_box(value: dict[str, Any]) -> tuple[float, float, float, float] | None:
        for keys in (("x0", "top", "x1", "bottom"), ("x0", "y0", "x1", "y1")):
            try:
                if all(key in value for key in keys):
                    return tuple(float(value[key]) for key in keys)
            except Exception:
                continue
        return None

    @staticmethod
    def _json_safe(value: Any) -> Any:
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, (list, tuple)):
            return [PDFDocumentProcessor._json_safe(item) for item in value[:20]]
        return str(value)

    @staticmethod
    def _build_page_capture_audit(
        *,
        page_number: int,
        native_text: str,
        text: str,
        text_blocks: list[PdfTextBlock],
        tables: list[PdfTable],
        semantic_tables: list[PdfSemanticTable],
        images: list[PdfImage],
        structural_objects: tuple[PdfStructuralObject, ...] | list[PdfStructuralObject],
        requires_ocr: bool,
        ocr_executed: bool,
        visual_ocr_attempted: bool,
        visual_ocr_complete: bool,
        visual_render_sha256: str,
        visual_understanding: dict[str, Any],
        ocr_blocks: tuple[PdfOcrBlock, ...],
        reading_order_count: int,
        warnings: list[str],
    ) -> dict[str, Any]:
        image_payload_missing = sum(1 for image in images if image.byte_size <= 0)
        image_ocr_failures = sum(
            1
            for image in images
            if image.ocr_attempted and not image.ocr_text.strip()
        )
        image_visual_failures = sum(
            1
            for image in images
            if str(image.visual_understanding.get("analysis_status", "")) == "failed"
        )
        visual_status = str(visual_understanding.get("analysis_status", "") or "")

        return {
            "status": "complete" if not warnings and visual_status != "failed" and visual_render_sha256 else "complete_with_warnings",
            "page_number": page_number,
            "layers": {
                "native_text": True,
                "text_blocks": True,
                "tables": True,
                "semantic_tables": True,
                "embedded_images": True,
                "page_render": bool(visual_render_sha256),
                "page_ocr_execution": (not requires_ocr) or ocr_executed,
                "embedded_image_ocr_execution": True,
                "visual_understanding_execution": visual_status in {"completed", ""},
                "reading_order": reading_order_count > 0 or not (text or images or tables or semantic_tables),
            },
            "counts": {
                "native_text_chars": len(native_text.strip()),
                "text_chars": len(text.strip()),
                "text_block_count": len(text_blocks),
                "ocr_block_count": len(ocr_blocks),
                "table_count": len(tables),
                "semantic_table_count": len(semantic_tables),
                "image_count": len(images),
                "image_payload_missing_count": image_payload_missing,
                "image_ocr_without_text_count": image_ocr_failures,
                "image_visual_failure_count": image_visual_failures,
                "structural_object_count": len(structural_objects),
                "reading_order_count": reading_order_count,
            },
            "recognition": {
                "ocr_executed": ocr_executed,
                "visual_ocr_attempted": visual_ocr_attempted,
                "visual_ocr_complete": visual_ocr_complete,
                "ocr_recognized_text": bool(text.strip()),
                "ocr_zero_text_is_not_capture_failure": True,
                "visual_understanding_status": visual_status or "not_recorded",
                "recognition_warnings": list(warnings),
            },
        }

    @classmethod
    def _build_document_capture_audit(
        cls,
        *,
        pages: list[PdfPageAnalysis],
        images: list[PdfImage],
        tables: list[PdfTable],
        semantic_tables: list[PdfSemanticTable],
        structural_objects: list[PdfStructuralObject],
        reading_order: tuple[PdfReadingEntry, ...],
        document_errors: list[str],
    ) -> dict[str, Any]:
        page_count = len(pages)
        successful_pages = sum(1 for page in pages if not page.errors)
        rendered_pages = sum(1 for page in pages if page.visual_render_sha256)
        visual_completed = sum(
            1
            for page in pages
            if str(page.visual_understanding.get("analysis_status", "")) == "completed"
        )
        page_audits = [dict(page.capture_audit) for page in pages]
        pages_with_warnings = sum(
            1 for page in pages if page.warnings
        )
        page_failures = sum(1 for page in pages if page.errors)
        image_payload_missing = sum(1 for image in images if image.byte_size <= 0)
        image_ocr_attempted = sum(1 for image in images if image.ocr_attempted)
        image_ocr_with_text = sum(1 for image in images if image.ocr_text.strip())
        recognition_gaps: list[dict[str, Any]] = []
        for page in pages:
            if page.ocr_executed and not page.ocr_text.strip():
                recognition_gaps.append({
                    "page_number": page.page_number,
                    "type": "page_ocr_no_text",
                    "severity": "recognition",
                })
            if page.ocr_executed and 0.0 < page.ocr_confidence < 0.55:
                recognition_gaps.append({
                    "page_number": page.page_number,
                    "type": "low_ocr_confidence",
                    "severity": "recognition",
                    "confidence": page.ocr_confidence,
                })
        for image in images:
            if image.ocr_attempted and not image.ocr_text.strip():
                recognition_gaps.append({
                    "page_number": image.page_number,
                    "image_id": image.image_id,
                    "type": "embedded_image_ocr_no_text",
                    "severity": "recognition",
                })
            if image.byte_size <= 0:
                recognition_gaps.append({
                    "page_number": image.page_number,
                    "image_id": image.image_id,
                    "type": "image_payload_unavailable",
                    "severity": "capture",
                })

        core_complete = (
            page_count > 0
            and successful_pages == page_count
            and rendered_pages == page_count
            and visual_completed == page_count
            and image_payload_missing == 0
            and not document_errors
        )
        status = "complete" if core_complete else "partial"
        return {
            "contract_version": "1.0",
            "status": status,
            "page_count": page_count,
            "processed_page_count": successful_pages,
            "rendered_page_count": rendered_pages,
            "visual_understanding_completed_page_count": visual_completed,
            "table_count": len(tables),
            "semantic_table_count": len(semantic_tables),
            "image_count": len(images),
            "image_ocr_attempted_count": image_ocr_attempted,
            "image_ocr_with_text_count": image_ocr_with_text,
            "image_payload_missing_count": image_payload_missing,
            "structural_object_count": len(structural_objects),
            "reading_order_entry_count": len(reading_order),
            "warning_page_count": pages_with_warnings,
            "error_page_count": page_failures,
            "recognition_gap_count": len(recognition_gaps),
            "recognition_gaps": recognition_gaps,
            "pages": page_audits,
            "interpretation": {
                "capture_complete": core_complete,
                "recognition_complete": len(recognition_gaps) == 0,
                "recognition_gaps_do_not_imply_missing_pdf_bytes": True,
                "text_recognition_is_not_the_same_as_content_capture": True,
            },
        }

    @staticmethod
    def _build_coverage_report(
        *,
        pages: list[PdfPageAnalysis],
        images: list[PdfImage],
        structural_objects: list[PdfStructuralObject],
        document_errors: list[str],
    ) -> dict[str, Any]:
        page_count = len(pages)
        processed_pages = sum(1 for page in pages if not page.errors)
        visual_pages = sum(
            1
            for page in pages
            if page.visual_render_sha256
        )
        visual_ocr_pages = sum(
            1
            for page in pages
            if page.visual_ocr_attempted and page.visual_ocr_complete
        )
        image_ocr_attempted = sum(
            1 for image in images if image.ocr_attempted
        )
        image_ocr_with_text = sum(
            1 for image in images if image.ocr_text.strip()
        )
        structural_counts: dict[str, int] = {}
        for item in structural_objects:
            structural_counts[item.object_type] = (
                structural_counts.get(item.object_type, 0) + 1
            )

        image_payload_unavailable = sum(
            1
            for image in images
            if image.byte_size <= 0
        )
        visual_understanding_attempted_pages = sum(
            1
            for page in pages
            if page.visual_understanding
        )
        visual_understanding_completed_pages = sum(
            1
            for page in pages
            if str(page.visual_understanding.get("analysis_status", "")) == "completed"
        )
        visual_understanding_failed_pages = sum(
            1
            for page in pages
            if str(page.visual_understanding.get("analysis_status", "")) == "failed"
        )
        low_confidence_ocr_pages = sum(
            1
            for page in pages
            if page.ocr_executed and 0.0 < page.ocr_confidence < 0.55
        )

        complete = (
            page_count > 0
            and processed_pages == page_count
            and visual_pages == page_count
            and visual_ocr_pages == page_count
            and visual_understanding_completed_pages == page_count
            and visual_understanding_failed_pages == 0
            and not document_errors
        )

        return {
            "status": "complete" if complete else "partial",
            "page_count": page_count,
            "processed_page_count": processed_pages,
            "native_text_page_count": sum(
                1 for page in pages if page.native_text.strip()
            ),
            "visual_capture_page_count": visual_pages,
            "visual_ocr_page_count": visual_ocr_pages,
            "embedded_image_count": len(images),
            "embedded_image_ocr_attempted": image_ocr_attempted,
            "embedded_image_ocr_with_text": image_ocr_with_text,
            "embedded_image_payload_unavailable_count": image_payload_unavailable,
            "visual_understanding_attempted_page_count": visual_understanding_attempted_pages,
            "visual_understanding_completed_page_count": visual_understanding_completed_pages,
            "visual_understanding_failed_page_count": visual_understanding_failed_pages,
            "visual_understanding_complete": (
                page_count > 0
                and visual_understanding_completed_pages == page_count
                and visual_understanding_failed_pages == 0
            ),
            "low_confidence_ocr_page_count": low_confidence_ocr_pages,
            "structural_object_count": len(structural_objects),
            "structural_object_counts": structural_counts,
            "document_error_count": len(document_errors),
        }

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
        