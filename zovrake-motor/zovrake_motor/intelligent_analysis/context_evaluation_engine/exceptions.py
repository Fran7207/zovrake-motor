"""Excepciones del Context Evaluation Engine."""


class ContextInputAccessError(Exception):
    """Error de acceso o validación a las entradas del CxEE."""


class ContextEvaluatorNotFoundError(Exception):
    """Evaluador contextual no registrado."""
