"""Excepciones del Sistema de Gestión de Eventos."""


class EventManagementError(Exception):
    """Error estructural en la gestión de eventos."""


class EventNotFoundError(EventManagementError):
    """El evento solicitado no existe en el sistema."""


class ProcessEventsNotFoundError(EventManagementError):
    """No existe historial de eventos para el proceso solicitado."""
