"""Motor de validación estructural del SVAF — sin validación de negocio."""

from __future__ import annotations

import time
from typing import Any
from uuid import UUID

from zovrake_motor.enterprise_integration.ecg.contracts.erp_deliveries import ErpAnalysisDelivery
from zovrake_motor.enterprise_integration.ecg.contracts.erp_requests import (
    EvidenceCenterAnalysisRequest,
    EvidenceCenterResultQuery,
    EvidenceCenterStatusQuery,
)
from zovrake_motor.enterprise_integration.ecg.enums import EcgContractVersion
from zovrake_motor.enterprise_integration.internal_api.contracts.requests import (
    AnalysisResultQueryRequest,
    AnalysisStatusQueryRequest,
    StartAnalysisRequest,
)
from zovrake_motor.enterprise_integration.internal_api.validation.structural_validator import (
    StructuralValidator,
)
from zovrake_motor.enterprise_integration.svaf.enums import (
    IntegrityIssueType,
    ValidationDirection,
    ValidationStage,
)
from zovrake_motor.enterprise_integration.svaf.models import ValidationIssue, ValidationResult


class ValidationEngine:
    """
    Verifica estructura del contrato, obligatoriedad, formatos e identificadores.

    No realiza validaciones de negocio.
    """

    MODULE_NAME = "SecurityValidationAuditFramework"

    def __init__(self, *, structural_validator: StructuralValidator | None = None) -> None:
        self._structural = structural_validator or StructuralValidator()

    def validate_erp_analysis_request(
        self,
        request: EvidenceCenterAnalysisRequest,
    ) -> ValidationResult:
        started = time.perf_counter()
        issues: list[ValidationIssue] = []

        issues.extend(self._validate_process_id(request.process_id))
        issues.extend(self._validate_identifier("project_id", request.project_id, required=True))
        issues.extend(self._validate_identifier("quotation_id", request.quotation_id, required=True))
        issues.extend(
            self._validate_identifier("codigo_req", request.requirement.codigo_req, required=True),
        )
        issues.extend(self._validate_contract_version(request.contract_version))
        issues.extend(self._validate_metadata("analysis_metadata", request.analysis_metadata))

        for index, document in enumerate(request.evidence_documents):
            if not document.document_id.strip():
                issues.append(
                    ValidationIssue(
                        field=f"evidence_documents[{index}].document_id",
                        message="document_id es obligatorio",
                        issue_type=IntegrityIssueType.INCOMPLETE_MESSAGE,
                    ),
                )

        return self._build_result(
            issues,
            direction=ValidationDirection.ERP_TO_MOTOR,
            started=started,
        )

    def validate_erp_status_query(self, request: EvidenceCenterStatusQuery) -> ValidationResult:
        started = time.perf_counter()
        issues: list[ValidationIssue] = []
        issues.extend(self._validate_process_id(request.process_id))
        return self._build_result(issues, direction=ValidationDirection.ERP_TO_MOTOR, started=started)

    def validate_erp_result_query(self, request: EvidenceCenterResultQuery) -> ValidationResult:
        started = time.perf_counter()
        issues: list[ValidationIssue] = []
        issues.extend(self._validate_process_id(request.process_id))
        return self._build_result(issues, direction=ValidationDirection.ERP_TO_MOTOR, started=started)

    def validate_internal_start_analysis(self, request: StartAnalysisRequest) -> ValidationResult:
        started = time.perf_counter()
        structural = self._structural.validate_start_analysis(request)
        issues = [
            ValidationIssue(field="internal_api", message=error)
            for error in structural.errors
        ]
        return self._build_result(issues, direction=ValidationDirection.PIPELINE_ENTRY, started=started)

    def validate_internal_status_query(
        self,
        request: AnalysisStatusQueryRequest,
    ) -> ValidationResult:
        started = time.perf_counter()
        structural = self._structural.validate_status_query(request)
        issues = [
            ValidationIssue(field="internal_api", message=error)
            for error in structural.errors
        ]
        return self._build_result(issues, direction=ValidationDirection.PIPELINE_ENTRY, started=started)

    def validate_internal_result_query(
        self,
        request: AnalysisResultQueryRequest,
    ) -> ValidationResult:
        started = time.perf_counter()
        structural = self._structural.validate_result_query(request)
        issues = [
            ValidationIssue(field="internal_api", message=error)
            for error in structural.errors
        ]
        return self._build_result(issues, direction=ValidationDirection.PIPELINE_ENTRY, started=started)

    def validate_erp_delivery(self, delivery: ErpAnalysisDelivery) -> ValidationResult:
        started = time.perf_counter()
        issues: list[ValidationIssue] = []

        issues.extend(self._validate_process_id(delivery.process_id))
        issues.extend(self._validate_identifier("project_id", delivery.project_id, required=True))
        issues.extend(self._validate_identifier("quotation_id", delivery.quotation_id, required=True))
        issues.extend(self._validate_contract_version(delivery.contract_version))

        if not delivery.message.strip():
            issues.append(
                ValidationIssue(
                    field="message",
                    message="message es obligatorio en entrega ERP",
                    issue_type=IntegrityIssueType.INCOMPLETE_MESSAGE,
                ),
            )
        if not delivery.analysis_status.strip():
            issues.append(
                ValidationIssue(
                    field="analysis_status",
                    message="analysis_status es obligatorio",
                    issue_type=IntegrityIssueType.INCOMPLETE_MESSAGE,
                ),
            )

        return self._build_result(
            issues,
            direction=ValidationDirection.MOTOR_TO_ERP,
            started=started,
        )

    def validate_pipeline_entry(
        self,
        *,
        process_id: UUID,
        operation: str,
        metadata: dict[str, Any] | None = None,
    ) -> ValidationResult:
        started = time.perf_counter()
        issues: list[ValidationIssue] = []
        issues.extend(self._validate_process_id(process_id))
        if not operation.strip():
            issues.append(
                ValidationIssue(
                    field="operation",
                    message="operation es obligatoria para entrada al Pipeline",
                ),
            )
        if metadata is not None:
            issues.extend(self._validate_metadata("metadata", metadata))
        return self._build_result(
            issues,
            direction=ValidationDirection.PIPELINE_ENTRY,
            started=started,
        )

    def _validate_process_id(self, process_id: UUID) -> list[ValidationIssue]:
        result = self._structural.validate_process_id(process_id)
        if result.valid:
            return []
        return [
            ValidationIssue(field="process_id", message=error, issue_type=IntegrityIssueType.INVALID_STRUCTURE)
            for error in result.errors
        ]

    @staticmethod
    def _validate_identifier(field: str, value: str, *, required: bool) -> list[ValidationIssue]:
        if required and not value.strip():
            return [
                ValidationIssue(
                    field=field,
                    message=f"{field} es obligatorio",
                    issue_type=IntegrityIssueType.INCOMPLETE_MESSAGE,
                ),
            ]
        return []

    @staticmethod
    def _validate_contract_version(version: str) -> list[ValidationIssue]:
        if version != EcgContractVersion.V1.value:
            return [
                ValidationIssue(
                    field="contract_version",
                    message=f"Versión de contrato no soportada: {version}",
                    issue_type=IntegrityIssueType.INVALID_CONTRACT,
                ),
            ]
        return []

    @staticmethod
    def _validate_metadata(field: str, metadata: Any) -> list[ValidationIssue]:
        if not isinstance(metadata, dict):
            return [
                ValidationIssue(
                    field=field,
                    message=f"{field} debe ser un diccionario",
                    issue_type=IntegrityIssueType.INVALID_STRUCTURE,
                ),
            ]
        return []

    @staticmethod
    def _build_result(
        issues: list[ValidationIssue],
        *,
        direction: ValidationDirection,
        started: float,
    ) -> ValidationResult:
        duration_ms = (time.perf_counter() - started) * 1000
        approved = len(issues) == 0
        stage = ValidationStage.VALIDATION_APPROVED if approved else ValidationStage.VALIDATION_REJECTED
        return ValidationResult(
            approved=approved,
            stage=stage,
            direction=direction,
            issues=tuple(issues),
            duration_ms=duration_ms,
        )
