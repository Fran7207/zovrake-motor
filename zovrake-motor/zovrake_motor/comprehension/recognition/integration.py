"""Integración del DRE con estados y eventos del núcleo."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from zovrake_motor.comprehension.recognition.models import DocumentRecognitionResult
from zovrake_motor.events.enums import EventCategory, EventSeverity, EventType
from zovrake_motor.events.manager import EventManager
from zovrake_motor.states.enums import MotorState
from zovrake_motor.states.manager import StateManager

if TYPE_CHECKING:
    from zovrake_motor.comprehension.integration import ComprehensionMotorIntegration


class RecognitionMotorIntegration:
    """
    Puente de integración del DRE con StateManager y EventManager.

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
    ) -> RecognitionMotorIntegration:
        return cls(
            state_manager=integration.state_manager,
            event_manager=integration.event_manager,
        )

    def begin_recognition(self, process_id: UUID, *, document_id: str) -> None:
        self._transition_state(
            process_id,
            MotorState.PREPARANDO_PROCESAMIENTO,
            f"Iniciando reconocimiento documental: {document_id}",
        )
        self._register_event(
            process_id=process_id,
            message=f"Reconocimiento documental iniciado para {document_id}",
            event_type=EventType.MODULE,
            severity=EventSeverity.INFO,
            metadata={"document_id": document_id, "phase": "recognition"},
        )

    def complete_recognition(
        self,
        process_id: UUID,
        result: DocumentRecognitionResult,
    ) -> dict[str, Any]:
        if result.recognized:
            state = self._transition_state(
                process_id,
                MotorState.PREPARANDO_PROCESAMIENTO,
                f"Formato identificado: {result.identified_format.value if result.identified_format else 'desconocido'}",
            )
            severity = EventSeverity.INFO
            message = f"Reconocimiento exitoso para {result.document_id}"
        else:
            state = self._transition_state(
                process_id,
                MotorState.INFORMACION_RECIBIDA,
                f"Formato no identificado: {result.document_id}",
            )
            severity = EventSeverity.WARNING
            message = f"Reconocimiento sin resultado para {result.document_id}"

        event = self._register_event(
            process_id=process_id,
            message=message,
            event_type=EventType.MODULE,
            severity=severity,
            associated_state=state.current_state.value,
            metadata={
                "document_id": result.document_id,
                "recognized": result.recognized,
                "identified_format": (
                    result.identified_format.value if result.identified_format else None
                ),
                "confidence": result.confidence,
                "strategy_used": result.strategy_used,
                "suggested_adapter": result.suggested_adapter,
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
            category=EventCategory.DOCUMENT,
            severity=severity,
        )
