"""API Interna del Motor Inteligente — Implementación 8.2."""

from zovrake_motor.enterprise_integration.internal_api.api import InternalIntegrationApi
from zovrake_motor.enterprise_integration.internal_api.context import InternalApiContext
from zovrake_motor.enterprise_integration.internal_api.contracts import (
    AnalysisResultQueryRequest,
    AnalysisResultResponse,
    AnalysisStatusQueryRequest,
    AnalysisStatusResponse,
    CancelAnalysisRequest,
    CancelAnalysisResponse,
    InternalApiErrorResponse,
    StartAnalysisRequest,
    StartAnalysisResponse,
    StructuredAnalysisResult,
    ValidateAnalysisRequest,
    ValidateAnalysisResponse,
    contract_snapshot,
)
from zovrake_motor.enterprise_integration.internal_api.enums import (
    AnalysisProcessingStatus,
    ContractVersionId,
    InternalApiErrorCode,
    InternalApiOperation,
)
from zovrake_motor.enterprise_integration.internal_api.services import (
    AnalysisRequestService,
    AnalysisRequestServicePort,
    AnalysisResultService,
    AnalysisResultServicePort,
    AnalysisStatusService,
    AnalysisStatusServicePort,
    ErrorResponseService,
    ErrorResponseServicePort,
    ValidationService,
    ValidationServicePort,
)
from zovrake_motor.enterprise_integration.internal_api.validation import (
    StructuralValidationResult,
    StructuralValidator,
)
from zovrake_motor.enterprise_integration.internal_api.versioning import ContractVersionRegistry

__all__ = [
    "AnalysisProcessingStatus",
    "AnalysisRequestService",
    "AnalysisRequestServicePort",
    "AnalysisResultQueryRequest",
    "AnalysisResultResponse",
    "AnalysisResultService",
    "AnalysisResultServicePort",
    "AnalysisStatusQueryRequest",
    "AnalysisStatusResponse",
    "AnalysisStatusService",
    "AnalysisStatusServicePort",
    "CancelAnalysisRequest",
    "CancelAnalysisResponse",
    "ContractVersionId",
    "ContractVersionRegistry",
    "ErrorResponseService",
    "ErrorResponseServicePort",
    "InternalApiContext",
    "InternalApiErrorCode",
    "InternalApiOperation",
    "InternalIntegrationApi",
    "StartAnalysisRequest",
    "StartAnalysisResponse",
    "StructuralAnalysisResult",
    "StructuralValidationResult",
    "StructuralValidator",
    "ValidateAnalysisRequest",
    "ValidateAnalysisResponse",
    "ValidationService",
    "ValidationServicePort",
    "contract_snapshot",
]
