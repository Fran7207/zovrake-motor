"""Ciclo de vida conceptual de estados — sin reglas automáticas."""

from __future__ import annotations

from zovrake_motor.states.enums import MotorState


class StateLifecycle:
    """
    Referencia arquitectónica del ciclo de vida de estados.

    No ejecuta transiciones automáticas ni reglas de negocio en esta etapa.
    """

    OFFICIAL_STATES: tuple[MotorState, ...] = MotorState.official_states()

    CONCEPTUAL_FLOW: tuple[MotorState, ...] = (
        MotorState.INICIALIZADO,
        MotorState.ESPERANDO_INFORMACION,
        MotorState.VALIDANDO_INFORMACION,
        MotorState.INFORMACION_RECIBIDA,
        MotorState.PREPARANDO_PROCESAMIENTO,
        MotorState.PROCESAMIENTO_PENDIENTE,
        MotorState.PROCESANDO,
        MotorState.PROCESAMIENTO_COMPLETADO,
        MotorState.FINALIZADO,
    )

    ERROR_STATES: tuple[MotorState, ...] = (
        MotorState.ERROR_VALIDACION,
        MotorState.ERROR_INTERNO,
    )

    def is_official(self, state: MotorState) -> bool:
        return state in self.OFFICIAL_STATES

    def validate_state(self, state: MotorState) -> None:
        if not self.is_official(state):
            raise ValueError(f"Estado no oficial: {state.value}")
