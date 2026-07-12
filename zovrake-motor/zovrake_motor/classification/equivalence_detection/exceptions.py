"""Excepciones del Equivalence Detection Engine."""


class EquivalenceDetectionError(Exception):
    """Error base del EDE."""


class NormalizedCatalogAccessError(EquivalenceDetectionError):
    """Error al acceder al catálogo de conceptos normalizados."""


class EquivalenceDetectorNotFoundError(EquivalenceDetectionError):
    """Detector no registrado en el EDE."""
