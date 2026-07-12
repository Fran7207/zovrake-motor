"""Excepciones del Recommendation Generation Engine."""


class RecommendationInputAccessError(Exception):
    """Error de acceso o validación de entradas del RGE."""


class RecommendationGeneratorNotFoundError(Exception):
    """Generador de recomendaciones no registrado."""
