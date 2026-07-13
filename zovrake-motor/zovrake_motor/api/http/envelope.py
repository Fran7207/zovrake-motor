"""Sobre uniforme de respuestas HTTP — contrato REST v1."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from zovrake_motor.api.enums import PublicContractVersion
from zovrake_motor.api.models import PublicAnalysisResponse


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ApiErrorBody(BaseModel):
    code: str
    message: str
    recoverable: bool = True
    details: dict[str, Any] = Field(default_factory=dict)


class ApiResponseEnvelope(BaseModel):
    """
    Contrato uniforme de respuesta de la API oficial.

    Todas las respuestas REST utilizan esta estructura.
    """

    analysis_id: str | None = None
    status: str
    timestamp: datetime = Field(default_factory=utc_now)
    message: str
    success: bool
    result: dict[str, Any] | None = None
    error: ApiErrorBody | None = None
    contract_version: str = PublicContractVersion.V1.value

    @classmethod
    def from_public_response(cls, response: PublicAnalysisResponse) -> ApiResponseEnvelope:
        result_payload: dict[str, Any] | None = None
        if response.result is not None:
            result_payload = response.result.to_dict()
        error_payload: ApiErrorBody | None = None
        if response.error is not None:
            error_payload = ApiErrorBody(
                code=response.error.error_code.value,
                message=response.error.message,
                recoverable=response.error.recoverable,
                details=dict(response.error.details),
            )
        return cls(
            analysis_id=str(response.analysis_id),
            status=response.status.stage.value,
            message=response.status.message or response.status.processing_status,
            success=response.success,
            result=result_payload,
            error=error_payload,
            timestamp=response.occurred_at,
            contract_version=response.contract_version,
        )

    @classmethod
    def service_message(
        cls,
        *,
        status: str,
        message: str,
        success: bool,
        result: dict[str, Any] | None = None,
        error: ApiErrorBody | None = None,
        analysis_id: UUID | str | None = None,
    ) -> ApiResponseEnvelope:
        return cls(
            analysis_id=str(analysis_id) if analysis_id is not None else None,
            status=status,
            message=message,
            success=success,
            result=result,
            error=error,
        )
