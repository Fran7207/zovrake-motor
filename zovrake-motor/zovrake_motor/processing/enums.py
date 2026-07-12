"""Enumeraciones del Pipeline Interno del Motor Inteligente."""

from __future__ import annotations

from enum import Enum


class PipelineStageType(str, Enum):
    """Etapas oficiales del recorrido interno de una solicitud."""

    RECEPCION = "recepcion"
    VALIDACION = "validacion"
    PREPARACION = "preparacion"
    COORDINACION = "coordinacion"
    PROCESAMIENTO = "procesamiento"
    RESPUESTA = "respuesta"
    FINALIZACION = "finalizacion"


class PipelineExecutionState(str, Enum):
    """Estado de ejecución estructural del Pipeline."""

    PENDIENTE = "pendiente"
    EN_CURSO = "en_curso"
    COMPLETADA = "completada"
    DETENIDA = "detenida"
    FINALIZADA = "finalizada"
    ERROR = "error"

    def is_terminal(self) -> bool:
        return self in {
            PipelineExecutionState.COMPLETADA,
            PipelineExecutionState.DETENIDA,
            PipelineExecutionState.FINALIZADA,
            PipelineExecutionState.ERROR,
        }
