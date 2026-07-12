"""Integración del DVF con estados y eventos del núcleo."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from zovrake_motor.comprehension.validation.models import DocumentValidationResult
from zovrake_motor.events.enums import EventCategory, EventSeverity, EventType
from zovrake_motor.events.manager import EventManager
from zovrake_motor.states.enums import MotorState
from zovrake_motor.states.manager import StateManager

if TYPE_CHECKING:
    from zovrake_motor.comprehension.integration import ComprehensionMotorIntegration


class ValidationMotorIntegration:
    """
    Puente de integración del DVF con StateManager y EventManager.

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
    ) -> ValidationMotorIntegration:
        return cls(
            state_manager=integration.state_manager,
            event_manager=integration.event_manager,
        )

    def begin_validation(self, process_id: UUID, *, document_id: str) -> None:
        self._transition_state(
            process_id,
            MotorState.VALIDANDO_INFORMACION,
            f"Iniciando validación documental: {document_id}",
        )
        self._register_event(
            process_id=process_id,
            message=f"Validación documental iniciada para {document_id}",
            event_type=EventType.MODULE,
            severity=EventSeverity.INFO,
            metadata={"document_id": document_id, "phase": "validation"},
        )

    def complete_validation(
        self,
        process_id: UUID,
        result: DocumentValidationResult,
    ) -> dict[str, Any]:
        if result.status.value == "failed":
            state = self._transition_state(
                process_id,
                MotorState.ERROR_VALIDACION,
                f"Validación documental fallida: {result.document_id}",
            )
            severity = EventSeverity.ERROR
            message = f"Validación fallida para {result.document_id}"
        elif result.status.value == "warning":
            state = self._transition_state(
                process_id,
                MotorState.INFORMACION_RECIBIDA,
                f"Validación documental con advertencias: {result.document_id}",
            )
            severity = EventSeverity.WARNING
            message = f"Validación con advertencias para {result.document_id}"
        else:
            state = self._transition_state(
                process_id,
                MotorState.INFORMACION_RECIBIDA,
                f"Validación documental exitosa: {result.document_id}",
            )
            severity = EventSeverity.INFO
            message = f"Validación exitosa para {result.document_id}"

        event = self._register_event(
            process_id=process_id,
            message=message,
            event_type=EventType.MODULE,
            severity=severity,
            associated_state=state.current_state.value,
            metadata={
                "document_id": result.document_id,
                "validation_status": result.status.value,
                "quality_level": result.quality_level.value,
                "incidents_count": len(result.incidents),
                "warnings_count": len(result.warnings),
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
            category=EventCategory.VALIDATION,
            severity=severity,
        )
