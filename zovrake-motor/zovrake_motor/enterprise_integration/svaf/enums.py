"""Enumeraciones del Security, Validation & Audit Framework."""

from __future__ import annotations

from enum import Enum


class ValidationStage(str, Enum):
    """Etapas del ciclo de validación SVAF."""

    VALIDATION_STARTED = "validacion_iniciada"
    VALIDATION_APPROVED = "validacion_aprobada"
    VALIDATION_REJECTED = "validacion_rechazada"
    AUDIT_RECORDED = "auditoria_registrada"


class ValidationDirection(str, Enum):
    """Dirección del flujo validado."""

    ERP_TO_MOTOR = "erp_to_motor"
    MOTOR_TO_ERP = "motor_to_erp"
    PIPELINE_ENTRY = "pipeline_entry"


class IntegrityIssueType(str, Enum):
    """Tipos de problemas de integridad detectados."""

    INCOMPLETE_MESSAGE = "mensaje_incompleto"
    INVALID_STRUCTURE = "estructura_invalida"
    DUPLICATE_MESSAGE = "mensaje_duplicado"
    INVALID_CONTRACT = "contrato_invalido"
    INCONSISTENT_RESPONSE = "respuesta_inconsistente"
    COMMUNICATION_ERROR = "error_comunicacion"


class AuditOperationResult(str, Enum):
    """Resultado de una operación auditada."""

    SUCCESS = "success"
    REJECTED = "rejected"
    ERROR = "error"
