"""Excepciones del Document Recognition Engine."""

from __future__ import annotations


class RecognitionEngineError(Exception):
    """Error base del Document Recognition Engine."""


class RecognitionStrategyNotFoundError(RecognitionEngineError):
    """Estrategia de reconocimiento no registrada."""


class RecognitionExecutionError(RecognitionEngineError):
    """Error durante la ejecución del reconocimiento."""
