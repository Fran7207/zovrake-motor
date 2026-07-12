"""Enumeraciones del Comparative Structure Engine."""

from __future__ import annotations

from enum import Enum


class ComparativeTableStructureStatus(str, Enum):
    """Estado de la estructura base del cuadro comparativo."""

    STRUCTURED = "structured"
    SKIPPED = "skipped"
    PARTIAL = "partial"


class StructureBuilderStrategyType(str, Enum):
    """Estrategias de construcción de estructuras comparativas."""

    DOMAIN_MODEL_GROUP = "domain_model_group"
