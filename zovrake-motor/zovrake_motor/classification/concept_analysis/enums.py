"""Enumeraciones del Concept Analysis Engine."""

from __future__ import annotations

from enum import Enum


class ConceptKind(str, Enum):
    """
    Tipo de concepto identificado — sin clasificación material/servicio.

    Los conceptos permanecen como candidatos hasta las etapas posteriores.
    """

    ITEM = "item"
    PARTIDA = "partida"
    COMMERCIAL_ELEMENT = "commercial_element"
    TECHNICAL_ELEMENT = "technical_element"
    COMMERCIAL_CONDITION = "commercial_condition"
    OBSERVATION = "observation"


class ConceptAnalysisStatus(str, Enum):
    """Estado del análisis de conceptos."""

    IDENTIFIED = "identified"
    SKIPPED = "skipped"
    FAILED = "failed"


class ConceptDetectorType(str, Enum):
    """Detectores especializados del CAE."""

    ITEM = "item_detector"
    TECHNICAL = "technical_detector"
    COMMERCIAL = "commercial_detector"
    CONDITION = "condition_detector"
    OBSERVATION = "observation_detector"
