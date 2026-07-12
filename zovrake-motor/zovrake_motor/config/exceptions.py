"""Excepciones del sistema de configuración centralizada."""


class ConfigurationError(Exception):
    """La configuración cargada no cumple la validación estructural básica."""
