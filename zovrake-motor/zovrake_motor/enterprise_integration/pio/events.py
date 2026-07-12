"""Eventos del Pipeline de Integración — Sistema Centralizado de Eventos."""

from __future__ import annotations

from uuid import UUID

from zovrake_motor.events.enums import EventCategory, EventSeverity, EventType
from zovrake_motor.enterprise_integration.pio.enums import IntegrationPipelinePhase
from zovrake_motor.enterprise_integration.integration import EnterpriseIntegrationMotorIntegration


class PipelineEventRecorder:
    """Registra eventos del ciclo de vida del Pipeline."""

    MODULE_NAME = "PipelineIntegrationOrchestrator"

    def __init__(self, integration: EnterpriseIntegrationMotorIntegration) -> None:
        self._event_manager = integration.event_manager

    def record_phase_transition(
        self,
        process_id: UUID,
        *,
        phase: IntegrationPipelinePhase,
        operation: str,
        reason: str = "",
    ) -> None:
        event = self._event_manager.create_event(
            process_id=process_id,
            module=self.MODULE_NAME,
            event_type=EventType.PIPELINE,
            message=f"Fase {phase.value}",
            associated_state=phase.value,
            metadata={"operation": operation, "reason": reason},
            category=EventCategory.COORDINATION,
            severity=EventSeverity.INFO,
        )
        self._event_manager.register_event(event)

    def record_orchestration_completed(
        self,
        process_id: UUID,
        *,
        operation: str,
        success: bool,
    ) -> None:
        event = self._event_manager.create_event(
            process_id=process_id,
            module=self.MODULE_NAME,
            event_type=EventType.FINALIZED if success else EventType.SYSTEM,
            message=f"Orquestación {operation} completada",
            metadata={"operation": operation, "success": success},
            category=EventCategory.COORDINATION,
            severity=EventSeverity.INFO if success else EventSeverity.WARNING,
        )
        self._event_manager.register_event(event)
