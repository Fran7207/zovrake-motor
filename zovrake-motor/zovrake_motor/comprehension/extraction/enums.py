"""Enumeraciones del Content Extraction Engine."""

from __future__ import annotations

from enum import Enum


class ExtractorType(str, Enum):
    """Tipos de extractores especializados del CEE."""

    TEXT = "text"
    TABLES = "tables"
    METADATA = "metadata"
    HEADERS = "headers"
    FOOTERS = "footers"
    LISTS = "lists"
    EMBEDDED_IMAGES = "embedded_images"
    STRUCTURAL_ELEMENTS = "structural_elements"


class ExtractionIncidentSeverity(str, Enum):
    """Severidad de incidencias durante la extracción."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
