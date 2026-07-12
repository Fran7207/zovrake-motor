"""Enumeraciones del Dynamic Column Builder."""

from __future__ import annotations

from enum import Enum


class ComparativeColumnBuildStatus(str, Enum):
    """Estado de la construcción de columnas dinámicas."""

    BUILT = "built"
    SKIPPED = "skipped"
    PARTIAL = "partial"


class ColumnDataType(str, Enum):
    """Tipos de dato soportados para columnas dinámicas."""

    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    SPECIFICATION = "specification"
    LIST = "list"


class ColumnBuilderStrategyType(str, Enum):
    """Estrategias de construcción de columnas."""

    STRUCTURE_ATTRIBUTE = "structure_attribute"
