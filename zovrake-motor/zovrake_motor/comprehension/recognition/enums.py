"""Enumeraciones del Document Recognition Engine."""

from __future__ import annotations

from enum import Enum


class RecognitionStrategyType(str, Enum):
    """Estrategias de reconocimiento documental."""

    EXTENSION = "extension"
    MIME_TYPE = "mime_type"
    METADATA = "metadata"
    MAGIC_NUMBER = "magic_number"


class RecognitionConfidenceLevel(str, Enum):
    """Nivel de confianza del reconocimiento."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    @classmethod
    def from_score(cls, score: float) -> RecognitionConfidenceLevel:
        if score >= 0.85:
            return cls.HIGH
        if score >= 0.55:
            return cls.MEDIUM
        return cls.LOW
