"""Enumeraciones del Pipeline Integration Orchestrator."""

from __future__ import annotations

from enum import Enum


class IntegrationPipelinePhase(str, Enum):
    """Fases del Pipeline de Integración — orquestación PIO, no estados del Motor."""

    SOLICITUD_RECIBIDA = "solicitud_recibida"
    VALIDACION_INICIADA = "validacion_iniciada"
    SOLICITUD_ACEPTADA = "solicitud_aceptada"
    PROCESAMIENTO_INICIADO = "procesamiento_iniciado"
    INVOCACION_MOTOR_PREPARADA = "invocacion_motor_preparada"
    PROCESAMIENTO_EN_EJECUCION = "procesamiento_en_ejecucion"
    RESULTADO_GENERADO = "resultado_generado"
    RESULTADO_ENTREGADO = "resultado_entregado"
    PROCESO_FINALIZADO = "proceso_finalizado"
    ERROR_CONTROLADO = "error_controlado"


class PipelineOrchestrationOperation(str, Enum):
    """Operaciones orquestadas por el PIO."""

    START_ANALYSIS = "start_analysis"
    QUERY_STATUS = "query_status"
    QUERY_RESULT = "query_result"
    CANCEL_ANALYSIS = "cancel_analysis"
    VALIDATE_REQUEST = "validate_request"
