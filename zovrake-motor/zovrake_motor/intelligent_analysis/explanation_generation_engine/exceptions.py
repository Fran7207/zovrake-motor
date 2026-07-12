"""Excepciones del Explanation Generation Engine."""


class ExplanationInputAccessError(Exception):
    """Error de acceso o validación de entradas del EGE."""


class ExplanationGeneratorNotFoundError(Exception):
    """Generador de explicaciones no registrado."""
