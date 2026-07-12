"""Enumeraciones del Document Validation Framework."""

from __future__ import annotations

from enum import Enum


class ValidationStatus(str, Enum):
    """Estado resultante de la validación documental."""

    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"


class ValidationIncidentType(str, Enum):
    """Tipos de incidencias detectables por el DVF."""

    EMPTY_FILE = "empty_file"
    CORRUPT_FILE = "corrupt_file"
    UNSUPPORTED_FORMAT = "unsupported_format"
    INACCESSIBLE_FILE = "inaccessible_file"
    INCOMPLETE_DOCUMENT = "incomplete_document"
    ILLEGIBLE_DOCUMENT = "illegible_document"
    INVALID_SIZE = "invalid_size"
    INCONSISTENT_STRUCTURE = "inconsistent_structure"


class DocumentQualityLevel(str, Enum):
    """Nivel preliminar de calidad documental."""

    UNKNOWN = "unknown"
    LOW = "low"
    ACCEPTABLE = "acceptable"
    HIGH = "high"


class ValidationSeverity(str, Enum):
    """Severidad de una incidencia o advertencia."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
