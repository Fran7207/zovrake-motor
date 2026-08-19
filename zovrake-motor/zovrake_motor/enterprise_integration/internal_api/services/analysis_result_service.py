"""Servicio de consulta de resultados de análisis."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from zovrake_motor.enterprise_integration.internal_api.context import InternalApiContext
from zovrake_motor.enterprise_integration.internal_api.contracts.requests import (
    AnalysisResultQueryRequest,
)
from zovrake_motor.enterprise_integration.internal_api.contracts.responses import (
    AnalysisResultResponse,
    InternalApiErrorResponse,
    StructuredAnalysisResult,
)
from zovrake_motor.enterprise_integration.internal_api.enums import AnalysisProcessingStatus
from zovrake_motor.enterprise_integration.internal_api.integration_events import (
    InternalApiEventRecorder,
)
from zovrake_motor.enterprise_integration.internal_api.services.error_response_service import (
    ErrorResponseService,
)
from zovrake_motor.enterprise_integration.internal_api.services.ports import (
    AnalysisResultServicePort,
)
from zovrake_motor.enterprise_integration.internal_api.validation.structural_validator import (
    StructuralValidationResult,
    StructuralValidator,
)

if TYPE_CHECKING:
    from zovrake_motor.motor_runtime.result_registry import AnalysisResultRegistry


class AnalysisResultService(AnalysisResultServicePort):
    """Consulta resultado estructurado — entrega datos reales cuando el Motor ya ejecutó."""

    def __init__(
        self,
        *,
        context: InternalApiContext,
        validator: StructuralValidator | None = None,
        error_service: ErrorResponseService | None = None,
        event_recorder: InternalApiEventRecorder | None = None,
        result_registry: AnalysisResultRegistry | None = None,
    ) -> None:
        self._context = context
        self._validator = validator or StructuralValidator()
        self._error_service = error_service or ErrorResponseService()
        self._event_recorder = event_recorder or InternalApiEventRecorder(context)
        self._result_registry = result_registry

    def bind_result_registry(self, result_registry: AnalysisResultRegistry | None) -> None:
        self._result_registry = result_registry

    def query_result(
        self,
        request: AnalysisResultQueryRequest,
    ) -> AnalysisResultResponse | InternalApiErrorResponse:
        if self._context.settings().structural_validation_enabled:
            validation = self._validator.validate_result_query(request)
        else:
            validation = StructuralValidationResult(valid=True)

        if not validation.valid:
            error = self._error_service.from_validation_errors(
                process_id=request.process_id,
                errors=validation.errors,
            )
            self._event_recorder.record_request_rejected(request.process_id, error.message)
            return error

        reference_id = request.result_reference_id or f"result-{request.process_id}"
        stored = None
        if self._result_registry is not None:
            stored = self._result_registry.get(request.process_id)

        if stored is not None and stored.executed:
            result = StructuredAnalysisResult(
                result_reference_id=reference_id,
                catalog_id=stored.catalog_id,
                prepared=True,
                executed=True,
                source_data_preserved=True,
                metadata=stored.to_structured_metadata(),
            )
            response = AnalysisResultResponse(
                process_id=request.process_id,
                success=True,
                message=stored.message,
                contract_version=request.contract_version,
                processing_status=AnalysisProcessingStatus.ACCEPTED,
                result=result,
                executed=True,
                metadata={
                    "codigo_req": stored.codigo_req or request.codigo_req,
                    "executed": True,
                    "documents_processed": len(stored.documents_processed),
                },
            )
            self._event_recorder.record_response_prepared(
                request.process_id,
                operation="query_result",
                success=True,
            )
            return response

        result = StructuredAnalysisResult(
            result_reference_id=reference_id,
            prepared=True,
            executed=False,
            metadata={"query_prepared": True},
        )

        response = AnalysisResultResponse(
            process_id=request.process_id,
            success=True,
            message="Resultado estructurado preparado — sin datos reales en esta etapa",
            contract_version=request.contract_version,
            processing_status=AnalysisProcessingStatus.NOT_EXECUTED,
            result=result,
            executed=False,
            metadata={"codigo_req": request.codigo_req},
        )
        self._event_recorder.record_response_prepared(
            request.process_id,
            operation="query_result",
            success=True,
        )
        return response
