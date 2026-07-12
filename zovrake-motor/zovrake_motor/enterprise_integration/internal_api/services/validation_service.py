"""Servicio de validación estructural de solicitudes."""

from __future__ import annotations

from zovrake_motor.enterprise_integration.internal_api.context import InternalApiContext
from zovrake_motor.enterprise_integration.internal_api.contracts.requests import (
    StartAnalysisRequest,
    ValidateAnalysisRequest,
)
from zovrake_motor.enterprise_integration.internal_api.contracts.responses import (
    InternalApiErrorResponse,
    ValidateAnalysisResponse,
)
from zovrake_motor.enterprise_integration.internal_api.enums import InternalApiOperation
from zovrake_motor.enterprise_integration.internal_api.services.error_response_service import (
    ErrorResponseService,
)
from zovrake_motor.enterprise_integration.internal_api.services.ports import ValidationServicePort
from zovrake_motor.enterprise_integration.internal_api.validation.structural_validator import (
    StructuralValidator,
)


class ValidationService(ValidationServicePort):
    """Validación estructural — sin validación funcional."""

    def __init__(
        self,
        *,
        context: InternalApiContext,
        validator: StructuralValidator | None = None,
        error_service: ErrorResponseService | None = None,
    ) -> None:
        self._context = context
        self._validator = validator or StructuralValidator()
        self._error_service = error_service or ErrorResponseService()

    def validate_request(
        self,
        request: ValidateAnalysisRequest,
    ) -> ValidateAnalysisResponse | InternalApiErrorResponse:
        validation = self._validator.validate_validate_request(request)
        if not validation.valid:
            return self._error_service.from_validation_errors(
                process_id=request.process_id,
                errors=validation.errors,
            )

        target_validation = self._validate_target_payload(request)
        return ValidateAnalysisResponse(
            process_id=request.process_id,
            success=True,
            message="Validación estructural completada — sin validación funcional",
            contract_version=request.contract_version,
            valid=target_validation.valid,
            validation_errors=target_validation.errors,
            metadata={
                "target_operation": request.target_operation.value,
                "structural_validation_enabled": (
                    self._context.settings().structural_validation_enabled
                ),
            },
        )

    def _validate_target_payload(self, request: ValidateAnalysisRequest):
        if request.target_operation == InternalApiOperation.START_ANALYSIS:
            start_request = StartAnalysisRequest(
                process_id=request.process_id,
                codigo_req=str(request.payload.get("codigo_req", request.codigo_req)),
                contract_version=request.contract_version,
                document_ids=tuple(request.payload.get("document_ids", ())),
                metadata=dict(request.payload.get("metadata", {})),
            )
            return self._validator.validate_start_analysis(start_request)
        return self._validator.validate_validate_request(request)
