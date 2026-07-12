"""Catálogo de formatos documentales y mapeo a adaptadores."""

from __future__ import annotations

from typing import Any

from zovrake_motor.comprehension.adapters.enums import DocumentFormatType


class FormatCatalog:
    """
    Catálogo extensible de formatos documentales.

    Relaciona tipos documentales con adaptadores del Document Adapter Framework.
    """

    ADAPTER_MAPPING: dict[DocumentFormatType, str] = {
        DocumentFormatType.PDF: "pdf_adapter",
        DocumentFormatType.WORD: "word_adapter",
        DocumentFormatType.EXCEL: "excel_adapter",
        DocumentFormatType.IMAGE: "image_adapter",
    }

    EXTENSION_MAPPING: dict[str, DocumentFormatType] = {
        ".pdf": DocumentFormatType.PDF,
        ".docx": DocumentFormatType.WORD,
        ".doc": DocumentFormatType.WORD,
        ".xlsx": DocumentFormatType.EXCEL,
        ".xls": DocumentFormatType.EXCEL,
        ".png": DocumentFormatType.IMAGE,
        ".jpg": DocumentFormatType.IMAGE,
        ".jpeg": DocumentFormatType.IMAGE,
        ".tiff": DocumentFormatType.IMAGE,
        ".bmp": DocumentFormatType.IMAGE,
    }

    MIME_MAPPING: dict[str, DocumentFormatType] = {
        "application/pdf": DocumentFormatType.PDF,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": DocumentFormatType.WORD,
        "application/msword": DocumentFormatType.WORD,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": DocumentFormatType.EXCEL,
        "application/vnd.ms-excel": DocumentFormatType.EXCEL,
        "image/png": DocumentFormatType.IMAGE,
        "image/jpeg": DocumentFormatType.IMAGE,
        "image/tiff": DocumentFormatType.IMAGE,
        "image/bmp": DocumentFormatType.IMAGE,
    }

    MAGIC_MAPPING: dict[str, DocumentFormatType] = {
        "%PDF": DocumentFormatType.PDF,
        "PK": DocumentFormatType.WORD,
        "D0CF11E0": DocumentFormatType.WORD,
        "89504E47": DocumentFormatType.IMAGE,
        "FFD8FF": DocumentFormatType.IMAGE,
    }

    @classmethod
    def suggested_adapter(cls, format_type: DocumentFormatType) -> str | None:
        return cls.ADAPTER_MAPPING.get(format_type)

    @classmethod
    def format_from_extension(cls, extension: str) -> DocumentFormatType | None:
        return cls.EXTENSION_MAPPING.get(extension.lower())

    @classmethod
    def format_from_mime(cls, mime_type: str) -> DocumentFormatType | None:
        return cls.MIME_MAPPING.get(mime_type.lower().strip())

    @classmethod
    def format_from_magic(cls, signature: str) -> DocumentFormatType | None:
        normalized = signature.strip().upper()
        for prefix, format_type in cls.MAGIC_MAPPING.items():
            if normalized.startswith(prefix):
                return format_type
        return None

    @classmethod
    def snapshot(cls) -> dict[str, Any]:
        return {
            "supported_formats": [fmt.value for fmt in cls.ADAPTER_MAPPING],
            "adapter_mapping": {k.value: v for k, v in cls.ADAPTER_MAPPING.items()},
            "extensions": list(cls.EXTENSION_MAPPING.keys()),
            "mime_types": list(cls.MIME_MAPPING.keys()),
        }
