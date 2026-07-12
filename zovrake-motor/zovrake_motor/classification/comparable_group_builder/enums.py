"""Enumeraciones del Comparable Group Builder."""

from __future__ import annotations

from enum import Enum


class ComparableGroupBuildStatus(str, Enum):
    """Estado de la construcción de grupos comparables."""

    BUILT = "built"
    SKIPPED = "skipped"
    PARTIAL = "partial"


class ComparableGroupType(str, Enum):
    """Tipo de Grupo Comparable."""

    MATERIAL = "material"
    SERVICE = "service"


class GroupBuilderStrategyType(str, Enum):
    """Estrategias de construcción de grupos."""

    EQUIVALENCE_CLUSTER = "equivalence_cluster"
