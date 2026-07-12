"""Integración del CVF con estados y eventos del núcleo."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from zovrake_motor.comparative_tables.comparative_validation_framework.models import (
    ComparativeModelValidationResult,
)
from zovrake_motor.events.enums import EventCategory, EventSeverity, EventType
from zovrake_motor.events.manager import EventManager
from zovrake_motor.states.enums import MotorState
from zovrake_motor.states.manager import StateManager

if TYPE_CHECKING:
    from zovrake_motor.comparative_tables.integration import ComparativeTablesMotorIntegration


class ComparativeValidationMotorIntegration:
    """Puente de integración del CVF con StateManager y EventManager."""

    MODULE_NAME = "comparative_tables"

    def __init__(
        self,
        *,
        state_manager: StateManager,
        event_manager: EventManager,
    ) -> None:
        self._state_manager = state_manager
        self._event_manager = event_manager

    @classmethod
    def from_comparative_tables_integration(
        cls,
        integration: ComparativeTablesMotorIntegration,
    ) -> ComparativeValidationMotorIntegration:
        return cls(
            state_manager=integration.state_manager,
            event_manager=integration.event_manager,
        )

    def begin_comparative_model_validation(
        self,
        process_id: UUID,
        *,
        document_id: str,
        model_id: str,
        definitive_catalog_id: str,
    ) -> None:
        self._transition_state(
            process_id,
            MotorState.PROCESANDO,
            f"Iniciando validación del Modelo Comparativo Definitivo: {document_id}",
        )
        self._register_event(
            process_id=process_id,
            message=f"Validación de modelo comparativo iniciada para {document_id}",
            event_type=EventType.MODULE,
            severity=EventSeverity.INFO,
            metadata={
                "document_id": document_id,
                "model_id": model_id,
                "definitive_catalog_id": definitive_catalog_id,
                "phase": "comparative_model_validation",
            },
        )

    def complete_comparative_model_validation(
        self,
        process_id: UUID,
        result: ComparativeModelValidationResult,
    ) -> dict[str, Any]:
        state = self._transition_state(
            process_id,
            MotorState.PROCESAMIENTO_COMPLETADO,
            f"Validación de modelo comparativo completada: {result.document_id}",
        )
        severity = (
            EventSeverity.WARNING
            if result.error_count or result.warning_count
            else EventSeverity.INFO
        )
        message = (
            f"Validación con hallazgos para {result.document_id}"
            if result.findings_count
            else f"Validación completada para {result.document_id}"
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
                "report_id": result.report.report_id,
                "status": result.status.value,
                "findings_count": result.findings_count,
                "error_count": result.error_count,
                "warning_count": result.warning_count,
                "validators_executed": result.validators_executed,
                "definitive_catalog_preserved": result.definitive_catalog_preserved,
                "domain_model_preserved": result.domain_model_preserved,
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
