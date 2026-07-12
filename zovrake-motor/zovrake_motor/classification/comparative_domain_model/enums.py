"""Enumeraciones del Comparative Domain Model Builder."""

from __future__ import annotations

from enum import Enum


class ComparativeDomainModelBuildStatus(str, Enum):
    """Estado de la construcción del modelo comparativo."""

    BUILT = "built"
    SKIPPED = "skipped"
    PARTIAL = "partial"


class DomainModelBuilderStrategyType(str, Enum):
    """Estrategias de construcción del modelo comparativo."""

    GROUP_CONTEXT_AGGREGATION = "group_context_aggregation"
