"""Excepciones del Sistema de Gestión de Estados."""


class StateManagementError(Exception):
    """Error estructural en la gestión de estados."""


class ProcessNotFoundError(StateManagementError):
    """El proceso solicitado no existe en el sistema de estados."""
