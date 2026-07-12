"""
Observability, Metrics & Monitoring Framework — núcleo de observabilidad transversal.

Único responsable de recopilar métricas, trazas e indicadores operativos.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from zovrake_motor.enterprise_integration.ommf.enums import (
    ComponentHealthStatus,
    PerformanceMetricKind,
)
from zovrake_motor.enterprise_integration.ommf.events import OmmfEventRecorder
from zovrake_motor.enterprise_integration.ommf.health_monitor import HealthMonitor
from zovrake_motor.enterprise_integration.ommf.metrics_collector import MetricsCollector
from zovrake_motor.enterprise_integration.ommf.performance_tracker import PerformanceTracker
from zovrake_motor.enterprise_integration.ommf.ports import ObservabilitySourcePort
from zovrake_motor.enterprise_integration.ommf.trace_collector import TraceCollector

if TYPE_CHECKING:
    from zovrake_motor.enterprise_integration.integration import EnterpriseIntegrationMotorIntegration


class ObservabilityMetricsMonitoringFramework:
    """
    Framework de observabilidad, métricas y monitoreo.

    Capa transversal que no altera el flujo operativo del sistema.
    """

    MODULE_NAME = "ObservabilityMetricsMonitoringFramework"

    def __init__(
        self,
        *,
        integration: EnterpriseIntegrationMotorIntegration,
        metrics: MetricsCollector | None = None,
        traces: TraceCollector | None = None,
        performance: PerformanceTracker | None = None,
        health: HealthMonitor | None = None,
        event_recorder: OmmfEventRecorder | None = None,
    ) -> None:
        self._integration = integration
        self._metrics = metrics or MetricsCollector()
        self._traces = traces or TraceCollector()
        self._performance = performance or PerformanceTracker()
        self._health = health or HealthMonitor()
        self._events = event_recorder or OmmfEventRecorder(integration)
        self._source: ObservabilitySourcePort | None = None
        self._consolidated: dict[str, Any] = {}
        self._initialized = False

    def bind_source(self, source: ObservabilitySourcePort) -> None:
        self._source = source

    def initialize(self) -> None:
        self._initialized = True
        for component in (
            "PipelineIntegrationOrchestrator",
            "AsyncProcessingQueueManager",
            "FaultToleranceRetryRecoveryFramework",
            "SecurityValidationAuditFramework",
            "ErpCommunicationGateway",
        ):
            self._health.update(component, ComponentHealthStatus.AVAILABLE, reason="Inicializado")

    def is_ready(self) -> bool:
        return self._initialized and self._settings().prepared

    def _settings(self):
        return (
            self._integration.enterprise_integration_settings().observability_metrics_monitoring_framework
        )

    def _enabled(self) -> bool:
        settings = self._settings()
        return settings.enabled and settings.prepared and self.is_ready()

    def record_request_received(
        self,
        *,
        process_id: UUID,
        project_id: str = "",
        quotation_id: str = "",
        component: str,
    ) -> None:
        if not self._enabled():
            return
        self._metrics.increment("requests_received")
        self._traces.record(
            process_id=process_id,
            project_id=project_id,
            quotation_id=quotation_id,
            component=component,
            pipeline_phase="solicitud_recibida",
            operation="receive",
            duration_ms=0.0,
        )
        self._events.record_metric(process_id, metric="requests_received", component=component)
        self._sync_state(process_id)

    def record_request_processed(
        self,
        *,
        process_id: UUID,
        component: str,
        success: bool,
        duration_ms: float = 0.0,
        project_id: str = "",
        quotation_id: str = "",
    ) -> None:
        if not self._enabled():
            return
        self._metrics.increment("requests_processed")
        if success:
            self._metrics.increment("processes_successful")
        else:
            self._metrics.increment("processes_failed")
        self._performance.record(
            process_id=process_id,
            kind=PerformanceMetricKind.PROCESSING_TIME,
            component=component,
            duration_ms=duration_ms,
        )
        self._traces.record(
            process_id=process_id,
            project_id=project_id,
            quotation_id=quotation_id,
            component=component,
            pipeline_phase="procesamiento_completado" if success else "procesamiento_fallido",
            operation="process",
            duration_ms=duration_ms,
            metadata={"success": success},
        )
        self._events.record_metric(process_id, metric="requests_processed", component=component)
        self._sync_state(process_id)

    def record_pipeline_transition(
        self,
        *,
        process_id: UUID,
        project_id: str,
        quotation_id: str,
        component: str,
        pipeline_phase: str,
        operation: str,
        duration_ms: float,
    ) -> None:
        if not self._enabled():
            return
        span = self._traces.record(
            process_id=process_id,
            project_id=project_id,
            quotation_id=quotation_id,
            component=component,
            pipeline_phase=pipeline_phase,
            operation=operation,
            duration_ms=duration_ms,
        )
        self._health.update(component, ComponentHealthStatus.BUSY, reason=f"Fase {pipeline_phase}")
        self._events.record_trace(process_id, component=component, phase=pipeline_phase)
        self._performance.record(
            process_id=process_id,
            kind=PerformanceMetricKind.COMPONENT_UTILIZATION,
            component=component,
            duration_ms=duration_ms,
            metadata={"phase": pipeline_phase, "trace_id": span.trace_id},
        )
        self._sync_state(process_id)

    def record_queue_event(
        self,
        *,
        process_id: UUID,
        project_id: str,
        quotation_id: str,
        event: str,
        queue_item_id: str = "",
        duration_ms: float = 0.0,
    ) -> None:
        if not self._enabled():
            return
        component = "AsyncProcessingQueueManager"
        phase_map = {
            "enqueued": "cola_encolado",
            "processing_started": "cola_procesamiento_iniciado",
            "processing_completed": "cola_procesamiento_completado",
            "controlled_error": "cola_error_controlado",
        }
        self._traces.record(
            process_id=process_id,
            project_id=project_id,
            quotation_id=quotation_id,
            component=component,
            pipeline_phase=phase_map.get(event, event),
            operation=event,
            duration_ms=duration_ms,
            metadata={"queue_item_id": queue_item_id},
        )
        if event == "enqueued":
            self._performance.record(
                process_id=process_id,
                kind=PerformanceMetricKind.QUEUE_WAIT_TIME,
                component=component,
                duration_ms=duration_ms,
            )
        elif event in {"processing_started", "processing_completed"}:
            self._performance.record(
                process_id=process_id,
                kind=PerformanceMetricKind.PROCESSING_TIME,
                component=component,
                duration_ms=duration_ms,
            )
        self._health.update(
            component,
            ComponentHealthStatus.BUSY if event == "processing_started" else ComponentHealthStatus.AVAILABLE,
            reason=event,
        )
        self._events.record_trace(process_id, component=component, phase=event)
        self._sync_state(process_id)

    def record_fault_event(
        self,
        *,
        process_id: UUID,
        event: str,
        category: str = "",
        attempt: int = 1,
        duration_ms: float = 0.0,
    ) -> None:
        if not self._enabled():
            return
        component = "FaultToleranceRetryRecoveryFramework"
        if event == "failure":
            self._metrics.increment("processes_failed")
        elif event == "recovery":
            self._metrics.increment("processes_recovered")
            self._health.update(component, ComponentHealthStatus.RECOVERING, reason="Recuperación")
        elif event == "retry":
            self._metrics.increment("retries_executed")
        elif event == "permanent_failure":
            self._metrics.increment("processes_failed")
            self._health.update(component, ComponentHealthStatus.DEGRADED, reason="Fallo permanente")

        self._traces.record(
            process_id=process_id,
            project_id="",
            quotation_id="",
            component=component,
            pipeline_phase=event,
            operation=event,
            duration_ms=duration_ms,
            metadata={"category": category, "attempt": attempt},
        )
        if event in {"recovery", "retry"}:
            self._performance.record(
                process_id=process_id,
                kind=PerformanceMetricKind.RECOVERY_TIME,
                component=component,
                duration_ms=duration_ms,
                metadata={"attempt": attempt},
            )
        self._events.record_metric(process_id, metric=event, component=component)
        self._sync_state(process_id)

    def record_validation_event(
        self,
        *,
        process_id: UUID,
        event: str,
        approved: bool,
        duration_ms: float = 0.0,
        operation: str = "",
    ) -> None:
        if not self._enabled():
            return
        component = "SecurityValidationAuditFramework"
        self._metrics.increment("validations_performed")
        if event == "audit":
            self._metrics.increment("audits_recorded")
        if not approved:
            self._metrics.increment("processes_failed")
        self._performance.record(
            process_id=process_id,
            kind=PerformanceMetricKind.VALIDATION_TIME,
            component=component,
            duration_ms=duration_ms,
            metadata={"operation": operation, "approved": approved},
        )
        self._traces.record(
            process_id=process_id,
            project_id="",
            quotation_id="",
            component=component,
            pipeline_phase=event,
            operation=operation or event,
            duration_ms=duration_ms,
            metadata={"approved": approved},
        )
        self._events.record_metric(process_id, metric=event, component=component)
        self._sync_state(process_id)

    def record_process_cancelled(self, *, process_id: UUID) -> None:
        if not self._enabled():
            return
        self._metrics.increment("processes_cancelled")
        self._traces.record(
            process_id=process_id,
            project_id="",
            quotation_id="",
            component=self.MODULE_NAME,
            pipeline_phase="cancelado",
            operation="cancel",
            duration_ms=0.0,
        )
        self._sync_state(process_id)

    def consolidate(self) -> dict[str, Any]:
        """Consolida información operativa desde fuentes hermanas."""
        sources: dict[str, Any] = {}
        if self._source is not None:
            sources = {
                "pipeline": self._source.pipeline_snapshot(),
                "queue": self._source.queue_snapshot(),
                "fault_tolerance": self._source.fault_snapshot(),
                "security": self._source.security_snapshot(),
            }
        self._consolidated = {
            "metrics": self._metrics.snapshot(),
            "traces": self._traces.snapshot(),
            "performance": self._performance.snapshot(),
            "health": self._health.snapshot(),
            "sources": sources,
        }
        self._events.record_consolidation(
            metrics_count=sum(self._metrics.snapshot().values()),
            traces_count=self._traces.count(),
        )
        return self._consolidated

    def traces_for_process(self, process_id: UUID) -> tuple[dict[str, Any], ...]:
        return tuple(span.to_dict() for span in self._traces.by_process(process_id))

    def _sync_state(self, process_id: UUID) -> None:
        state_manager = self._integration.state_manager
        record = state_manager.get_process(process_id)
        if record is None:
            return
        self._events.record_state_sync(process_id, motor_state=record.current_state.value)

    def observability_snapshot(self) -> dict[str, Any]:
        consolidated = self.consolidate()
        return {
            **consolidated["metrics"],
            "traces_total": self._traces.count(),
            "performance_records": self._performance.count(),
            "health_components": len(self._health.snapshot()),
        }

    def snapshot(self) -> dict[str, Any]:
        settings = self._settings()
        return {
            "initialized": self._initialized,
            "ready": self.is_ready(),
            "enabled": settings.enabled,
            "prepared": settings.prepared,
            "source_bound": self._source is not None,
            "observability": self.observability_snapshot(),
            "consolidated": self._consolidated or self.consolidate(),
            "opentelemetry_prepared": settings.opentelemetry_prepared,
            "prometheus_prepared": settings.prometheus_prepared,
            "grafana_prepared": settings.grafana_prepared,
        }
