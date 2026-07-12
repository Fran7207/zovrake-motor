"""Enumeraciones del Reasoning Result Builder."""

from __future__ import annotations

from enum import Enum


class ReasoningResultBuildStatus(str, Enum):
    """Estado de la construcción del resultado."""

    BUILT = "built"
    PARTIAL = "partial"
    SKIPPED = "skipped"


class ReasoningResultBuilderStrategyType(str, Enum):
    """Estrategias de construcción del resultado."""

    ORGANIZED_REASONING_RESULT = "organized_reasoning_result"
