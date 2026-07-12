"""Contratos de respuesta de la API Interna."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from zovrake_motor.enterprise_integration.internal_api.contracts.base import (
    InternalApiResponseBase,
    utc_now,
)
from zovrake_motor.enterprise_integration.internal_api.enums import (
    AnalysisProcessingStatus,
    InternalApiErrorCode,
    InternalApiOperation,
)


@dataclass(frozen=True)
class StructuredAnalysisResult:
    """Resultado estructurado preparatorio — sin datos reales en 8.2."""

    result_reference_id: str
    catalog_id: str = ""
    prepared: bool = True
    executed: bool = False
    source_data_preserved: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "result_reference_id": self.result_reference_id,
            "catalog_id": self.catalog_id,
            "prepared": self.prepared,
            "executed": self.executed,
            "source_data_preserved": self.source_data_preserved,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class StartAnalysisResponse(InternalApiResponseBase):
    """Respuesta a solicitud de inicio de análisis."""

    operation: InternalApiOperation = InternalApiOperation.START_ANALYSIS
    processing_status: AnalysisProcessingStatus = AnalysisProcessingStatus.ACCEPTED
    executed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.base_dict(),
            "operation": self.operation.value,
            "processing_status": self.processing_status.value,
            "executed": self.executed,
        }


@dataclass(frozen=True)
class AnalysisStatusResponse(InternalApiResponseBase):
    """Respuesta a consulta de estado."""

    operation: InternalApiOperation = InternalApiOperation.QUERY_STATUS
    processing_status: AnalysisProcessingStatus = AnalysisProcessingStatus.NOT_EXECUTED
    motor_state: str | None = None
    executed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.base_dict(),
            "operation": self.operation.value,
            "processing_status": self.processing_status.value,
            "motor_state": self.motor_state,
            "executed": self.executed,
        }


@dataclass(frozen=True)
class AnalysisResultResponse(InternalApiResponseBase):
    """Respuesta a consulta de resultado."""

    operation: InternalApiOperation = InternalApiOperation.QUERY_RESULT
    processing_status: AnalysisProcessingStatus = AnalysisProcessingStatus.NOT_EXECUTED
    result: StructuredAnalysisResult | None = None
    executed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.base_dict(),
            "operation": self.operation.value,
            "processing_status": self.processing_status.value,
            "result": self.result.to_dict() if self.result is not None else None,
            "executed": self.executed,
        }


@dataclass(frozen=True)
class CancelAnalysisResponse(InternalApiResponseBase):
    """Respuesta a solicitud de cancelación — preparada para futuro."""

    operation: InternalApiOperation = InternalApiOperation.CANCEL_ANALYSIS
    processing_status: AnalysisProcessingStatus = AnalysisProcessingStatus.CANCELLED
    executed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.base_dict(),
            "operation": self.operation.value,
            "processing_status": self.processing_status.value,
            "executed": self.executed,
        }


@dataclass(frozen=True)
class ValidateAnalysisResponse(InternalApiResponseBase):
    """Respuesta a validación estructural."""

    operation: InternalApiOperation = InternalApiOperation.VALIDATE_REQUEST
    valid: bool = True
    validation_errors: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.base_dict(),
            "operation": self.operation.value,
            "valid": self.valid,
            "validation_errors": list(self.validation_errors),
        }


@dataclass(frozen=True)
class InternalApiErrorResponse:
    """Error controlado de la API Interna."""

    error_code: InternalApiErrorCode
    message: str
    process_id: UUID | None = None
    contract_version: str = "v1"
    contract_name: str = "InternalIntegrationApi"
    occurred_at: datetime = field(default_factory=utc_now)
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return False

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": False,
            "error_code": self.error_code.value,
            "message": self.message,
            "process_id": str(self.process_id) if self.process_id is not None else None,
            "contract_version": self.contract_version,
            "contract_name": self.contract_name,
            "occurred_at": self.occurred_at.isoformat(),
            "details": self.details,
        }
