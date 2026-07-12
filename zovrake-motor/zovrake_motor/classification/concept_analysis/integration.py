"""Integración del CAE con estados y eventos del núcleo."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from zovrake_motor.classification.concept_analysis.models import ConceptAnalysisResult
from zovrake_motor.events.enums import EventCategory, EventSeverity, EventType
from zovrake_motor.events.manager import EventManager
from zovrake_motor.states.enums import MotorState
from zovrake_motor.states.manager import StateManager

if TYPE_CHECKING:
    from zovrake_motor.classification.integration import ClassificationMotorIntegration


class ConceptAnalysisMotorIntegration:
    """
    Puente de integración del CAE con StateManager y EventManager.

    Registra trazabilidad sin almacenamiento persistente.
    """

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
    ) -> ConceptAnalysisMotorIntegration:
        return cls(
            state_manager=integration.state_manager,
            event_manager=integration.event_manager,
        )

    def begin_concept_analysis(self, process_id: UUID, *, document_id: str, model_id: str) -> None:
        self._transition_state(
            process_id,
            MotorState.PROCESANDO,
            f"Iniciando análisis de conceptos: {document_id}",
        )
        self._register_event(
            process_id=process_id,
            message=f"Análisis de conceptos iniciado para {document_id}",
            event_type=EventType.MODULE,
            severity=EventSeverity.INFO,
            metadata={
                "document_id": document_id,
                "model_id": model_id,
                "phase": "concept_analysis",
            },
        )

    def complete_concept_analysis(
        self,
        process_id: UUID,
        result: ConceptAnalysisResult,
    ) -> dict[str, Any]:
        state = self._transition_state(
            process_id,
            MotorState.PROCESAMIENTO_COMPLETADO,
            f"Análisis de conceptos completado: {result.document_id}",
        )
        severity = EventSeverity.WARNING if result.incidents else EventSeverity.INFO
        message = (
            f"Análisis de conceptos con incidencias para {result.document_id}"
            if result.incidents
            else f"Análisis de conceptos completado para {result.document_id}"
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
                "concepts_identified": len(result.catalog.concepts),
                "detectors_executed": result.detectors_executed,
                "internal_model_preserved": result.internal_model_preserved,
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
