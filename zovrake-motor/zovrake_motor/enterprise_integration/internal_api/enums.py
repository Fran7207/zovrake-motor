"""Enumeraciones de la API Interna del Motor Inteligente."""

from __future__ import annotations

from enum import Enum


class InternalApiOperation(str, Enum):
    """Operaciones oficiales de la API Interna."""

    START_ANALYSIS = "start_analysis"
    QUERY_STATUS = "query_status"
    QUERY_RESULT = "query_result"
    CANCEL_ANALYSIS = "cancel_analysis"
    VALIDATE_REQUEST = "validate_request"


class AnalysisProcessingStatus(str, Enum):
    """Estado de procesamiento expuesto por la API Interna — sin nuevos estados del motor."""

    PREPARED = "prepared"
    ACCEPTED = "accepted"
    NOT_EXECUTED = "not_executed"
    PENDING = "pending"
    CANCELLED = "cancelled"
    UNAVAILABLE = "unavailable"


class InternalApiErrorCode(str, Enum):
    """Códigos de error controlados de la API Interna."""

    CONTRACT_VERSION_UNSUPPORTED = "contract_version_unsupported"
    STRUCTURAL_VALIDATION_FAILED = "structural_validation_failed"
    REQUIRED_FIELD_MISSING = "required_field_missing"
    INVALID_FIELD_TYPE = "invalid_field_type"
    PROCESS_NOT_FOUND = "process_not_found"
    OPERATION_NOT_EXECUTED = "operation_not_executed"
    API_NOT_INITIALIZED = "api_not_initialized"
    COORDINATOR_REQUIRED = "coordinator_required"
    PIO_ORCHESTRATION_REQUIRED = "pio_orchestration_required"


class ContractVersionId(str, Enum):
    """Versiones de contrato preparadas — solo v1 activa en 8.2."""

    V1 = "v1"
    V2 = "v2"
