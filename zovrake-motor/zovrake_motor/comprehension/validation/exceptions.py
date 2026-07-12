"""Excepciones del Document Validation Framework."""

from __future__ import annotations


class ValidationFrameworkError(Exception):
    """Error base del Document Validation Framework."""


class ValidationRuleNotFoundError(ValidationFrameworkError):
    """Regla de validación no registrada."""


class ValidationExecutionError(ValidationFrameworkError):
    """Error durante la ejecución de validación."""
