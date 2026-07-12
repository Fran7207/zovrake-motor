"""
Security, Validation & Audit Framework — núcleo de seguridad transversal.

Único responsable de validación estructural, integridad y auditoría.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from zovrake_motor.enterprise_integration.ecg.contracts.erp_deliveries import ErpAnalysisDelivery
from zovrake_motor.enterprise_integration.ecg.contracts.erp_requests import (
    EvidenceCenterAnalysisRequest,
    EvidenceCenterResultQuery,
    EvidenceCenterStatusQuery,
)
from zovrake_motor.enterprise_integration.internal_api.contracts.requests import StartAnalysisRequest
from zovrake_motor.enterprise_integration.svaf.audit_store import AuditStore
from zovrake_motor.enterprise_integration.svaf.enums import (
    AuditOperationResult,
    ValidationDirection,
    ValidationStage,
)
from zovrake_motor.enterprise_integration.svaf.events import SvafEventRecorder
from zovrake_motor.enterprise_integration.svaf.fault_notification_port import (
    ValidationFaultNotificationPort,
)
from zovrake_motor.enterprise_integration.svaf.integrity_validator import RequestIntegrityValidator
from zovrake_motor.enterprise_integration.svaf.models import (
    AuditRecord,
    SecurityValidationOutcome,
    ValidationIssue,
    ValidationResult,
)
from zovrake_motor.enterprise_integration.svaf.validation_engine import ValidationEngine
from zovrake_motor.states.enums import MotorState

if TYPE_CHECKING:
    from zovrake_motor.enterprise_integration.integration import EnterpriseIntegrationMotorIntegration
    from zovrake_motor.enterprise_integration.ommf.ports import IntegrationObservabilityPort


class SecurityValidationAuditFramework:
    """
    Framework de seguridad, validación y auditoría.

    Capa transversal sin invadir lógica de negocio del Motor ni del ERP.
    """

    MODULE_NAME = "SecurityValidationAuditFramework"

    def __init__(
        self,
        *,
        integration: EnterpriseIntegrationMotorIntegration,
        validation_engine: ValidationEngine | None = None,
        integrity_validator: RequestIntegrityValidator | None = None,
        audit_store: AuditStore | None = None,
        event_recorder: SvafEventRecorder | None = None,
    ) -> None:
        self._integration = integration
        self._engine = validation_engine or ValidationEngine()
        self._integrity = integrity_validator or RequestIntegrityValidator()
        self._audit = audit_store or AuditStore()
        self._events = event_recorder or SvafEventRecorder(integration)
        self._fault_notifier: ValidationFaultNotificationPort | None = None
        self._observability: IntegrationObservabilityPort | None = None
        self._approved_inbound: set[str] = set()
        self._initialized = False
        self._metrics = {
            "validations_total": 0,
            "validations_approved": 0,
            "validations_rejected": 0,
            "integrity_errors": 0,
            "audits_recorded": 0,
            "total_validation_duration_ms": 0.0,
        }

    @property
    def audit_store(self) -> AuditStore:
        return self._audit

    def bind_fault_notifier(self, notifier: ValidationFaultNotificationPort) -> None:
        self._fault_notifier = notifier

    def bind_observability(self, observability: IntegrationObservabilityPort) -> None:
        self._observability = observability

    def initialize(self) -> None:
        self._initialized = True

    def is_ready(self) -> bool:
        return self._initialized and self._settings().prepared

    def _settings(self):
        return (
            self._integration.enterprise_integration_settings().security_validation_audit_framework
        )

    def validate_inbound_analysis_request(
        self,
        request: EvidenceCenterAnalysisRequest,
    ) -> SecurityValidationOutcome:
        return self._validate_inbound(
            process_id=request.process_id,
            operation="submit_analysis_request",
            payload=request.to_dict(),
            structural=self._engine.validate_erp_analysis_request(request),
        )

    def validate_inbound_status_query(
        self,
        request: EvidenceCenterStatusQuery,
    ) -> SecurityValidationOutcome:
        return self._validate_inbound(
            process_id=request.process_id,
            operation="query_analysis_status",
            payload=request.to_dict(),
            structural=self._engine.validate_erp_status_query(request),
        )

    def validate_inbound_result_query(
        self,
        request: EvidenceCenterResultQuery,
    ) -> SecurityValidationOutcome:
        return self._validate_inbound(
            process_id=request.process_id,
            operation="query_analysis_result",
            payload=request.to_dict(),
            structural=self._engine.validate_erp_result_query(request),
        )

    def validate_outbound_delivery(
        self,
        delivery: ErpAnalysisDelivery,
        *,
        operation: str,
    ) -> SecurityValidationOutcome:
        if not self.is_ready():
            raise RuntimeError("SVAF no está listo")

        self._events.record_validation_started(delivery.process_id, operation=operation)
        structural = self._engine.validate_erp_delivery(delivery)
        inbound_key = f"{delivery.process_id}:{operation}"
        integrity_issues = self._integrity.check_outbound(
            process_id=delivery.process_id,
            operation=operation,
            payload=delivery.to_dict(),
            inbound_approved=inbound_key in self._approved_inbound,
        )
        validation = self._merge_validation(structural, integrity_issues)

        if validation.approved:
            self._events.record_validation_approved(delivery.process_id, operation=operation)
            if delivery.analysis_status == "procesamiento_pendiente":
                self._sync_state(
                    delivery.process_id,
                    MotorState.PROCESAMIENTO_PENDIENTE,
                    "Entrega validada — procesamiento pendiente",
                )
            else:
                self._sync_state(delivery.process_id, MotorState.INFORMACION_RECIBIDA, "Entrega validada")
        else:
            return self._reject(
                process_id=delivery.process_id,
                operation=operation,
                validation=validation,
                direction=ValidationDirection.MOTOR_TO_ERP,
            )

        audit = self._record_audit(
            process_id=delivery.process_id,
            operation=operation,
            direction=ValidationDirection.MOTOR_TO_ERP,
            result=AuditOperationResult.SUCCESS,
        )
        return SecurityValidationOutcome(
            approved=True,
            validation=validation,
            audit_record=audit,
        )

    @staticmethod
    def _requires_erp_inbound_validation(metadata: dict[str, Any] | None) -> bool:
        meta = metadata or {}
        return (
            meta.get("source") == "evidence_center"
            or meta.get("evidence_center_contract") is not None
        )

    def authorize_pipeline_entry(
        self,
        *,
        process_id: UUID,
        operation: str,
        metadata: dict[str, Any] | None = None,
    ) -> SecurityValidationOutcome:
        if not self.is_ready():
            raise RuntimeError("SVAF no está listo")

        if not self._requires_erp_inbound_validation(metadata):
            return SecurityValidationOutcome(
                approved=True,
                validation=ValidationResult(
                    approved=True,
                    stage=ValidationStage.VALIDATION_APPROVED,
                    direction=ValidationDirection.PIPELINE_ENTRY,
                ),
            )

        inbound_key = f"{process_id}:submit_analysis_request"
        if inbound_key not in self._approved_inbound:
            validation = ValidationResult(
                approved=False,
                stage=ValidationStage.VALIDATION_REJECTED,
                direction=ValidationDirection.PIPELINE_ENTRY,
                issues=(
                    ValidationIssue(
                        field="pipeline",
                        message="Pipeline bloqueado — solicitud ERP no validada",
                    ),
                ),
            )
            return self._reject(
                process_id=process_id,
                operation=operation,
                validation=validation,
                direction=ValidationDirection.PIPELINE_ENTRY,
                block_pipeline=True,
            )

        self._events.record_validation_started(process_id, operation=operation)
        validation = self._engine.validate_pipeline_entry(
            process_id=process_id,
            operation=operation,
            metadata=metadata,
        )
        if not validation.approved:
            return self._reject(
                process_id=process_id,
                operation=operation,
                validation=validation,
                direction=ValidationDirection.PIPELINE_ENTRY,
                block_pipeline=True,
            )

        self._events.record_validation_approved(process_id, operation=operation)
        audit = self._record_audit(
            process_id=process_id,
            operation=operation,
            direction=ValidationDirection.PIPELINE_ENTRY,
            result=AuditOperationResult.SUCCESS,
        )
        return SecurityValidationOutcome(
            approved=True,
            validation=validation,
            audit_record=audit,
        )

    def validate_internal_request(
        self,
        request: StartAnalysisRequest,
    ) -> SecurityValidationOutcome:
        validation = self._engine.validate_internal_start_analysis(request)
        if not validation.approved:
            return self._reject(
                process_id=request.process_id,
                operation="start_analysis",
                validation=validation,
                direction=ValidationDirection.PIPELINE_ENTRY,
                block_pipeline=True,
            )
        audit = self._record_audit(
            process_id=request.process_id,
            operation="start_analysis",
            direction=ValidationDirection.PIPELINE_ENTRY,
            result=AuditOperationResult.SUCCESS,
        )
        return SecurityValidationOutcome(approved=True, validation=validation, audit_record=audit)

    def _validate_inbound(
        self,
        *,
        process_id: UUID,
        operation: str,
        payload: dict[str, Any],
        structural: ValidationResult,
    ) -> SecurityValidationOutcome:
        if not self.is_ready():
            raise RuntimeError("SVAF no está listo")

        self._events.record_validation_started(process_id, operation=operation)
        self._sync_state(process_id, MotorState.VALIDANDO_INFORMACION, "Validación iniciada")

        integrity_issues = self._integrity.check_inbound(
            process_id=process_id,
            operation=operation,
            payload=payload,
        )
        validation = self._merge_validation(structural, integrity_issues)

        if not validation.approved:
            return self._reject(
                process_id=process_id,
                operation=operation,
                validation=validation,
                direction=ValidationDirection.ERP_TO_MOTOR,
                block_pipeline=True,
            )

        self._events.record_validation_approved(process_id, operation=operation)
        self._sync_state(process_id, MotorState.INFORMACION_RECIBIDA, "Validación aprobada")
        self._integrity.mark_processed(process_id, operation)
        self._approved_inbound.add(f"{process_id}:{operation}")

        audit = self._record_audit(
            process_id=process_id,
            operation=operation,
            direction=ValidationDirection.ERP_TO_MOTOR,
            result=AuditOperationResult.SUCCESS,
        )
        if self._observability is not None:
            self._observability.record_validation_event(
                process_id=process_id,
                event="validation_approved",
                approved=True,
                duration_ms=validation.duration_ms,
                operation=operation,
            )
        return SecurityValidationOutcome(
            approved=True,
            validation=validation,
            audit_record=audit,
        )

    def _reject(
        self,
        *,
        process_id: UUID,
        operation: str,
        validation: ValidationResult,
        direction: ValidationDirection,
        block_pipeline: bool = False,
    ) -> SecurityValidationOutcome:
        errors = tuple(issue.message for issue in validation.issues)
        self._events.record_validation_rejected(process_id, operation=operation, errors=errors)
        for issue in validation.issues:
            self._events.record_integrity_issue(process_id, issue=issue.message)
        self._sync_state(process_id, MotorState.ERROR_VALIDACION, "Validación rechazada")

        self._metrics["validations_rejected"] += 1
        if any(issue.issue_type.value != "estructura_invalida" for issue in validation.issues):
            self._metrics["integrity_errors"] += 1

        notified = False
        if self._fault_notifier is not None:
            self._fault_notifier.notify_validation_failure(
                process_id=process_id,
                error_message="; ".join(errors) or "Validación rechazada",
                error_code="structural_validation_failed",
                context_metadata={"operation": operation, "direction": direction.value},
            )
            notified = True

        audit = self._record_audit(
            process_id=process_id,
            operation=operation,
            direction=direction,
            result=AuditOperationResult.REJECTED,
            errors_detected=errors,
        )
        if self._observability is not None:
            self._observability.record_validation_event(
                process_id=process_id,
                event="validation_rejected",
                approved=False,
                operation=operation,
            )
        return SecurityValidationOutcome(
            approved=False,
            validation=validation,
            audit_record=audit,
            notified_ftrrf=notified,
            pipeline_blocked=block_pipeline,
        )

    def _record_audit(
        self,
        *,
        process_id: UUID,
        operation: str,
        direction: ValidationDirection,
        result: AuditOperationResult,
        errors_detected: tuple[str, ...] = (),
    ) -> AuditRecord:
        state = self._integration.state_manager.get_process(process_id)
        process_state = state.current_state.value if state is not None else ""
        record = AuditRecord.create(
            process_id=process_id,
            operation=operation,
            component=self.MODULE_NAME,
            direction=direction,
            result=result,
            process_state=process_state,
            errors_detected=errors_detected,
        )
        self._audit.save(record)
        self._events.record_audit_registered(process_id, audit_id=record.audit_id)
        self._metrics["audits_recorded"] += 1
        if self._observability is not None:
            self._observability.record_validation_event(
                process_id=process_id,
                event="audit",
                approved=True,
                operation=operation,
            )
        return record

    def _merge_validation(
        self,
        structural: ValidationResult,
        integrity_issues: tuple[ValidationIssue, ...],
    ) -> ValidationResult:
        self._metrics["validations_total"] += 1
        self._metrics["total_validation_duration_ms"] += structural.duration_ms

        all_issues = list(structural.issues) + list(integrity_issues)
        if all_issues:
            return ValidationResult(
                approved=False,
                stage=ValidationStage.VALIDATION_REJECTED,
                direction=structural.direction,
                issues=tuple(all_issues),
                duration_ms=structural.duration_ms,
            )

        self._metrics["validations_approved"] += 1
        return structural

    def _sync_state(self, process_id: UUID, motor_state: MotorState, reason: str) -> None:
        state_manager = self._integration.state_manager
        if state_manager.get_process(process_id) is None:
            return
        state_manager.update_state(process_id, motor_state, reason)
        self._events.record_state_sync(process_id, motor_state=motor_state.value)

    def observability_snapshot(self) -> dict[str, Any]:
        total = self._metrics["validations_total"]
        avg_duration = (
            self._metrics["total_validation_duration_ms"] / total if total else 0.0
        )
        return {
            **self._metrics,
            "average_validation_duration_ms": avg_duration,
            "audits_in_store": self._audit.count(),
        }

    def snapshot(self) -> dict[str, Any]:
        settings = self._settings()
        return {
            "initialized": self._initialized,
            "ready": self.is_ready(),
            "enabled": settings.enabled,
            "prepared": settings.prepared,
            "fault_notifier_bound": self._fault_notifier is not None,
            "observability_bound": self._observability is not None,
            "observability": self.observability_snapshot(),
            "integrity": self._integrity.snapshot(),
        }
