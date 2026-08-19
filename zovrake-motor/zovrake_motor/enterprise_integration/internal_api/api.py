"""
API Interna del Motor Inteligente — contrato oficial ERP ↔ Motor.

Punto de entrada interno; todas las solicitudes deben enrutarse
exclusivamente a través del Enterprise Integration Coordinator.
"""

from __future__ import annotations

from typing import Any

from zovrake_motor.enterprise_integration.internal_api.context import InternalApiContext
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
    ValidateAnalysisResponse,
)
from zovrake_motor.enterprise_integration.internal_api.contracts.v1 import contract_snapshot
from zovrake_motor.enterprise_integration.internal_api.enums import (
    AnalysisProcessingStatus,
    InternalApiErrorCode,
    InternalApiOperation,
)
from zovrake_motor.enterprise_integration.internal_api.services.analysis_request_service import (
    AnalysisRequestService,
)
from zovrake_motor.enterprise_integration.internal_api.services.analysis_result_service import (
    AnalysisResultService,
)
from zovrake_motor.enterprise_integration.internal_api.services.analysis_status_service import (
    AnalysisStatusService,
)
from zovrake_motor.enterprise_integration.internal_api.services.error_response_service import (
    ErrorResponseService,
)
from zovrake_motor.enterprise_integration.internal_api.services.validation_service import (
    ValidationService,
)
from zovrake_motor.enterprise_integration.internal_api.versioning import ContractVersionRegistry


class InternalIntegrationApi:
    """
    API Interna del Motor Inteligente.

    Define contratos, interfaces y servicios de comunicación.
    No expone HTTP ni endpoints públicos.
    """

    def __init__(self, *, context: InternalApiContext) -> None:
        self._context = context
        self._error_service = ErrorResponseService()
        self._analysis_request_service = AnalysisRequestService(context=context)
        self._analysis_status_service = AnalysisStatusService(context=context)
        self._analysis_result_service = AnalysisResultService(context=context)
        self._validation_service = ValidationService(context=context)
        self._initialized = False

    @property
    def context(self) -> InternalApiContext:
        return self._context

    @property
    def analysis_request_service(self) -> AnalysisRequestService:
        return self._analysis_request_service

    @property
    def analysis_status_service(self) -> AnalysisStatusService:
        return self._analysis_status_service

    @property
    def analysis_result_service(self) -> AnalysisResultService:
        return self._analysis_result_service

    @property
    def validation_service(self) -> ValidationService:
        return self._validation_service

    @property
    def error_response_service(self) -> ErrorResponseService:
        return self._error_service

    def initialize(self) -> None:
        self._context.initialize()
        self._initialized = True

    def bind_result_registry(self, result_registry) -> None:
        """Conecta el registro de resultados ejecutados por ``motor_runtime``."""
        self._analysis_result_service.bind_result_registry(result_registry)
        self._analysis_status_service.bind_result_registry(result_registry)

    def is_ready(self) -> bool:
        return self._initialized and self._context.is_initialized

    def start_analysis(
        self,
        request: StartAnalysisRequest,
    ) -> StartAnalysisResponse | InternalApiErrorResponse:
        if not self.is_ready():
            return self._not_initialized_error(request.process_id)
        return self._analysis_request_service.start_analysis(request)

    def query_status(
        self,
        request: AnalysisStatusQueryRequest,
    ) -> AnalysisStatusResponse | InternalApiErrorResponse:
        if not self.is_ready():
            return self._not_initialized_error(request.process_id)
        return self._analysis_status_service.query_status(request)

    def query_result(
        self,
        request: AnalysisResultQueryRequest,
    ) -> AnalysisResultResponse | InternalApiErrorResponse:
        if not self.is_ready():
            return self._not_initialized_error(request.process_id)
        return self._analysis_result_service.query_result(request)

    def cancel_analysis(
        self,
        request: CancelAnalysisRequest,
    ) -> CancelAnalysisResponse | InternalApiErrorResponse:
        if not self.is_ready():
            return self._not_initialized_error(request.process_id)
        return CancelAnalysisResponse(
            process_id=request.process_id,
            success=True,
            message="Cancelación preparada — sin ejecución en esta etapa",
            contract_version=request.contract_version,
            processing_status=AnalysisProcessingStatus.CANCELLED,
            executed=False,
            metadata={"reason": request.reason},
        )

    def validate_request(
        self,
        request: ValidateAnalysisRequest,
    ) -> ValidateAnalysisResponse | InternalApiErrorResponse:
        if not self.is_ready():
            return self._not_initialized_error(request.process_id)
        return self._validation_service.validate_request(request)

    def _not_initialized_error(self, process_id) -> InternalApiErrorResponse:
        return InternalApiErrorResponse(
            error_code=InternalApiErrorCode.API_NOT_INITIALIZED,
            message="API Interna no inicializada",
            process_id=process_id,
        )

    def contract_catalog(self) -> dict[str, Any]:
        return {
            "versioning": ContractVersionRegistry.snapshot(),
            "v1": contract_snapshot(),
            "operations": [operation.value for operation in InternalApiOperation],
        }

    def snapshot(self) -> dict[str, Any]:
        settings = self._context.settings()
        return {
            "initialized": self._initialized,
            "ready": self.is_ready(),
            "enabled": settings.enabled,
            "prepared": settings.prepared,
            "active_contract_version": settings.active_contract_version,
            "contract_catalog": self.contract_catalog(),
            "context": self._context.snapshot(),
        }
