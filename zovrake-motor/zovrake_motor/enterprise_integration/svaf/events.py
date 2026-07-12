"""Eventos del SVAF — Sistema Centralizado de Eventos."""

from __future__ import annotations

from uuid import UUID

from zovrake_motor.enterprise_integration.integration import EnterpriseIntegrationMotorIntegration
from zovrake_motor.enterprise_integration.svaf.enums import ValidationStage
from zovrake_motor.events.enums import EventCategory, EventSeverity, EventType


class SvafEventRecorder:
    """Registra eventos de validación, auditoría e integridad."""

    MODULE_NAME = "SecurityValidationAuditFramework"

    def __init__(self, integration: EnterpriseIntegrationMotorIntegration) -> None:
        self._event_manager = integration.event_manager

    def _register(
        self,
        process_id: UUID,
        *,
        event_type: EventType,
        message: str,
        severity: EventSeverity,
        associated_state: str = "",
        metadata: dict | None = None,
        category: EventCategory = EventCategory.VALIDATION,
    ) -> None:
        event = self._event_manager.create_event(
            process_id=process_id,
            module=self.MODULE_NAME,
            event_type=event_type,
            message=message,
            associated_state=associated_state,
            metadata=dict(metadata or {}),
            category=category,
            severity=severity,
        )
        self._event_manager.register_event(event)

    def record_validation_started(self, process_id: UUID, *, operation: str) -> None:
        self._register(
            process_id,
            event_type=EventType.MODULE,
            message="Validación iniciada",
            severity=EventSeverity.INFO,
            associated_state=ValidationStage.VALIDATION_STARTED.value,
            metadata={"operation": operation},
        )

    def record_validation_approved(self, process_id: UUID, *, operation: str) -> None:
        self._register(
            process_id,
            event_type=EventType.FINALIZED,
            message="Validación aprobada",
            severity=EventSeverity.INFO,
            associated_state=ValidationStage.VALIDATION_APPROVED.value,
            metadata={"operation": operation},
        )

    def record_validation_rejected(
        self,
        process_id: UUID,
        *,
        operation: str,
        errors: tuple[str, ...],
    ) -> None:
        self._register(
            process_id,
            event_type=EventType.SYSTEM,
            message="Validación rechazada",
            severity=EventSeverity.WARNING,
            associated_state=ValidationStage.VALIDATION_REJECTED.value,
            metadata={"operation": operation, "errors": list(errors)},
        )

    def record_audit_registered(self, process_id: UUID, *, audit_id: str) -> None:
        self._register(
            process_id,
            event_type=EventType.REGISTERED,
            message="Auditoría registrada",
            severity=EventSeverity.INFO,
            associated_state=ValidationStage.AUDIT_RECORDED.value,
            metadata={"audit_id": audit_id},
        )

    def record_integrity_issue(self, process_id: UUID, *, issue: str) -> None:
        self._register(
            process_id,
            event_type=EventType.SYSTEM,
            message="Incidencia de integridad detectada",
            severity=EventSeverity.ERROR,
            metadata={"issue": issue},
        )

    def record_state_sync(self, process_id: UUID, *, motor_state: str) -> None:
        self._register(
            process_id,
            event_type=EventType.STATE_CHANGE,
            message="Sincronización de estado SVAF",
            severity=EventSeverity.INFO,
            associated_state=motor_state,
            category=EventCategory.STATE,
        )
