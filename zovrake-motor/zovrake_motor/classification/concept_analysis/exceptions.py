"""Excepciones del Concept Analysis Engine."""

from __future__ import annotations


class ConceptAnalysisError(Exception):
    """Error base del CAE."""


class InternalModelAccessError(ConceptAnalysisError):
    """El modelo documental interno no cumple el contrato de consumo."""


class ConceptDetectorNotFoundError(ConceptAnalysisError):
    """Detector de conceptos no registrado."""
