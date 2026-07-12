"""Enumeraciones del Context Association Engine."""

from __future__ import annotations

from enum import Enum


class ContextAssociationStatus(str, Enum):
    """Estado de la asociación de contexto."""

    ASSOCIATED = "associated"
    SKIPPED = "skipped"
    PARTIAL = "partial"


class ContextAssociatorStrategyType(str, Enum):
    """Estrategias de asociación de contexto."""

    UNIFORM_GROUP_CONTEXT = "uniform_group_context"
