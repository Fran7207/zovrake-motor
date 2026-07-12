"""Excepciones del Material Classification Engine."""

from __future__ import annotations


class MaterialClassificationError(Exception):
    """Error base del MCE."""


class ConceptCatalogAccessError(MaterialClassificationError):
    """El catálogo de conceptos del CAE no cumple el contrato de consumo."""


class MaterialClassifierNotFoundError(MaterialClassificationError):
    """Clasificador de materiales no registrado."""
