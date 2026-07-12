"""Enumeraciones del Service Classification Engine."""

from __future__ import annotations

from enum import Enum


class ServiceClassificationStatus(str, Enum):
    """Estado de la clasificación de servicios."""

    CLASSIFIED = "classified"
    SKIPPED = "skipped"
    FAILED = "failed"


class ServiceClassifierType(str, Enum):
    """Clasificadores especializados del SCE."""

    COMMERCIAL_CONDITION = "commercial_condition_service_classifier"
    OBSERVATION = "observation_service_classifier"
    TECHNICAL_ELEMENT = "technical_element_service_classifier"
