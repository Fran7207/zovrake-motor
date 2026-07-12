"""Enumeraciones del Comparative Model Builder."""

from __future__ import annotations

from enum import Enum


class ComparativeModelBuildStatus(str, Enum):
    """Estado de construcción del Modelo Comparativo Definitivo."""

    BUILT = "built"
    PARTIAL = "partial"
    SKIPPED = "skipped"


class ModelBuilderStrategyType(str, Enum):
    """Tipos de estrategia de construcción de modelos."""

    COMPARATIVE_TABLE = "comparative_table"
