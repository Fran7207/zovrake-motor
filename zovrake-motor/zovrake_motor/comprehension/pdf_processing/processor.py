"""Procesador documental profundo para archivos PDF."""

from __future__ import annotations

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
    PdfPageAnalysis,
    PdfTable,
    PdfTextBlock,
    ProcessedPdfDocument,
)


class PDFDocumentProcessor:
    """
    Procesa físicamente un PDF y construye una representación documental
    estructurada para las siguientes etapas de comprensión.

    Esta clase NO realiza todavía:
    - OCR;
    - clasificación de materiales;
    - comparación de proveedores;
    - selección de ganador;
    - análisis inteligente.

    Su responsabilidad es comprender la estructura física del PDF.
    """

    OCR_TEXT_THRESHOLD = 20

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
        reader: PdfReader,
        plumber_pdf: pdfplumber.PDF,
    ) -> ProcessedPdfDocument:
        pages: list[PdfPageAnalysis] = []
        all_tables: list[PdfTable] = []
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
                )

                pages.append(page_result)
                all_tables.extend(page_result.tables)
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

        if ocr_required:
            document_warnings.append(
                "Una o más páginas requieren OCR. "
                "La ejecución OCR se implementará en la siguiente etapa."
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
            images=tuple(all_images),
            pdf_metadata=metadata,
            ocr_required=ocr_required,
            extraction_method="native_pdf",
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

        images = self._extract_images(
            page_number,
            reader_page,
            plumber_page,
            warnings,
        )

        has_text = bool(text.strip())
        has_tables = bool(tables)
        has_images = bool(images)

        requires_ocr = self._requires_ocr(
            has_text=has_text,
            has_images=has_images,
            text_length=len(text.strip()),
        )

        return PdfPageAnalysis(
            page_number=page_number,
            width=width,
            height=height,
            text=text,
            text_blocks=tuple(text_blocks),
            tables=tuple(tables),
            images=tuple(images),
            has_text=has_text,
            has_tables=has_tables,
            has_images=has_images,
            requires_ocr=requires_ocr,
            warnings=tuple(warnings),
        )

    @classmethod
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

        La ejecución real de OCR pertenece a una etapa posterior.
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
                    tables.append(
                        PdfTable(
                            table_id=(
                                f"page-{page_number}-"
                                f"table-{index + 1}"
                            ),
                            page_number=page_number,
                            rows=tuple(rows),
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