"""Eventos del FTRRF — Sistema Centralizado de Eventos."""

from __future__ import annotations

from uuid import UUID

from zovrake_motor.enterprise_integration.ftrrf.enums import RecoveryStage
from zovrake_motor.enterprise_integration.integration import EnterpriseIntegrationMotorIntegration
from zovrake_motor.events.enums import EventCategory, EventSeverity, EventType


class FtrrfEventRecorder:
    """Registra eventos de errores, recuperación, reintentos y cancelaciones."""

    MODULE_NAME = "FaultToleranceRetryRecoveryFramework"

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
    ) -> None:
        event = self._event_manager.create_event(
            process_id=process_id,
            module=self.MODULE_NAME,
            event_type=event_type,
            message=message,
            associated_state=associated_state,
            metadata=dict(metadata or {}),
            category=EventCategory.PROCESSING,
            severity=severity,
        )
        self._event_manager.register_event(event)

    def record_fault_detected(
        self,
        process_id: UUID,
        *,
        error_id: str,
        category: str,
        severity: EventSeverity,
    ) -> None:
        self._register(
            process_id,
            event_type=EventType.SYSTEM,
            message="Fallo detectado y clasificado",
            severity=severity,
            associated_state=RecoveryStage.FAULT_DETECTED.value,
            metadata={"error_id": error_id, "category": category},
        )

    def record_recovery_started(self, process_id: UUID, *, error_id: str) -> None:
        self._register(
            process_id,
            event_type=EventType.MODULE,
            message="Recuperación iniciada",
            severity=EventSeverity.INFO,
            associated_state=RecoveryStage.RECOVERY_STARTED.value,
            metadata={"error_id": error_id},
        )

    def record_retry_scheduled(
        self,
        process_id: UUID,
        *,
        error_id: str,
        attempt: int,
        retries_remaining: int,
    ) -> None:
        self._register(
            process_id,
            event_type=EventType.MODULE,
            message="Reintento programado",
            severity=EventSeverity.WARNING,
            associated_state=RecoveryStage.RETRY_SCHEDULED.value,
            metadata={
                "error_id": error_id,
                "attempt": attempt,
                "retries_remaining": retries_remaining,
            },
        )

    def record_recovery_completed(self, process_id: UUID, *, error_id: str) -> None:
        self._register(
            process_id,
            event_type=EventType.FINALIZED,
            message="Recuperación completada",
            severity=EventSeverity.INFO,
            associated_state=RecoveryStage.RECOVERY_COMPLETED.value,
            metadata={"error_id": error_id},
        )

    def record_process_cancelled(self, process_id: UUID, *, error_id: str, reason: str) -> None:
        self._register(
            process_id,
            event_type=EventType.SYSTEM,
            message="Proceso cancelado por fallo no recuperable",
            severity=EventSeverity.WARNING,
            associated_state=RecoveryStage.PROCESS_CANCELLED.value,
            metadata={"error_id": error_id, "reason": reason},
        )

    def record_finalized_with_error(self, process_id: UUID, *, error_id: str) -> None:
        self._register(
            process_id,
            event_type=EventType.SYSTEM,
            message="Proceso finalizado por error",
            severity=EventSeverity.ERROR,
            associated_state=RecoveryStage.FINALIZED_WITH_ERROR.value,
            metadata={"error_id": error_id},
        )

    def record_state_sync(self, process_id: UUID, *, motor_state: str) -> None:
        self._register(
            process_id,
            event_type=EventType.STATE_CHANGE,
            message="Sincronización de estado FTRRF",
            severity=EventSeverity.INFO,
            associated_state=motor_state,
        )
