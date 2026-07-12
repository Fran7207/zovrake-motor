"""Enumeraciones del Sistema de Gestión de Eventos."""

from __future__ import annotations

from enum import Enum


class EventType(str, Enum):
    """Tipos oficiales de eventos internos del Motor."""

    CREATED = "created"
    REGISTERED = "registered"
    STATE_CHANGE = "state_change"
    COORDINATION = "coordination"
    MODULE = "module"
    PIPELINE = "pipeline"
    SYSTEM = "system"
    FINALIZED = "finalized"


class EventCategory(str, Enum):
    """Categoría funcional del evento — clasificación transversal."""

    RECEPTION = "reception"
    VALIDATION = "validation"
    DOCUMENT = "document"
    CONTEXT = "context"
    STATE = "state"
    COORDINATION = "coordination"
    PROCESSING = "processing"
    COMMUNICATION = "communication"
    SYSTEM = "system"


class EventSeverity(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class EventLifecycleState(str, Enum):
    """Ciclo de vida administrativo de un evento."""

    CREATED = "created"
    REGISTERED = "registered"
    FINALIZED = "finalized"

    def is_terminal(self) -> bool:
        return self == EventLifecycleState.FINALIZED
