"""Validación estructural de contratos de la API Interna."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from zovrake_motor.enterprise_integration.internal_api.contracts.requests import (
    AnalysisResultQueryRequest,
    AnalysisStatusQueryRequest,
    CancelAnalysisRequest,
    StartAnalysisRequest,
    ValidateAnalysisRequest,
)
from zovrake_motor.enterprise_integration.internal_api.enums import InternalApiOperation
from zovrake_motor.enterprise_integration.internal_api.versioning import ContractVersionRegistry


@dataclass(frozen=True)
class StructuralValidationResult:
    """Resultado de validación estructural — sin validación funcional."""

    valid: bool
    errors: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {"valid": self.valid, "errors": list(self.errors)}


class StructuralValidator:
    """
    Validador estructural de contratos.

    Verifica obligatoriedad, tipos y consistencia básica.
    """

    def validate_contract_version(self, version: str) -> StructuralValidationResult:
        normalized = ContractVersionRegistry.normalize_version(version)
        if not ContractVersionRegistry.is_supported(normalized):
            return StructuralValidationResult(
                valid=False,
                errors=(f"Versión de contrato no soportada: {version}",),
            )
        return StructuralValidationResult(valid=True)

    def validate_process_id(self, process_id: UUID) -> StructuralValidationResult:
        if process_id.int == 0:
            return StructuralValidationResult(
                valid=False,
                errors=("process_id no puede ser nulo",),
            )
        return StructuralValidationResult(valid=True)

    def validate_codigo_req(self, codigo_req: str, *, required: bool) -> StructuralValidationResult:
        if required and not codigo_req.strip():
            return StructuralValidationResult(
                valid=False,
                errors=("codigo_req es obligatorio",),
            )
        return StructuralValidationResult(valid=True)

    def _merge(self, *results: StructuralValidationResult) -> StructuralValidationResult:
        errors: list[str] = []
        for result in results:
            errors.extend(result.errors)
        return StructuralValidationResult(valid=len(errors) == 0, errors=tuple(errors))

    def validate_start_analysis(self, request: StartAnalysisRequest) -> StructuralValidationResult:
        return self._merge(
            self.validate_contract_version(request.contract_version),
            self.validate_process_id(request.process_id),
            self.validate_codigo_req(request.codigo_req, required=True),
        )

    def validate_status_query(
        self,
        request: AnalysisStatusQueryRequest,
    ) -> StructuralValidationResult:
        return self._merge(
            self.validate_contract_version(request.contract_version),
            self.validate_process_id(request.process_id),
        )

    def validate_result_query(
        self,
        request: AnalysisResultQueryRequest,
    ) -> StructuralValidationResult:
        return self._merge(
            self.validate_contract_version(request.contract_version),
            self.validate_process_id(request.process_id),
        )

    def validate_cancel(self, request: CancelAnalysisRequest) -> StructuralValidationResult:
        return self._merge(
            self.validate_contract_version(request.contract_version),
            self.validate_process_id(request.process_id),
        )

    def validate_validate_request(
        self,
        request: ValidateAnalysisRequest,
    ) -> StructuralValidationResult:
        errors: list[str] = []
        base = self._merge(
            self.validate_contract_version(request.contract_version),
            self.validate_process_id(request.process_id),
        )
        errors.extend(base.errors)
        if request.target_operation not in InternalApiOperation:
            errors.append("target_operation no es una operación válida")
        return StructuralValidationResult(valid=len(errors) == 0, errors=tuple(errors))
