"""Enumeraciones del Material Classification Engine."""

from __future__ import annotations

from enum import Enum


class MaterialClassificationStatus(str, Enum):
    """Estado de la clasificación de materiales."""

    CLASSIFIED = "classified"
    SKIPPED = "skipped"
    FAILED = "failed"


class MaterialClassifierType(str, Enum):
    """Clasificadores especializados del MCE."""

    ITEM = "item_material_classifier"
    PARTIDA = "partida_material_classifier"
