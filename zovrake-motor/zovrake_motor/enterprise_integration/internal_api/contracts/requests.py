"""Contratos de solicitud de la API Interna."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from zovrake_motor.enterprise_integration.internal_api.contracts.base import InternalApiRequestBase
from zovrake_motor.enterprise_integration.internal_api.enums import InternalApiOperation


@dataclass(frozen=True)
class StartAnalysisRequest(InternalApiRequestBase):
    """Contrato para iniciar un análisis documental real."""

    operation: InternalApiOperation = InternalApiOperation.START_ANALYSIS
    document_ids: tuple[str, ...] = field(default_factory=tuple)
    document_references: tuple[dict[str, Any], ...] = field(
        default_factory=tuple
    )
    analysis_scope: str = "full"

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.base_dict(),
            "operation": self.operation.value,
            "document_ids": list(self.document_ids),
            "document_references": list(self.document_references),
            "analysis_scope": self.analysis_scope,
        }


@dataclass(frozen=True)
class AnalysisStatusQueryRequest(InternalApiRequestBase):
    """Contrato para consultar estado del análisis."""

    operation: InternalApiOperation = InternalApiOperation.QUERY_STATUS

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.base_dict(),
            "operation": self.operation.value,
        }


@dataclass(frozen=True)
class AnalysisResultQueryRequest(InternalApiRequestBase):
    """Contrato para consultar resultado del análisis."""

    operation: InternalApiOperation = InternalApiOperation.QUERY_RESULT
    result_reference_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.base_dict(),
            "operation": self.operation.value,
            "result_reference_id": self.result_reference_id,
        }


@dataclass(frozen=True)
class CancelAnalysisRequest(InternalApiRequestBase):
    """Contrato para cancelar procesamiento — preparado para implementación futura."""

    operation: InternalApiOperation = InternalApiOperation.CANCEL_ANALYSIS
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.base_dict(),
            "operation": self.operation.value,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class ValidateAnalysisRequest(InternalApiRequestBase):
    """Contrato para validar estructura de una solicitud de análisis."""

    operation: InternalApiOperation = InternalApiOperation.VALIDATE_REQUEST
    target_operation: InternalApiOperation = InternalApiOperation.START_ANALYSIS
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.base_dict(),
            "operation": self.operation.value,
            "target_operation": self.target_operation.value,
            "payload": self.payload,
        }


InternalApiRequest = (
    StartAnalysisRequest
    | AnalysisStatusQueryRequest
    | AnalysisResultQueryRequest
    | CancelAnalysisRequest
    | ValidateAnalysisRequest
)
