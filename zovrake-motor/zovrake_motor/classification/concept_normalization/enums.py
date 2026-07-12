"""Enumeraciones del Concept Normalization Engine."""

from __future__ import annotations

from enum import Enum


class ConceptNormalizationStatus(str, Enum):
    """Estado de la normalización conceptual."""

    NORMALIZED = "normalized"
    SKIPPED = "skipped"
    PARTIAL = "partial"


class ConceptNormalizerType(str, Enum):
    """Tipos de normalizadores del CNE."""

    MATERIAL = "material"
    PARTIDA = "partida"
    SERVICE = "service"
    TECHNICAL_ELEMENT = "technical_element"
    COMMERCIAL_ELEMENT = "commercial_element"
    SPECIFICATION = "specification"


class NormalizedConceptCategory(str, Enum):
    """Categoría de origen del concepto normalizado."""

    MATERIAL = "material"
    SERVICE = "service"
    SPECIFICATION = "specification"
