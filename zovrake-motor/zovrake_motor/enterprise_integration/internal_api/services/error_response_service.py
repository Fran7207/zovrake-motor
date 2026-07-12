"""Servicio de respuestas de error controladas."""

from __future__ import annotations

from uuid import UUID

from zovrake_motor.enterprise_integration.internal_api.contracts.responses import (
    InternalApiErrorResponse,
)
from zovrake_motor.enterprise_integration.internal_api.enums import InternalApiErrorCode
from zovrake_motor.enterprise_integration.internal_api.services.ports import ErrorResponseServicePort
from zovrake_motor.enterprise_integration.internal_api.versioning import ContractVersionRegistry


class ErrorResponseService(ErrorResponseServicePort):
    """Genera respuestas de error estandarizadas — sin lógica de negocio."""

    def build_error(self, *, error: InternalApiErrorResponse) -> InternalApiErrorResponse:
        return error

    def from_validation_errors(
        self,
        *,
        process_id: UUID,
        errors: tuple[str, ...],
    ) -> InternalApiErrorResponse:
        return InternalApiErrorResponse(
            error_code=InternalApiErrorCode.STRUCTURAL_VALIDATION_FAILED,
            message="Validación estructural fallida",
            process_id=process_id,
            contract_version=ContractVersionRegistry.ACTIVE_VERSION,
            contract_name=ContractVersionRegistry.CONTRACT_NAME,
            details={"validation_errors": list(errors)},
        )
