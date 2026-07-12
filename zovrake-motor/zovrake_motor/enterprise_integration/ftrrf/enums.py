"""Enumeraciones del Fault Tolerance, Retry & Recovery Framework."""

from __future__ import annotations

from enum import Enum


class ErrorCategory(str, Enum):
    """Clasificación oficial de errores del Módulo de Integración."""

    VALIDATION = "error_validacion"
    DOCUMENTAL = "error_documental"
    COMMUNICATION = "error_comunicacion"
    PROCESSING = "error_procesamiento"
    TEMPORARY = "error_temporal"
    PERMANENT = "error_permanente"
    SYSTEM_INTERNAL = "error_interno_sistema"


class ErrorSeverity(str, Enum):
    """Severidad del error registrado."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class RecoveryStatus(str, Enum):
    """Estado de recuperación de un error registrado."""

    PENDING = "pendiente"
    IN_PROGRESS = "en_progreso"
    RETRY_SCHEDULED = "reintento_programado"
    RECOVERED = "recuperado"
    CANCELLED = "cancelado"
    FAILED = "fallido"


class RecoveryStage(str, Enum):
    """Etapas del ciclo de vida de resiliencia — observabilidad del FTRRF."""

    FAULT_DETECTED = "fallo_detectado"
    RECOVERY_STARTED = "recuperacion_iniciada"
    RECOVERY_COMPLETED = "recuperacion_completada"
    RETRY_SCHEDULED = "reintento_programado"
    PROCESS_CANCELLED = "proceso_cancelado"
    FINALIZED_WITH_ERROR = "finalizacion_por_error"


class RecoveryDecision(str, Enum):
    """Decisión de continuidad tomada por el FTRRF."""

    RETRY = "retry"
    RECOVER = "recover"
    CANCEL = "cancel"
    TERMINAL_FAILURE = "terminal_failure"


class RetryStrategy(str, Enum):
    """Estrategias de reintento preparadas — sin backoff avanzado todavía."""

    NONE = "none"
    IMMEDIATE = "immediate"
    FIXED_INTERVAL = "fixed_interval"
