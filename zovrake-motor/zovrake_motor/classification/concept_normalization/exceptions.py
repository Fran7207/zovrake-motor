"""Excepciones del Concept Normalization Engine."""


class ConceptNormalizationError(Exception):
    """Error base del CNE."""


class ClassificationCatalogAccessError(ConceptNormalizationError):
    """Error al acceder a catálogos de materiales o servicios."""


class ConceptNormalizerNotFoundError(ConceptNormalizationError):
    """Normalizador no registrado en el CNE."""
