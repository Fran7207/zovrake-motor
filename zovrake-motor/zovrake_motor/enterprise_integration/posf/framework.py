"""
Performance Optimization & Scalability Framework — núcleo de optimización transversal.

Único responsable de optimizar rendimiento y preparar escalabilidad empresarial.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from zovrake_motor.enterprise_integration.posf.async_advisor import AsyncProcessingAdvisor
from zovrake_motor.enterprise_integration.posf.enums import ResourceKind
from zovrake_motor.enterprise_integration.posf.events import PosfEventRecorder
from zovrake_motor.enterprise_integration.posf.pipeline_analyzer import PipelineAnalyzer
from zovrake_motor.enterprise_integration.posf.ports import PerformanceMetricsSourcePort
from zovrake_motor.enterprise_integration.posf.resource_optimizer import ResourceOptimizer
from zovrake_motor.enterprise_integration.posf.reuse_registry import SafeReuseRegistry
from zovrake_motor.enterprise_integration.posf.scalability_planner import ScalabilityPlanner

if TYPE_CHECKING:
    from zovrake_motor.enterprise_integration.integration import EnterpriseIntegrationMotorIntegration


class PerformanceOptimizationScalabilityFramework:
    """
    Framework de optimización de rendimiento y escalabilidad.

    Capa transversal que no altera el comportamiento funcional del sistema.
    """

    MODULE_NAME = "PerformanceOptimizationScalabilityFramework"

    def __init__(
        self,
        *,
        integration: EnterpriseIntegrationMotorIntegration,
        pipeline_analyzer: PipelineAnalyzer | None = None,
        resource_optimizer: ResourceOptimizer | None = None,
        async_advisor: AsyncProcessingAdvisor | None = None,
        reuse_registry: SafeReuseRegistry | None = None,
        scalability_planner: ScalabilityPlanner | None = None,
        event_recorder: PosfEventRecorder | None = None,
    ) -> None:
        self._integration = integration
        self._pipeline = pipeline_analyzer or PipelineAnalyzer()
        self._resources = resource_optimizer or ResourceOptimizer()
        self._async = async_advisor or AsyncProcessingAdvisor()
        self._reuse = reuse_registry or SafeReuseRegistry()
        self._scalability = scalability_planner or ScalabilityPlanner()
        self._events = event_recorder or PosfEventRecorder(integration)
        self._metrics_source: PerformanceMetricsSourcePort | None = None
        self._optimizations_applied = 0
        self._initialized = False

    def bind_metrics_source(self, source: PerformanceMetricsSourcePort) -> None:
        self._metrics_source = source

    def initialize(self) -> None:
        settings = self._settings()
        self._async = AsyncProcessingAdvisor(
            congestion_threshold=settings.queue_congestion_threshold,
        )
        self._scalability = ScalabilityPlanner(
            horizontal_prepared=settings.horizontal_scaling_prepared,
            vertical_prepared=settings.vertical_scaling_prepared,
            load_balancing_prepared=settings.load_balancing_prepared,
            auto_scaling_prepared=settings.auto_scaling_prepared,
            multi_node_prepared=settings.multi_node_prepared,
        )
        ei_settings = self._integration.enterprise_integration_settings()
        self._reuse.register_configuration(
            "enterprise_integration",
            {
                "max_concurrent_integrations": ei_settings.max_concurrent_integrations,
                "max_requests_per_process": ei_settings.max_requests_per_process,
            },
        )
        self._reuse.register_contract(
            "internal_api_v1",
            {"active_version": "v1", "prepared": True},
        )
        self._initialized = True

    def is_ready(self) -> bool:
        return self._initialized and self._settings().prepared

    def _settings(self):
        return (
            self._integration.enterprise_integration_settings().performance_optimization_scalability_framework
        )

    def _enabled(self) -> bool:
        settings = self._settings()
        return settings.enabled and settings.prepared and self.is_ready()

    def record_pipeline_transition(
        self,
        *,
        process_id: UUID,
        phase: str,
        operation: str,
        transition_count: int,
        project_id: str = "",
        quotation_id: str = "",
    ) -> None:
        if not self._enabled():
            return
        self._resources.record(
            kind=ResourceKind.CPU,
            units=1,
            component="PipelineIntegrationOrchestrator",
        )
        hint = self._pipeline.record_transition(
            process_id=process_id,
            phase=phase,
            operation=operation,
            transition_count=transition_count,
        )
        self._events.record_pipeline_analysis(
            process_id,
            phase=phase,
            operation=operation,
        )
        if hint is not None:
            self._optimizations_applied += 1
            self._events.record_optimization_applied(
                process_id,
                strategy=hint.strategy.value,
                component=hint.component,
                message=hint.message,
            )
        self._sync_state(process_id)
        _ = project_id, quotation_id

    def record_queue_metrics(
        self,
        *,
        process_id: UUID | None,
        queue_depth: int,
        pending_count: int,
        active_count: int,
        max_workers: int,
    ) -> None:
        if not self._enabled():
            return
        self._resources.record(
            kind=ResourceKind.SHARED,
            units=queue_depth,
            component="AsyncProcessingQueueManager",
        )
        hint = self._async.evaluate_queue(
            process_id=process_id,
            queue_depth=queue_depth,
            pending_count=pending_count,
            active_count=active_count,
            max_workers=max_workers,
        )
        if hint is not None:
            self._optimizations_applied += 1
            self._events.record_optimization_applied(
                process_id,
                strategy=hint.strategy.value,
                component=hint.component,
                message=hint.message,
            )
        if process_id is not None:
            self._sync_state(process_id)

    def record_resource_allocation(
        self,
        *,
        process_id: UUID | None,
        component: str,
        memory_units: int = 0,
        cpu_units: int = 0,
        storage_units: int = 0,
    ) -> None:
        if not self._enabled():
            return
        if memory_units:
            self._resources.record(
                kind=ResourceKind.MEMORY,
                units=memory_units,
                component=component,
            )
            self._events.record_resource_usage(
                process_id,
                kind=ResourceKind.MEMORY.value,
                units=memory_units,
                component=component,
            )
        if cpu_units:
            self._resources.record(
                kind=ResourceKind.CPU,
                units=cpu_units,
                component=component,
            )
        if storage_units:
            self._resources.record(
                kind=ResourceKind.TEMP_STORAGE,
                units=storage_units,
                component=component,
            )
        if process_id is not None:
            self._sync_state(process_id)

    def evaluate_from_metrics(self) -> dict[str, Any]:
        """Evalúa rendimiento consumiendo métricas del OMMF."""
        if self._metrics_source is None:
            return {"evaluated": False, "reason": "metrics_source_not_bound"}

        metrics = self._metrics_source.observability_snapshot()
        ei_settings = self._integration.enterprise_integration_settings()
        concurrent = metrics.get("requests_processed", 0)
        mode = self._scalability.evaluate_capacity(
            concurrent_processes=concurrent,
            max_concurrent_integrations=ei_settings.max_concurrent_integrations,
        )

        if metrics.get("validations_performed", 0) > 0:
            self._events.record_performance_improvement(
                None,
                component=self.MODULE_NAME,
                detail="Validaciones registradas — flujo operativo estable",
            )

        return {
            "evaluated": True,
            "ommf_metrics": metrics,
            "scalability_mode": mode.value,
            "optimizations_applied": self._optimizations_applied,
        }

    def _sync_state(self, process_id: UUID) -> None:
        state_manager = self._integration.state_manager
        record = state_manager.get_process(process_id)
        if record is None:
            return
        self._events.record_state_sync(process_id, motor_state=record.current_state.value)

    def optimization_snapshot(self) -> dict[str, Any]:
        evaluation = self.evaluate_from_metrics()
        return {
            "optimizations_applied": self._optimizations_applied,
            "pipeline": self._pipeline.snapshot(),
            "resources": self._resources.snapshot(),
            "async": self._async.snapshot(),
            "reuse": self._reuse.snapshot(),
            "scalability": self._scalability.snapshot(),
            "metrics_evaluation": evaluation,
        }

    def snapshot(self) -> dict[str, Any]:
        settings = self._settings()
        return {
            "initialized": self._initialized,
            "ready": self.is_ready(),
            "enabled": settings.enabled,
            "prepared": settings.prepared,
            "metrics_source_bound": self._metrics_source is not None,
            "optimization": self.optimization_snapshot(),
            "load_balancing_prepared": settings.load_balancing_prepared,
            "auto_scaling_prepared": settings.auto_scaling_prepared,
            "kubernetes_prepared": settings.kubernetes_prepared,
            "multi_datacenter_prepared": settings.multi_datacenter_prepared,
        }
