"""Ciclo de vida y reglas de transición del Pipeline de Integración."""

from __future__ import annotations

from zovrake_motor.enterprise_integration.pio.enums import (
    IntegrationPipelinePhase,
    PipelineOrchestrationOperation,
)
from zovrake_motor.states.enums import MotorState


class IntegrationPipelineLifecycle:
    """
    Referencia determinística del Pipeline de Integración.

    Ninguna fase puede ejecutarse fuera del orden definido.
    """

    FULL_ANALYSIS_FLOW: tuple[IntegrationPipelinePhase, ...] = (
        IntegrationPipelinePhase.SOLICITUD_RECIBIDA,
        IntegrationPipelinePhase.VALIDACION_INICIADA,
        IntegrationPipelinePhase.SOLICITUD_ACEPTADA,
        IntegrationPipelinePhase.PROCESAMIENTO_INICIADO,
        IntegrationPipelinePhase.INVOCACION_MOTOR_PREPARADA,
        IntegrationPipelinePhase.PROCESAMIENTO_EN_EJECUCION,
        IntegrationPipelinePhase.RESULTADO_GENERADO,
        IntegrationPipelinePhase.RESULTADO_ENTREGADO,
        IntegrationPipelinePhase.PROCESO_FINALIZADO,
    )

    STATUS_QUERY_FLOW: tuple[IntegrationPipelinePhase, ...] = (
        IntegrationPipelinePhase.SOLICITUD_RECIBIDA,
        IntegrationPipelinePhase.VALIDACION_INICIADA,
        IntegrationPipelinePhase.SOLICITUD_ACEPTADA,
        IntegrationPipelinePhase.RESULTADO_ENTREGADO,
        IntegrationPipelinePhase.PROCESO_FINALIZADO,
    )

    RESULT_QUERY_FLOW: tuple[IntegrationPipelinePhase, ...] = (
        IntegrationPipelinePhase.SOLICITUD_RECIBIDA,
        IntegrationPipelinePhase.VALIDACION_INICIADA,
        IntegrationPipelinePhase.SOLICITUD_ACEPTADA,
        IntegrationPipelinePhase.RESULTADO_GENERADO,
        IntegrationPipelinePhase.RESULTADO_ENTREGADO,
        IntegrationPipelinePhase.PROCESO_FINALIZADO,
    )

    VALIDATION_FLOW: tuple[IntegrationPipelinePhase, ...] = (
        IntegrationPipelinePhase.SOLICITUD_RECIBIDA,
        IntegrationPipelinePhase.VALIDACION_INICIADA,
        IntegrationPipelinePhase.SOLICITUD_ACEPTADA,
        IntegrationPipelinePhase.PROCESO_FINALIZADO,
    )

    CANCEL_FLOW: tuple[IntegrationPipelinePhase, ...] = (
        IntegrationPipelinePhase.SOLICITUD_RECIBIDA,
        IntegrationPipelinePhase.ERROR_CONTROLADO,
        IntegrationPipelinePhase.PROCESO_FINALIZADO,
    )

    OPERATION_FLOWS: dict[PipelineOrchestrationOperation, tuple[IntegrationPipelinePhase, ...]] = {
        PipelineOrchestrationOperation.START_ANALYSIS: FULL_ANALYSIS_FLOW,
        PipelineOrchestrationOperation.QUERY_STATUS: STATUS_QUERY_FLOW,
        PipelineOrchestrationOperation.QUERY_RESULT: RESULT_QUERY_FLOW,
        PipelineOrchestrationOperation.VALIDATE_REQUEST: VALIDATION_FLOW,
        PipelineOrchestrationOperation.CANCEL_ANALYSIS: CANCEL_FLOW,
    }

    PHASE_MOTOR_STATE_MAP: dict[IntegrationPipelinePhase, MotorState | None] = {
        IntegrationPipelinePhase.SOLICITUD_RECIBIDA: MotorState.INICIALIZADO,
        IntegrationPipelinePhase.VALIDACION_INICIADA: MotorState.VALIDANDO_INFORMACION,
        IntegrationPipelinePhase.SOLICITUD_ACEPTADA: MotorState.INFORMACION_RECIBIDA,
        IntegrationPipelinePhase.PROCESAMIENTO_INICIADO: MotorState.PREPARANDO_PROCESAMIENTO,
        IntegrationPipelinePhase.INVOCACION_MOTOR_PREPARADA: MotorState.PROCESAMIENTO_PENDIENTE,
        IntegrationPipelinePhase.PROCESAMIENTO_EN_EJECUCION: MotorState.PROCESANDO,
        IntegrationPipelinePhase.RESULTADO_GENERADO: MotorState.PROCESAMIENTO_COMPLETADO,
        IntegrationPipelinePhase.RESULTADO_ENTREGADO: MotorState.PROCESAMIENTO_COMPLETADO,
        IntegrationPipelinePhase.PROCESO_FINALIZADO: MotorState.FINALIZADO,
        IntegrationPipelinePhase.ERROR_CONTROLADO: MotorState.ERROR_VALIDACION,
    }

    @classmethod
    def flow_for(cls, operation: PipelineOrchestrationOperation) -> tuple[IntegrationPipelinePhase, ...]:
        return cls.OPERATION_FLOWS[operation]

    @classmethod
    def next_phase(
        cls,
        operation: PipelineOrchestrationOperation,
        current: IntegrationPipelinePhase | None,
    ) -> IntegrationPipelinePhase | None:
        flow = cls.flow_for(operation)
        if current is None:
            return flow[0] if flow else None
        try:
            index = flow.index(current)
        except ValueError:
            return None
        if index + 1 >= len(flow):
            return None
        return flow[index + 1]

    @classmethod
    def is_valid_transition(
        cls,
        operation: PipelineOrchestrationOperation,
        from_phase: IntegrationPipelinePhase | None,
        to_phase: IntegrationPipelinePhase,
    ) -> bool:
        if to_phase == IntegrationPipelinePhase.ERROR_CONTROLADO:
            return True
        expected = cls.next_phase(operation, from_phase)
        return expected == to_phase

    @classmethod
    def motor_state_for_phase(cls, phase: IntegrationPipelinePhase) -> MotorState | None:
        return cls.PHASE_MOTOR_STATE_MAP.get(phase)
