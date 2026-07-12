"""Excepciones del administrador de módulos del Coordinator."""


class ModuleNotFoundError(Exception):
    """El módulo solicitado no está registrado en el Coordinator."""


class ModuleNotAvailableError(Exception):
    """El módulo existe pero no está disponible para coordinación."""
