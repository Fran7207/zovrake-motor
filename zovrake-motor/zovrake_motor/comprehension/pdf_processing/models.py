"""Modelos de procesamiento documental profundo de PDF."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PdfImage:
    """Imagen detectada dentro de una página PDF."""

    image_id: str
    page_number: int
    width: int | None = None
    height: int | None = None
    image_format: str = ""
    byte_size: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "image_id": self.image_id,
            "page_number": self.page_number,
            "width": self.width,
            "height": self.height,
            "image_format": self.image_format,
            "byte_size": self.byte_size,
        }


@dataclass(frozen=True)
class PdfTableColumn:
    """Columna semántica identificada dentro de una tabla PDF."""

    key: str
    label: str
    index: int
    confidence: float = 0.0
    evidence: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label,
            "index": self.index,
            "confidence": self.confidence,
            "evidence": list(self.evidence),
        }


@dataclass(frozen=True)
class PdfSemanticTable:
    """
    Representación semántica de una tabla PDF.

    La estructura se descubre a partir del contenido real del documento.
    No representa una plantilla fija de cotización.
    """

    table_id: str
    columns: tuple[PdfTableColumn, ...] = ()
    rows: tuple[dict[str, Any], ...] = ()
    confidence: float = 0.0
    source_table_id: str = ""
    source_page_number: int | None = None
    evidence: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "table_id": self.table_id,
            "columns": [
                column.to_dict()
                for column in self.columns
            ],
            "rows": [
                dict(row)
                for row in self.rows
            ],
            "confidence": self.confidence,
            "source_table_id": self.source_table_id,
            "source_page_number": self.source_page_number,
            "evidence": list(self.evidence),
        }


@dataclass(frozen=True)
class PdfTable:
    """Tabla física detectada dentro de una página PDF."""

    table_id: str
    page_number: int
    rows: tuple[tuple[str, ...], ...] = ()
    bbox: tuple[float, float, float, float] | None = None
    semantic: PdfSemanticTable | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "table_id": self.table_id,
            "page_number": self.page_number,
            "rows": [list(row) for row in self.rows],
            "bbox": (
                list(self.bbox)
                if self.bbox is not None
                else None
            ),
            "semantic": (
                self.semantic.to_dict()
                if self.semantic is not None
                else None
            ),
        }


@dataclass(frozen=True)
class PdfTextBlock:
    """Bloque de texto detectado en una página."""

    block_id: str
    page_number: int
    text: str
    bbox: tuple[float, float, float, float] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "block_id": self.block_id,
            "page_number": self.page_number,
            "text": self.text,
            "bbox": (
                list(self.bbox)
                if self.bbox is not None
                else None
            ),
        }


@dataclass(frozen=True)
class PdfOcrBlock:
    """
    Bloque de texto obtenido mediante OCR.

    La información OCR se mantiene separada de los bloques nativos
    para conservar la procedencia del contenido.
    """

    block_id: str
    page_number: int
    text: str
    bbox: tuple[float, float, float, float] | None = None
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "block_id": self.block_id,
            "page_number": self.page_number,
            "text": self.text,
            "bbox": (
                list(self.bbox)
                if self.bbox is not None
                else None
            ),
            "confidence": self.confidence,
            "source": "ocr",
        }


@dataclass(frozen=True)
class PdfPageAnalysis:
    """Análisis físico y documental de una página PDF."""

    page_number: int
    width: float
    height: float
    text: str
    text_blocks: tuple[PdfTextBlock, ...] = ()
    tables: tuple[PdfTable, ...] = ()
    semantic_tables: tuple[PdfSemanticTable, ...] = ()
    images: tuple[PdfImage, ...] = ()
    has_text: bool = False
    has_tables: bool = False
    has_images: bool = False
    requires_ocr: bool = False

    # Información específica de OCR.
    ocr_executed: bool = False
    ocr_text: str = ""
    ocr_blocks: tuple[PdfOcrBlock, ...] = ()
    ocr_confidence: float = 0.0
    ocr_language: str = ""
    ocr_dpi: int | None = None

    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "page_number": self.page_number,
            "width": self.width,
            "height": self.height,
            "text": self.text,
            "text_blocks": [
                block.to_dict()
                for block in self.text_blocks
            ],
            "tables": [
                table.to_dict()
                for table in self.tables
            ],
            "semantic_tables": [
                table.to_dict()
                for table in self.semantic_tables
            ],
            "images": [
                image.to_dict()
                for image in self.images
            ],
            "has_text": self.has_text,
            "has_tables": self.has_tables,
            "has_images": self.has_images,
            "requires_ocr": self.requires_ocr,
            "ocr_executed": self.ocr_executed,
            "ocr_text": self.ocr_text,
            "ocr_blocks": [
                block.to_dict()
                for block in self.ocr_blocks
            ],
            "ocr_confidence": self.ocr_confidence,
            "ocr_language": self.ocr_language,
            "ocr_dpi": self.ocr_dpi,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }


@dataclass(frozen=True)
class ProcessedPdfDocument:
    """Representación documental estructurada producida por el procesador PDF."""

    document_id: str
    file_name: str
    page_count: int
    pages: tuple[PdfPageAnalysis, ...]
    full_text: str
    tables: tuple[PdfTable, ...]
    semantic_tables: tuple[PdfSemanticTable, ...] = ()
    images: tuple[PdfImage, ...] = ()
    pdf_metadata: dict[str, Any] = field(default_factory=dict)

    # Estado global de OCR.
    ocr_required: bool = False
    ocr_executed: bool = False
    ocr_pages_executed: tuple[int, ...] = ()
    ocr_confidence: float = 0.0
    ocr_language: str = ""
    ocr_dpi: int | None = None

    extraction_method: str = "native_pdf"
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()

    @property
    def has_text(self) -> bool:
        return bool(self.full_text.strip())

    @property
    def has_tables(self) -> bool:
        return bool(self.tables)

    @property
    def has_images(self) -> bool:
        return bool(self.images)

    @property
    def successfully_processed(self) -> bool:
        return self.page_count > 0 and not self.errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "file_name": self.file_name,
            "page_count": self.page_count,
            "pages": [
                page.to_dict()
                for page in self.pages
            ],
            "full_text": self.full_text,
            "tables": [
                table.to_dict()
                for table in self.tables
            ],
            "semantic_tables": [
                table.to_dict()
                for table in self.semantic_tables
            ],
            "images": [
                image.to_dict()
                for image in self.images
            ],
            "pdf_metadata": self.pdf_metadata,
            "ocr_required": self.ocr_required,
            "ocr_executed": self.ocr_executed,
            "ocr_pages_executed": list(
                self.ocr_pages_executed
            ),
            "ocr_confidence": self.ocr_confidence,
            "ocr_language": self.ocr_language,
            "ocr_dpi": self.ocr_dpi,
            "extraction_method": self.extraction_method,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "has_text": self.has_text,
            "has_tables": self.has_tables,
            "has_images": self.has_images,
            "successfully_processed": self.successfully_processed,
        }