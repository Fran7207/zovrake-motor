"""Excepciones del Document Adapter Framework."""

from __future__ import annotations


class AdapterFrameworkError(Exception):
    """Error base del Framework de Adaptadores Documentales."""


class AdapterNotFoundError(AdapterFrameworkError):
    """Adaptador no registrado para el formato solicitado."""


class AdapterResolutionError(AdapterFrameworkError):
    """No fue posible resolver un adaptador para la solicitud."""
