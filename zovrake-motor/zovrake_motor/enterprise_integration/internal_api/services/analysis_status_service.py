"""Servicio de consulta de estado de análisis."""

from __future__ import annotations

from zovrake_motor.enterprise_integration.internal_api.context import InternalApiContext
from zovrake_motor.enterprise_integration.internal_api.contracts.requests import (
    AnalysisStatusQueryRequest,
)
from zovrake_motor.enterprise_integration.internal_api.contracts.responses import (
    AnalysisStatusResponse,
    InternalApiErrorResponse,
)
from zovrake_motor.enterprise_integration.internal_api.enums import AnalysisProcessingStatus
from zovrake_motor.enterprise_integration.internal_api.integration_events import (
    InternalApiEventRecorder,
)
from zovrake_motor.enterprise_integration.internal_api.services.error_response_service import (
    ErrorResponseService,
)
from zovrake_motor.enterprise_integration.internal_api.services.ports import (
    AnalysisStatusServicePort,
)
from zovrake_motor.enterprise_integration.internal_api.validation.structural_validator import (
    StructuralValidationResult,
    StructuralValidator,
)


class AnalysisStatusService(AnalysisStatusServicePort):
    """Consulta estado — integrado con Sistema Centralizado de Estados."""

    def __init__(
        self,
        *,
        context: InternalApiContext,
        validator: StructuralValidator | None = None,
        error_service: ErrorResponseService | None = None,
        event_recorder: InternalApiEventRecorder | None = None,
        result_registry=None,
    ) -> None:
        self._context = context
        self._validator = validator or StructuralValidator()
        self._error_service = error_service or ErrorResponseService()
        self._event_recorder = event_recorder or InternalApiEventRecorder(context)
        self._result_registry = result_registry

    def bind_result_registry(self, result_registry) -> None:
        self._result_registry = result_registry

    def query_status(
        self,
        request: AnalysisStatusQueryRequest,
    ) -> AnalysisStatusResponse | InternalApiErrorResponse:
        if self._context.settings().structural_validation_enabled:
            validation = self._validator.validate_status_query(request)
        else:
            validation = StructuralValidationResult(valid=True)

        if not validation.valid:
            error = self._error_service.from_validation_errors(
                process_id=request.process_id,
                errors=validation.errors,
            )
            self._event_recorder.record_request_rejected(request.process_id, error.message)
            return error

        motor_state = None
        process_record = self._context.state_manager.get_process(request.process_id)
        if process_record is not None:
            motor_state = process_record.current_state.value

        stored = None
        if self._result_registry is not None:
            stored = self._result_registry.get(request.process_id)

        if stored is not None and stored.executed:
            response = AnalysisStatusResponse(
                process_id=request.process_id,
                success=True,
                message="Análisis ejecutado — resultado disponible",
                contract_version=request.contract_version,
                processing_status=AnalysisProcessingStatus.ACCEPTED,
                motor_state=motor_state,
                executed=True,
                metadata={
                    "codigo_req": stored.codigo_req or request.codigo_req,
                    "executed": True,
                    "catalog_id": stored.catalog_id,
                },
            )
        else:
            response = AnalysisStatusResponse(
                process_id=request.process_id,
                success=True,
                message="Estado consultado — sin ejecución de análisis en esta etapa",
                contract_version=request.contract_version,
                processing_status=AnalysisProcessingStatus.NOT_EXECUTED,
                motor_state=motor_state,
                executed=False,
                metadata={"codigo_req": request.codigo_req},
            )
        self._event_recorder.record_response_prepared(
            request.process_id,
            operation="query_status",
            success=True,
        )
        return response
