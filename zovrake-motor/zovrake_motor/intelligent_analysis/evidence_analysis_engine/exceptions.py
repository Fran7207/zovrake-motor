"""Excepciones del Evidence Analysis Engine."""


class DefinitiveCatalogAccessError(Exception):
    """Error de acceso o validación al Modelo Comparativo Definitivo."""


class EvidenceAnalyzerNotFoundError(Exception):
    """Analizador de evidencias no registrado."""
