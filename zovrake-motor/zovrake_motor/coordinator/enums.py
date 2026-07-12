"""Estados internos del Coordinator Central."""

from __future__ import annotations

from enum import Enum


class CoordinatorState(str, Enum):
    """Ciclo de vida del Coordinator — sin lógica de negocio."""

    INICIALIZADO = "inicializado"
    ESPERANDO_MODULOS = "esperando_modulos"
    PREPARADO = "preparado"
    COORDINANDO = "coordinando"
    FINALIZADO = "finalizado"
    ERROR_INTERNO = "error_interno"

    def is_terminal(self) -> bool:
        return self in {
            CoordinatorState.FINALIZADO,
            CoordinatorState.ERROR_INTERNO,
        }


class CoordinationPhase(str, Enum):
    """Fases del flujo de coordinación — preparado para orquestación futura."""

    SOLICITUD = "solicitud"
    INICIALIZACION = "inicializacion"
    COORDINACION = "coordinacion"
    PROCESAMIENTO = "procesamiento"
    FINALIZACION = "finalizacion"


class ModuleLifecycleState(str, Enum):
    """Ciclo de vida administrado por el Coordinator — sin lógica de negocio."""

    REGISTRADO = "registrado"
    INICIALIZADO = "inicializado"
    DISPONIBLE = "disponible"
    PREPARADO = "preparado"
    FINALIZADO = "finalizado"
