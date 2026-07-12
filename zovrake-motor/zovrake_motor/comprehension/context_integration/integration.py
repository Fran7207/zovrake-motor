"""Integración del CIE con estados y eventos del núcleo."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from zovrake_motor.comprehension.context_integration.models import ContextIntegrationResult
from zovrake_motor.events.enums import EventCategory, EventSeverity, EventType
from zovrake_motor.events.manager import EventManager
from zovrake_motor.states.enums import MotorState
from zovrake_motor.states.manager import StateManager

if TYPE_CHECKING:
    from zovrake_motor.comprehension.integration import ComprehensionMotorIntegration


class ContextIntegrationMotorIntegration:
    """
    Puente de integración del CIE con StateManager y EventManager.

    Registra trazabilidad sin almacenamiento persistente.
    """

    MODULE_NAME = "comprehension"

    def __init__(
        self,
        *,
        state_manager: StateManager,
        event_manager: EventManager,
    ) -> None:
        self._state_manager = state_manager
        self._event_manager = event_manager

    @classmethod
    def from_comprehension_integration(
        cls,
        integration: ComprehensionMotorIntegration,
    ) -> ContextIntegrationMotorIntegration:
        return cls(
            state_manager=integration.state_manager,
            event_manager=integration.event_manager,
        )

    def begin_integration(self, process_id: UUID, *, document_id: str) -> None:
        self._transition_state(
            process_id,
            MotorState.PROCESANDO,
            f"Iniciando integración de contexto: {document_id}",
        )
        self._register_event(
            process_id=process_id,
            message=f"Integración de contexto iniciada para {document_id}",
            event_type=EventType.MODULE,
            severity=EventSeverity.INFO,
            metadata={"document_id": document_id, "phase": "context_integration"},
        )

    def complete_integration(
        self,
        process_id: UUID,
        result: ContextIntegrationResult,
    ) -> dict[str, Any]:
        state = self._transition_state(
            process_id,
            MotorState.PROCESAMIENTO_COMPLETADO,
            f"Integración de contexto completada: {result.document_id}",
        )
        severity = EventSeverity.WARNING if result.incidents else EventSeverity.INFO
        message = (
            f"Integración de contexto con incidencias para {result.document_id}"
            if result.incidents
            else f"Integración de contexto exitosa para {result.document_id}"
        )

        event = self._register_event(
            process_id=process_id,
            message=message,
            event_type=EventType.MODULE,
            severity=severity,
            associated_state=state.current_state.value,
            metadata={
                "document_id": result.document_id,
                "context_id": result.context_id,
                "associations_count": result.associations_count,
                "document_unmodified": result.document_unmodified,
                "original_preserved": result.original_preserved,
                "model_reference": result.association.model_reference,
                "index_reference": result.association.index_reference,
                "incidents_count": len(result.incidents),
            },
        )

        return {
            "process_state": state.to_dict(),
            "event": event.to_dict(),
        }

    def _transition_state(self, process_id: UUID, to_state: MotorState, reason: str):
        if self._state_manager.get_process(process_id) is None:
            self._state_manager.create_process(process_id, str(process_id))
        return self._state_manager.update_state(process_id, to_state, reason)

    def _register_event(
        self,
        *,
        process_id: UUID,
        message: str,
        event_type: EventType,
        severity: EventSeverity,
        associated_state: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        return self._event_manager.create_and_register(
            process_id=process_id,
            module=self.MODULE_NAME,
            event_type=event_type,
            message=message,
            associated_state=associated_state,
            metadata=metadata,
            category=EventCategory.PROCESSING,
            severity=severity,
        )
