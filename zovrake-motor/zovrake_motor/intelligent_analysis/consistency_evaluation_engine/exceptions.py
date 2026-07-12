"""Excepciones del Consistency Evaluation Engine."""


class EvidenceCatalogAccessError(Exception):
    """Error de acceso o validación al catálogo de evidencias del EAE."""


class ConsistencyEvaluatorNotFoundError(Exception):
    """Evaluador de consistencia no registrado."""
