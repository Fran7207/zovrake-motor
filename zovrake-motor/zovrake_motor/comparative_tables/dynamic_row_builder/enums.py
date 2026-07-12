"""Enumeraciones del Dynamic Row Builder."""

from __future__ import annotations

from enum import Enum


class ComparativeRowBuildStatus(str, Enum):
    """Estado de la construcción de filas dinámicas."""

    BUILT = "built"
    SKIPPED = "skipped"
    PARTIAL = "partial"


class RowBuilderStrategyType(str, Enum):
    """Estrategias de construcción de filas."""

    PROVIDER_ROW = "provider_row"
