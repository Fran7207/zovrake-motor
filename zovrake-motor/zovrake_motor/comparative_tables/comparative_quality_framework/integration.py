"""Integración del CQF con estados y eventos del núcleo."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from zovrake_motor.comparative_tables.comparative_quality_framework.models import (
    ComparativeQualityValidationResult,
)
from zovrake_motor.events.enums import EventCategory, EventSeverity, EventType
from zovrake_motor.events.manager import EventManager
from zovrake_motor.states.enums import MotorState
from zovrake_motor.states.manager import StateManager

if TYPE_CHECKING:
    from zovrake_motor.comparative_tables.integration import ComparativeTablesMotorIntegration


class ComparativeQualityMotorIntegration:
    """Puente de integración del CQF con StateManager y EventManager."""

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
    ) -> ComparativeQualityMotorIntegration:
        return cls(
            state_manager=integration.state_manager,
            event_manager=integration.event_manager,
        )

    def begin_quality_audit(
        self,
        process_id: UUID,
        *,
        document_id: str,
        model_id: str,
        definitive_catalog_id: str,
        validation_report_id: str,
    ) -> None:
        self._transition_state(
            process_id,
            MotorState.PROCESANDO,
            f"Iniciando auditoría de calidad: {document_id}",
        )
        self._register_event(
            process_id=process_id,
            message=f"Auditoría de calidad iniciada para {document_id}",
            event_type=EventType.MODULE,
            severity=EventSeverity.INFO,
            metadata={
                "document_id": document_id,
                "model_id": model_id,
                "definitive_catalog_id": definitive_catalog_id,
                "validation_report_id": validation_report_id,
                "phase": "comparative_quality_audit",
            },
        )

    def complete_quality_audit(
        self,
        process_id: UUID,
        result: ComparativeQualityValidationResult,
    ) -> dict[str, Any]:
        state = self._transition_state(
            process_id,
            MotorState.PROCESAMIENTO_COMPLETADO,
            f"Auditoría de calidad completada: {result.document_id}",
        )
        has_issues = result.report.checks_failed > 0 or result.report.findings
        severity = EventSeverity.WARNING if has_issues else EventSeverity.INFO
        message = (
            f"Auditoría de calidad con hallazgos para {result.document_id}"
            if has_issues
            else f"Auditoría de calidad completada para {result.document_id}"
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
                "validation_report_id": result.report.validation_report_id,
                "checks_executed": result.report.checks_executed,
                "checks_passed": result.report.checks_passed,
                "checks_failed": result.report.checks_failed,
                "overall_status": result.status.value,
                "module_certification_prepared": result.report.module_certification_prepared,
                "definitive_catalog_preserved": result.definitive_catalog_preserved,
                "validation_report_preserved": result.validation_report_preserved,
                "validators_executed": result.validators_executed,
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
