"""Eventos del ERP Communication Gateway."""

from __future__ import annotations

from uuid import UUID

from zovrake_motor.events.enums import EventCategory, EventSeverity, EventType
from zovrake_motor.enterprise_integration.ecg.enums import EcgChannelDirection, EcgMessageType
from zovrake_motor.enterprise_integration.integration import EnterpriseIntegrationMotorIntegration


class EcgEventRecorder:
    """Registra eventos de comunicación ERP ↔ Motor."""

    MODULE_NAME = "ErpCommunicationGateway"

    def __init__(self, integration: EnterpriseIntegrationMotorIntegration) -> None:
        self._event_manager = integration.event_manager

    def record_message(
        self,
        process_id: UUID,
        *,
        message_type: EcgMessageType,
        direction: EcgChannelDirection,
        summary: str,
    ) -> None:
        event = self._event_manager.create_event(
            process_id=process_id,
            module=self.MODULE_NAME,
            event_type=EventType.MODULE,
            message=summary,
            metadata={
                "message_type": message_type.value,
                "direction": direction.value,
            },
            category=EventCategory.COMMUNICATION,
            severity=EventSeverity.INFO,
        )
        self._event_manager.register_event(event)

    def record_state_sync(self, process_id: UUID, *, motor_state: str) -> None:
        event = self._event_manager.create_event(
            process_id=process_id,
            module=self.MODULE_NAME,
            event_type=EventType.STATE_CHANGE,
            message="Sincronización de estado ECG",
            associated_state=motor_state,
            category=EventCategory.STATE,
            severity=EventSeverity.INFO,
        )
        self._event_manager.register_event(event)
