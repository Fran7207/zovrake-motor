"""Eventos del POSF — Sistema Centralizado de Eventos."""

from __future__ import annotations

from uuid import UUID

from zovrake_motor.enterprise_integration.integration import EnterpriseIntegrationMotorIntegration
from zovrake_motor.events.enums import EventCategory, EventSeverity, EventType


class PosfEventRecorder:
    """Registra eventos de optimización, recursos y rendimiento."""

    MODULE_NAME = "PerformanceOptimizationScalabilityFramework"

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

    def record_optimization_applied(
        self,
        process_id: UUID | None,
        *,
        strategy: str,
        component: str,
        message: str,
    ) -> None:
        self._register(
            process_id,
            event_type=EventType.MODULE,
            message=message,
            severity=EventSeverity.INFO,
            metadata={"strategy": strategy, "component": component},
        )

    def record_resource_usage(
        self,
        process_id: UUID | None,
        *,
        kind: str,
        units: int,
        component: str,
    ) -> None:
        self._register(
            process_id,
            event_type=EventType.SYSTEM,
            message=f"Uso de recurso {kind}",
            severity=EventSeverity.INFO,
            metadata={"kind": kind, "units": units, "component": component},
        )

    def record_performance_improvement(
        self,
        process_id: UUID | None,
        *,
        component: str,
        detail: str,
    ) -> None:
        self._register(
            process_id,
            event_type=EventType.FINALIZED,
            message="Mejora de rendimiento registrada",
            severity=EventSeverity.INFO,
            metadata={"component": component, "detail": detail},
        )

    def record_pipeline_analysis(
        self,
        process_id: UUID,
        *,
        phase: str,
        operation: str,
    ) -> None:
        self._register(
            process_id,
            event_type=EventType.PIPELINE,
            message="Análisis de Pipeline registrado",
            severity=EventSeverity.INFO,
            metadata={"phase": phase, "operation": operation},
            category=EventCategory.COORDINATION,
        )

    def record_state_sync(self, process_id: UUID, *, motor_state: str) -> None:
        self._register(
            process_id,
            event_type=EventType.STATE_CHANGE,
            message="Sincronización de estado POSF",
            severity=EventSeverity.INFO,
            metadata={"motor_state": motor_state},
            category=EventCategory.STATE,
        )
