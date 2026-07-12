"""Enumeraciones del Asynchronous Processing & Queue Manager."""

from __future__ import annotations

from enum import Enum


class ApqmProcessingStage(str, Enum):
    """Etapas del ciclo de vida de procesamiento asíncrono — cola lógica APQM."""

    REQUEST_RECEIVED = "solicitud_recibida"
    QUEUED = "solicitud_en_cola"
    ASSIGNED = "solicitud_asignada"
    PROCESSING_STARTED = "procesamiento_iniciado"
    PROCESSING_IN_EXECUTION = "procesamiento_en_ejecucion"
    PROCESSING_COMPLETED = "procesamiento_completado"
    PROCESSING_CANCELLED = "procesamiento_cancelado"
    CONTROLLED_ERROR = "error_controlado"


class ApqmQueueOperation(str, Enum):
    """Operaciones de cola soportadas."""

    ENQUEUE = "enqueue"
    ASSIGN = "assign"
    EXECUTE = "execute"
    COMPLETE = "complete"
    CANCEL = "cancel"
    ERROR = "error"
