"""Excepciones del Classification Quality Framework."""


class ClassificationQualityError(Exception):
    """Error base del CQF."""


class ComparativeDomainModelCatalogAccessError(ClassificationQualityError):
    """Error al acceder al catálogo del modelo comparativo."""


class QualityValidatorNotFoundError(ClassificationQualityError):
    """Validador de calidad no registrado."""
