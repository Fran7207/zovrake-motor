"""Integración del CAE-Context con estados y eventos del núcleo."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from zovrake_motor.classification.context_association.models import ContextAssociationResult
from zovrake_motor.events.enums import EventCategory, EventSeverity, EventType
from zovrake_motor.events.manager import EventManager
from zovrake_motor.states.enums import MotorState
from zovrake_motor.states.manager import StateManager

if TYPE_CHECKING:
    from zovrake_motor.classification.integration import ClassificationMotorIntegration


class ContextAssociationMotorIntegration:
    """Puente de integración del CAE-Context con StateManager y EventManager."""

    MODULE_NAME = "classification"

    def __init__(
        self,
        *,
        state_manager: StateManager,
        event_manager: EventManager,
    ) -> None:
        self._state_manager = state_manager
        self._event_manager = event_manager

    @classmethod
    def from_classification_integration(
        cls,
        integration: ClassificationMotorIntegration,
    ) -> ContextAssociationMotorIntegration:
        return cls(
            state_manager=integration.state_manager,
            event_manager=integration.event_manager,
        )

    def begin_context_association(
        self,
        process_id: UUID,
        *,
        document_id: str,
        model_id: str,
        comparable_group_catalog_id: str,
    ) -> None:
        self._transition_state(
            process_id,
            MotorState.PROCESANDO,
            f"Iniciando asociación de contexto: {document_id}",
        )
        self._register_event(
            process_id=process_id,
            message=f"Asociación de contexto iniciada para {document_id}",
            event_type=EventType.MODULE,
            severity=EventSeverity.INFO,
            metadata={
                "document_id": document_id,
                "model_id": model_id,
                "comparable_group_catalog_id": comparable_group_catalog_id,
                "phase": "context_association",
            },
        )

    def complete_context_association(
        self,
        process_id: UUID,
        result: ContextAssociationResult,
    ) -> dict[str, Any]:
        state = self._transition_state(
            process_id,
            MotorState.PROCESAMIENTO_COMPLETADO,
            f"Asociación de contexto completada: {result.document_id}",
        )
        severity = EventSeverity.WARNING if result.incidents else EventSeverity.INFO
        message = (
            f"Asociación de contexto con incidencias para {result.document_id}"
            if result.incidents
            else f"Asociación de contexto completada para {result.document_id}"
        )

        event = self._register_event(
            process_id=process_id,
            message=message,
            event_type=EventType.MODULE,
            severity=severity,
            associated_state=state.current_state.value,
            metadata={
                "document_id": result.document_id,
                "model_id": result.model_id,
                "catalog_id": result.catalog.catalog_id,
                "associations_created": len(result.catalog.associations),
                "associators_executed": result.associators_executed,
                "comparable_group_catalog_preserved": result.comparable_group_catalog_preserved,
                "context_preserved": result.context_preserved,
                "status": result.status.value,
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
