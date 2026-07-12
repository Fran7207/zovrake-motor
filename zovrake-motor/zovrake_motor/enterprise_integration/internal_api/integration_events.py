"""Registro de eventos de la API Interna — Sistema Centralizado de Eventos."""

from __future__ import annotations

from uuid import UUID

from zovrake_motor.events.enums import EventCategory, EventSeverity, EventType
from zovrake_motor.enterprise_integration.internal_api.context import InternalApiContext


class InternalApiEventRecorder:
    """Registra eventos de solicitudes y respuestas — sin persistencia adicional."""

    def __init__(self, context: InternalApiContext) -> None:
        self._context = context

    def record_request_accepted(
        self,
        process_id: UUID,
        *,
        operation: str,
        codigo_req: str = "",
    ) -> None:
        event = self._context.event_manager.create_event(
            process_id=process_id,
            module=InternalApiContext.MODULE_NAME,
            event_type=EventType.REGISTERED,
            message=f"Solicitud {operation} aceptada",
            associated_state=None,
            metadata={"operation": operation, "codigo_req": codigo_req},
            category=EventCategory.COMMUNICATION,
            severity=EventSeverity.INFO,
        )
        self._context.event_manager.register_event(event)

    def record_request_rejected(self, process_id: UUID, message: str) -> None:
        event = self._context.event_manager.create_event(
            process_id=process_id,
            module=InternalApiContext.MODULE_NAME,
            event_type=EventType.SYSTEM,
            message=message,
            metadata={"rejected": True},
            category=EventCategory.VALIDATION,
            severity=EventSeverity.WARNING,
        )
        self._context.event_manager.register_event(event)

    def record_response_prepared(
        self,
        process_id: UUID,
        *,
        operation: str,
        success: bool,
    ) -> None:
        event = self._context.event_manager.create_event(
            process_id=process_id,
            module=InternalApiContext.MODULE_NAME,
            event_type=EventType.MODULE,
            message=f"Respuesta {operation} preparada",
            metadata={"operation": operation, "success": success},
            category=EventCategory.COMMUNICATION,
            severity=EventSeverity.INFO,
        )
        self._context.event_manager.register_event(event)
