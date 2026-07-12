"""Contratos oficiales de la API Interna."""

from zovrake_motor.enterprise_integration.internal_api.contracts.base import (
    ContractEnvelope,
    InternalApiRequestBase,
    InternalApiResponseBase,
)
from zovrake_motor.enterprise_integration.internal_api.contracts.requests import (
    AnalysisResultQueryRequest,
    AnalysisStatusQueryRequest,
    CancelAnalysisRequest,
    StartAnalysisRequest,
    ValidateAnalysisRequest,
)
from zovrake_motor.enterprise_integration.internal_api.contracts.responses import (
    AnalysisResultResponse,
    AnalysisStatusResponse,
    CancelAnalysisResponse,
    InternalApiErrorResponse,
    StartAnalysisResponse,
    StructuredAnalysisResult,
    ValidateAnalysisResponse,
)
from zovrake_motor.enterprise_integration.internal_api.contracts.v1 import contract_snapshot

__all__ = [
    "AnalysisResultQueryRequest",
    "AnalysisResultResponse",
    "AnalysisStatusQueryRequest",
    "AnalysisStatusResponse",
    "CancelAnalysisRequest",
    "CancelAnalysisResponse",
    "ContractEnvelope",
    "InternalApiErrorResponse",
    "InternalApiRequestBase",
    "InternalApiResponseBase",
    "StartAnalysisRequest",
    "StartAnalysisResponse",
    "StructuredAnalysisResult",
    "ValidateAnalysisRequest",
    "ValidateAnalysisResponse",
    "contract_snapshot",
]
