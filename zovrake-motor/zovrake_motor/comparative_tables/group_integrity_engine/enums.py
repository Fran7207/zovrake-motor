"""Enumeraciones del Group Integrity Engine."""

from __future__ import annotations

from enum import Enum


class GroupIntegrityValidationStatus(str, Enum):
    """Estado global de la validación de integridad."""

    VALID = "valid"
    INVALID = "invalid"
    PARTIAL = "partial"
    SKIPPED = "skipped"


class IntegrityFindingCategory(str, Enum):
    """Categoría de un hallazgo de integridad."""

    GROUP = "group"
    COLUMN = "column"
    ROW = "row"
    PROVIDER = "provider"
    GENERAL = "general"


class IntegrityFindingSeverity(str, Enum):
    """Severidad de un hallazgo de integridad."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class IntegrityValidatorStrategyType(str, Enum):
    """Estrategias de validación de integridad."""

    COMPARATIVE_TABLE = "comparative_table"
