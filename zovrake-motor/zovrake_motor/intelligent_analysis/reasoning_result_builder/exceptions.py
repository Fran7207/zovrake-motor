"""Excepciones del Reasoning Result Builder."""


class ReasoningResultInputAccessError(Exception):
    """Error de acceso o validación de entradas del RRB."""


class ReasoningResultBuilderNotFoundError(Exception):
    """Constructor de resultados no registrado."""
