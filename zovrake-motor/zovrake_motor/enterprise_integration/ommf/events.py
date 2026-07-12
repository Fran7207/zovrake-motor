"""Eventos del OMMF — Sistema Centralizado de Eventos."""

from __future__ import annotations

from uuid import UUID

from zovrake_motor.enterprise_integration.integration import EnterpriseIntegrationMotorIntegration
from zovrake_motor.events.enums import EventCategory, EventSeverity, EventType


class OmmfEventRecorder:
    """Registra eventos operativos de observabilidad."""

    MODULE_NAME = "ObservabilityMetricsMonitoringFramework"

    def __init__(self, integration: EnterpriseIntegrationMotorIntegration) -> None:
        self._event_manager = integration.event_manager

    def _register(
        self,
        process_id: UUID | None,
        *,
        event_type: EventType,
        message: str,
        severity: EventSeverity,
        metadata: dict | None = None,
        category: EventCategory = EventCategory.SYSTEM,
    ) -> None:
        pid = process_id or UUID(int=0)
        event = self._event_manager.create_event(
            process_id=pid,
            module=self.MODULE_NAME,
            event_type=event_type,
            message=message,
            metadata=dict(metadata or {}),
            category=category,
            severity=severity,
        )
        self._event_manager.register_event(event)

    def record_metric(self, process_id: UUID, *, metric: str, component: str) -> None:
        self._register(
            process_id,
            event_type=EventType.MODULE,
            message=f"Métrica registrada: {metric}",
            severity=EventSeverity.INFO,
            metadata={"metric": metric, "component": component},
        )

    def record_trace(self, process_id: UUID, *, component: str, phase: str) -> None:
        self._register(
            process_id,
            event_type=EventType.PIPELINE,
            message=f"Traza registrada — {component}",
            severity=EventSeverity.INFO,
            metadata={"component": component, "phase": phase},
        )

    def record_health_update(self, *, component: str, status: str) -> None:
        self._register(
            None,
            event_type=EventType.SYSTEM,
            message=f"Salud actualizada — {component}",
            severity=EventSeverity.INFO,
            metadata={"component": component, "status": status},
        )

    def record_consolidation(self, *, metrics_count: int, traces_count: int) -> None:
        self._register(
            None,
            event_type=EventType.FINALIZED,
            message="Consolidación de observabilidad",
            severity=EventSeverity.INFO,
            metadata={"metrics_count": metrics_count, "traces_count": traces_count},
        )

    def record_state_sync(self, process_id: UUID, *, motor_state: str) -> None:
        self._register(
            process_id,
            event_type=EventType.STATE_CHANGE,
            message="Sincronización de estado OMMF",
            severity=EventSeverity.INFO,
            metadata={"motor_state": motor_state},
            category=EventCategory.STATE,
        )
