"""Enumeraciones del Document Adapter Framework."""

from __future__ import annotations

from enum import Enum


class DocumentFormatType(str, Enum):
    """Formatos documentales soportados por el Framework de Adaptadores."""

    PDF = "pdf"
    WORD = "docx"
    EXCEL = "xlsx"
    IMAGE = "image"

    @classmethod
    def from_value(cls, value: str) -> DocumentFormatType | None:
        normalized = value.strip().lower()
        for item in cls:
            if item.value == normalized:
                return item
        return None
