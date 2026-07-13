"""Enumeraciones de la API de Integración Pública — Prompt Maestro 9."""

from __future__ import annotations

from enum import Enum


class PublicContractVersion(str, Enum):
    """Versiones del contrato público ERP ↔ API."""

    V1 = "v1"


class IntegrationApiOperation(str, Enum):
    """Operaciones oficiales de la API de Integración."""

    START_ANALYSIS = "start_analysis"
    QUERY_STATUS = "query_status"
    QUERY_RESULT = "query_result"
    CANCEL_ANALYSIS = "cancel_analysis"
    VALIDATE_REQUEST = "validate_request"


class IntegrationApiLifecycleStage(str, Enum):
    """Etapas del ciclo de vida del análisis ERP ↔ Motor."""

    ANALYSIS_CREATED = "analysis_created"
    DOCUMENTS_RECEIVED = "documents_received"
    VALIDATION = "validation"
    SENT_TO_MOTOR = "sent_to_motor"
    PROCESSING = "processing"
    RESULT_GENERATED = "result_generated"
    RETURNED_TO_ERP = "returned_to_erp"
    VISUAL_UPDATE = "visual_update"
    FAILED = "failed"
    CANCELLED = "cancelled"


class IntegrationApiErrorCode(str, Enum):
    """Errores controlados de la API pública — no detienen el resto del sistema."""

    INVALID_DOCUMENT = "invalid_document"
    UNREADABLE_FILE = "unreadable_file"
    UNSUPPORTED_FORMAT = "unsupported_format"
    INCOMPLETE_REQUEST = "incomplete_request"
    INTERNAL_ERROR = "internal_error"
    PROCESSING_CANCELLED = "processing_cancelled"
    VALIDATION_FAILED = "validation_failed"
    NOT_FOUND = "not_found"
    CONTRACT_VIOLATION = "contract_violation"
