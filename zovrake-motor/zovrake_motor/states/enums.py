"""Estados oficiales del ciclo de vida de procesos del Motor."""

from __future__ import annotations

from enum import Enum


class MotorState(str, Enum):
    """Estados oficiales del Motor Inteligente — única fuente de verdad."""

    INICIALIZADO = "inicializado"
    ESPERANDO_INFORMACION = "esperando_informacion"
    VALIDANDO_INFORMACION = "validando_informacion"
    INFORMACION_RECIBIDA = "informacion_recibida"
    PREPARANDO_PROCESAMIENTO = "preparando_procesamiento"
    PROCESAMIENTO_PENDIENTE = "procesamiento_pendiente"
    PROCESANDO = "procesando"
    PROCESAMIENTO_COMPLETADO = "procesamiento_completado"
    FINALIZADO = "finalizado"
    ERROR_VALIDACION = "error_validacion"
    ERROR_INTERNO = "error_interno"

    @classmethod
    def official_states(cls) -> tuple[MotorState, ...]:
        return (
            cls.INICIALIZADO,
            cls.ESPERANDO_INFORMACION,
            cls.VALIDANDO_INFORMACION,
            cls.INFORMACION_RECIBIDA,
            cls.PREPARANDO_PROCESAMIENTO,
            cls.PROCESAMIENTO_PENDIENTE,
            cls.PROCESANDO,
            cls.PROCESAMIENTO_COMPLETADO,
            cls.FINALIZADO,
            cls.ERROR_VALIDACION,
            cls.ERROR_INTERNO,
        )

    def is_terminal(self) -> bool:
        return self in {
            MotorState.PROCESAMIENTO_COMPLETADO,
            MotorState.FINALIZADO,
            MotorState.ERROR_VALIDACION,
            MotorState.ERROR_INTERNO,
        }

    def is_error(self) -> bool:
        return self in {
            MotorState.ERROR_VALIDACION,
            MotorState.ERROR_INTERNO,
        }
