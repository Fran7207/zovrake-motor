"""Eventos del APQM — Sistema Centralizado de Eventos."""

from __future__ import annotations

from uuid import UUID

from zovrake_motor.enterprise_integration.apqm.enums import ApqmProcessingStage
from zovrake_motor.enterprise_integration.integration import EnterpriseIntegrationMotorIntegration
from zovrake_motor.events.enums import EventCategory, EventSeverity, EventType


class ApqmEventRecorder:
    """Registra eventos del ciclo de vida de procesamiento asíncrono."""

    MODULE_NAME = "AsyncProcessingQueueManager"

    def __init__(self, integration: EnterpriseIntegrationMotorIntegration) -> None:
        self._event_manager = integration.event_manager

    def _register(
        self,
        process_id: UUID,
        *,
        event_type: EventType,
        message: str,
        category: EventCategory,
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
            category=category,
            severity=severity,
        )
        self._event_manager.register_event(event)

    def record_enqueued(self, process_id: UUID, *, queue_item_id: str, position: int) -> None:
        self._register(
            process_id,
            event_type=EventType.REGISTERED,
            message="Solicitud ingresada a cola lógica",
            category=EventCategory.PROCESSING,
            severity=EventSeverity.INFO,
            associated_state=ApqmProcessingStage.QUEUED.value,
            metadata={"queue_item_id": queue_item_id, "queue_position": position},
        )

    def record_assigned(self, process_id: UUID, *, queue_item_id: str) -> None:
        self._register(
            process_id,
            event_type=EventType.MODULE,
            message="Solicitud asignada para procesamiento",
            category=EventCategory.PROCESSING,
            severity=EventSeverity.INFO,
            associated_state=ApqmProcessingStage.ASSIGNED.value,
            metadata={"queue_item_id": queue_item_id},
        )

    def record_processing_started(self, process_id: UUID, *, queue_item_id: str) -> None:
        self._register(
            process_id,
            event_type=EventType.PIPELINE,
            message="Procesamiento asíncrono iniciado",
            category=EventCategory.PROCESSING,
            severity=EventSeverity.INFO,
            associated_state=ApqmProcessingStage.PROCESSING_STARTED.value,
            metadata={"queue_item_id": queue_item_id},
        )

    def record_processing_completed(self, process_id: UUID, *, queue_item_id: str) -> None:
        self._register(
            process_id,
            event_type=EventType.FINALIZED,
            message="Procesamiento asíncrono completado",
            category=EventCategory.PROCESSING,
            severity=EventSeverity.INFO,
            associated_state=ApqmProcessingStage.PROCESSING_COMPLETED.value,
            metadata={"queue_item_id": queue_item_id},
        )

    def record_cancelled(self, process_id: UUID, *, queue_item_id: str, reason: str) -> None:
        self._register(
            process_id,
            event_type=EventType.SYSTEM,
            message="Procesamiento cancelado",
            category=EventCategory.PROCESSING,
            severity=EventSeverity.WARNING,
            associated_state=ApqmProcessingStage.PROCESSING_CANCELLED.value,
            metadata={"queue_item_id": queue_item_id, "reason": reason},
        )

    def record_controlled_error(
        self,
        process_id: UUID,
        *,
        queue_item_id: str,
        error_message: str,
    ) -> None:
        self._register(
            process_id,
            event_type=EventType.SYSTEM,
            message="Error controlado en procesamiento asíncrono",
            category=EventCategory.PROCESSING,
            severity=EventSeverity.ERROR,
            associated_state=ApqmProcessingStage.CONTROLLED_ERROR.value,
            metadata={"queue_item_id": queue_item_id, "error": error_message},
        )

    def record_state_sync(self, process_id: UUID, *, motor_state: str) -> None:
        self._register(
            process_id,
            event_type=EventType.STATE_CHANGE,
            message="Sincronización de estado APQM",
            category=EventCategory.STATE,
            severity=EventSeverity.INFO,
            associated_state=motor_state,
        )
