"""Excepciones del Comparative Quality Framework."""


class ComparativeQualityError(Exception):
    """Error base del CQF."""


class ComparativeQualityInputAccessError(ComparativeQualityError):
    """Error al acceder a los insumos de auditoría de calidad."""


class ComparativeQualityValidatorNotFoundError(ComparativeQualityError):
    """Auditor de calidad no registrado."""
