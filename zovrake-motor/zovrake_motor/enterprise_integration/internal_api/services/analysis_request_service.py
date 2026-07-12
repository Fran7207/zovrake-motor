"""Servicio de solicitudes de análisis."""

from __future__ import annotations

from zovrake_motor.enterprise_integration.internal_api.context import InternalApiContext
from zovrake_motor.enterprise_integration.internal_api.contracts.requests import StartAnalysisRequest
from zovrake_motor.enterprise_integration.internal_api.contracts.responses import (
    InternalApiErrorResponse,
    StartAnalysisResponse,
)
from zovrake_motor.enterprise_integration.internal_api.enums import AnalysisProcessingStatus
from zovrake_motor.enterprise_integration.internal_api.integration_events import (
    InternalApiEventRecorder,
)
from zovrake_motor.enterprise_integration.internal_api.services.error_response_service import (
    ErrorResponseService,
)
from zovrake_motor.enterprise_integration.internal_api.services.ports import (
    AnalysisRequestServicePort,
)
from zovrake_motor.enterprise_integration.internal_api.validation.structural_validator import (
    StructuralValidationResult,
    StructuralValidator,
)


class AnalysisRequestService(AnalysisRequestServicePort):
    """Acepta solicitudes de inicio — sin ejecutar análisis."""

    def __init__(
        self,
        *,
        context: InternalApiContext,
        validator: StructuralValidator | None = None,
        error_service: ErrorResponseService | None = None,
        event_recorder: InternalApiEventRecorder | None = None,
    ) -> None:
        self._context = context
        self._validator = validator or StructuralValidator()
        self._error_service = error_service or ErrorResponseService()
        self._event_recorder = event_recorder or InternalApiEventRecorder(context)

    def start_analysis(
        self,
        request: StartAnalysisRequest,
    ) -> StartAnalysisResponse | InternalApiErrorResponse:
        if self._context.settings().structural_validation_enabled:
            validation = self._validator.validate_start_analysis(request)
        else:
            validation = StructuralValidationResult(valid=True)

        if not validation.valid:
            error = self._error_service.from_validation_errors(
                process_id=request.process_id,
                errors=validation.errors,
            )
            self._event_recorder.record_request_rejected(request.process_id, error.message)
            return error

        self._event_recorder.record_request_accepted(
            request.process_id,
            operation="start_analysis",
            codigo_req=request.codigo_req,
        )

        return StartAnalysisResponse(
            process_id=request.process_id,
            success=True,
            message="Solicitud de análisis aceptada — sin ejecución en esta etapa",
            contract_version=request.contract_version,
            processing_status=AnalysisProcessingStatus.ACCEPTED,
            executed=False,
            metadata={
                "codigo_req": request.codigo_req,
                "document_ids": list(request.document_ids),
                "analysis_scope": request.analysis_scope,
            },
        )
