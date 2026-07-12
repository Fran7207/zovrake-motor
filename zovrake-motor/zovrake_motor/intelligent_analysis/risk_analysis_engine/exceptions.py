"""Excepciones del Risk Analysis Engine."""


class AnalysisInputAccessError(Exception):
    """Error de acceso o validación a las entradas del EAE o CEE."""


class RiskAnalyzerNotFoundError(Exception):
    """Analizador de riesgos no registrado."""
