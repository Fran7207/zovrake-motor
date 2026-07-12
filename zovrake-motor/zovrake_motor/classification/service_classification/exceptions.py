"""Excepciones del Service Classification Engine."""

from __future__ import annotations


class ServiceClassificationError(Exception):
    """Error base del SCE."""


class ConceptCatalogAccessError(ServiceClassificationError):
    """El catálogo de conceptos del CAE no cumple el contrato de consumo."""


class ServiceClassifierNotFoundError(ServiceClassificationError):
    """Clasificador de servicios no registrado."""
