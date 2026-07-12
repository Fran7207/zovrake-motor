"""
Coordinator Central del Motor Inteligente ZOVRAKE.

Único componente autorizado para coordinar el flujo interno.
Los módulos nunca se comunican directamente entre sí.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from zovrake_motor.config.provider import ConfigurationProvider
from zovrake_motor.config.settings import MotorSettings
from zovrake_motor.coordinator.enums import CoordinatorState
from zovrake_motor.coordinator.events import EventCollector
from zovrake_motor.coordinator.lifecycle import LifecycleManager
from zovrake_motor.coordinator.models import CoordinationProcess, CoordinationResult
from zovrake_motor.coordinator.module_administrator import (
    ModuleAdministrator,
    ModuleDiscoveryResult,
    ModuleStatus,
)
from zovrake_motor.coordinator.pipeline import CoordinationPipeline, PipelineStage
from zovrake_motor.coordinator.ports import ModulePort
from zovrake_motor.coordinator.registry import ModuleRegistry
from zovrake_motor.processing import (
    InternalPipeline,
    PipelineContext,
    PipelineController,
    PipelineResult,
    PipelineStageDefinition,
    PipelineStageType,
)
from zovrake_motor.states import MotorState, ProcessStateRecord, StateManager
from zovrake_motor.events import (
    EventCategory,
    EventManager,
    EventType,
    MotorEvent,
)


class MotorCoordinator:
    """
    Núcleo de coordinación del Motor Inteligente.

    Responsabilidad única: orquestar el flujo interno y administrar módulos.
    No contiene lógica de negocio.
    """

    MODULE_NAME = "MotorCoordinator"

    def __init__(
        self,
        *,
        settings: MotorSettings | None = None,
        config_provider: ConfigurationProvider | None = None,
        module_registry: ModuleRegistry | None = None,
        module_administrator: ModuleAdministrator | None = None,
        event_collector: EventCollector | None = None,
        lifecycle_manager: LifecycleManager | None = None,
        pipeline_controller: PipelineController | None = None,
        state_manager: StateManager | None = None,
        event_manager: EventManager | None = None,
    ) -> None:
        if config_provider is not None:
            self._config = config_provider
        elif settings is not None:
            self._config = ConfigurationProvider.from_general(settings)
        else:
            self._config = ConfigurationProvider.default()
        self._admin = module_administrator or ModuleAdministrator(registry=module_registry)
        self._events = event_collector or EventCollector()
        self._lifecycle = lifecycle_manager or LifecycleManager()
        self._pipeline_controller = pipeline_controller or PipelineController()
        self._state_manager = state_manager or StateManager()
        self._event_manager = event_manager or EventManager(
            max_events_per_process=self._config.events().max_events_in_memory,
        )
        self._state = CoordinatorState.INICIALIZADO
        self._processes: dict[UUID, CoordinationProcess] = {}

        self._initialize()

    @property
    def state(self) -> CoordinatorState:
        return self._state

    @property
    def module_registry(self) -> ModuleRegistry:
        return self._admin.registry

    @property
    def module_administrator(self) -> ModuleAdministrator:
        return self._admin

    @property
    def event_collector(self) -> EventCollector:
        return self._events

    @property
    def config_provider(self) -> ConfigurationProvider:
        return self._config

    @property
    def settings(self) -> MotorSettings:
        return self._config.general()

    @property
    def active_process_count(self) -> int:
        return len(self._processes)

    def is_ready(self) -> bool:
        return self._state == CoordinatorState.PREPARADO

    def register_module(self, module: ModulePort) -> None:
        """Registra un módulo interno mediante composición."""
        self._admin.register(module)
        self._evaluate_readiness()

    def get_module(self, name: str) -> ModulePort | None:
        return self._admin.get(name)

    def require_module(self, name: str) -> ModulePort:
        return self._admin.require(name)

    def is_module_available(self, name: str) -> bool:
        return self._admin.is_available(name)

    def list_modules(self) -> list[str]:
        return self._admin.list_modules()

    def discover_modules(self) -> ModuleDiscoveryResult:
        return self._admin.discover()

    def validate_base_modules(self) -> bool:
        return self._admin.validate_base_modules()

    def initialize_modules(self) -> None:
        self._admin.initialize_all()
        self._evaluate_readiness()

    def prepare_modules(self) -> None:
        self._admin.prepare_all()
        self._evaluate_readiness()

    def finalize_modules(self) -> None:
        self._admin.finalize_all()

    def get_module_status(self, name: str) -> ModuleStatus:
        return self._admin.get_status(name)

    def get_pipeline_stages(self) -> tuple[PipelineStage, ...]:
        return CoordinationPipeline.MAIN_STAGES

    def get_pipeline_snapshot(self) -> list[dict[str, Any]]:
        return CoordinationPipeline.build_snapshot(self._admin)

    @property
    def pipeline_controller(self) -> PipelineController:
        return self._pipeline_controller

    @property
    def internal_pipeline(self) -> InternalPipeline:
        return self._pipeline_controller.pipeline

    def get_internal_pipeline_stages(self) -> tuple[PipelineStageDefinition, ...]:
        return self.internal_pipeline.stages

    def get_internal_pipeline_snapshot(self) -> list[dict[str, Any]]:
        return self.internal_pipeline.snapshot()

    def start_pipeline(
        self,
        process_id: UUID,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> PipelineContext:
        """Inicia el Pipeline Interno — exclusivo del Coordinator."""
        return self._pipeline_controller.start(process_id, metadata=metadata)

    def advance_pipeline(self, process_id: UUID) -> PipelineContext:
        """Avanza secuencialmente al siguiente paso del Pipeline."""
        return self._pipeline_controller.advance(process_id)

    def run_internal_pipeline(
        self,
        process_id: UUID,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> PipelineResult:
        """Recorre todas las etapas del Pipeline sin procesamiento real."""
        return self._pipeline_controller.run_sequential(process_id, metadata=metadata)

    def stop_pipeline(self, process_id: UUID, *, reason: str) -> PipelineContext:
        """Detiene el Pipeline Interno."""
        return self._pipeline_controller.stop(process_id, reason=reason)

    def finalize_pipeline(self, process_id: UUID) -> PipelineContext:
        """Finaliza el recorrido del Pipeline Interno."""
        return self._pipeline_controller.finalize(process_id)

    def get_pipeline_context(self, process_id: UUID) -> PipelineContext | None:
        return self._pipeline_controller.get_context(process_id)

    @property
    def state_manager(self) -> StateManager:
        return self._state_manager

    def create_process_state(
        self,
        process_id: UUID,
        codigo_req: str,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> ProcessStateRecord:
        """Crea el estado inicial de una solicitud — exclusivo del Coordinator."""
        return self._state_manager.create_process(
            process_id,
            codigo_req,
            metadata=metadata,
        )

    def get_process_state(self, process_id: UUID) -> ProcessStateRecord | None:
        return self._state_manager.get_process(process_id)

    def transition_process_state(
        self,
        process_id: UUID,
        to_state: MotorState,
        reason: str,
    ) -> ProcessStateRecord:
        """Actualiza el estado de una solicitud — exclusivo del Coordinator."""
        return self._state_manager.update_state(process_id, to_state, reason)

    def get_state_snapshot(self) -> dict[str, Any]:
        return self._state_manager.snapshot()

    @property
    def event_manager(self) -> EventManager:
        return self._event_manager

    def create_event(
        self,
        *,
        process_id: UUID,
        module: str,
        event_type: EventType,
        message: str,
        associated_state: str | None = None,
        metadata: dict[str, Any] | None = None,
        category: EventCategory = EventCategory.COORDINATION,
    ) -> MotorEvent:
        """Crea un evento sin registrarlo — coordinación exclusiva del Coordinator."""
        return self._event_manager.create_event(
            process_id=process_id,
            module=module,
            event_type=event_type,
            message=message,
            associated_state=associated_state,
            metadata=metadata,
            category=category,
        )

    def register_event(self, event: MotorEvent) -> MotorEvent:
        """Registra un evento en el EMS — exclusivo del Coordinator."""
        return self._event_manager.register_event(event)

    def register_coordination_event(
        self,
        *,
        process_id: UUID,
        message: str,
        event_type: EventType = EventType.COORDINATION,
        associated_state: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> MotorEvent:
        return self._event_manager.create_and_register(
            process_id=process_id,
            module=self.MODULE_NAME,
            event_type=event_type,
            message=message,
            associated_state=associated_state,
            metadata=metadata,
            category=EventCategory.COORDINATION,
        )

    def get_process_events(self, process_id: UUID) -> list[MotorEvent]:
        return self._event_manager.get_process_history(process_id)

    def finalize_event(self, event_id: UUID) -> MotorEvent:
        return self._event_manager.finalize_event(event_id)

    def get_event_snapshot(self) -> dict[str, Any]:
        return self._event_manager.snapshot()

    def initialize(self) -> None:
        """Reinicia el ciclo de vida del Coordinator."""
        self._initialize()

    def coordinate(
        self,
        *,
        process_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> CoordinationResult:
        """
        Ejecuta un ciclo de coordinación.

        Recorre las fases del ciclo de vida y la estructura del pipeline
        sin procesamiento de negocio.
        """
        if not self.is_ready():
            return self._error_result(
                message=f"Coordinator no está preparado. Estado actual: {self._state.value}",
            )

        if not self.validate_base_modules():
            return self._error_result(
                message="Módulos base no registrados o no disponibles",
            )

        process = CoordinationProcess(
            process_id=process_id or CoordinationProcess().process_id,
            metadata=metadata or {},
        )
        self._processes[process.process_id] = process

        try:
            codigo_req = str((metadata or {}).get("codigo_req", process.process_id))
            process_state = self.create_process_state(
                process.process_id,
                codigo_req,
                metadata=metadata,
            )
            self.register_coordination_event(
                process_id=process.process_id,
                message="Proceso de coordinación iniciado",
                event_type=EventType.CREATED,
                associated_state=process_state.current_state.value,
            )

            self._transition(CoordinatorState.COORDINANDO, "Iniciando coordinación", process.process_id)
            process.state = CoordinatorState.COORDINANDO

            phases = self._lifecycle.run_lifecycle(process)
            module_pipeline_snapshot = self.get_pipeline_snapshot()
            internal_pipeline_result = self.run_internal_pipeline(
                process.process_id,
                metadata=metadata or {},
            )

            process_state = self.transition_process_state(
                process.process_id,
                MotorState.FINALIZADO,
                "Coordinación completada sin lógica de negocio",
            )
            completion_event = self.register_coordination_event(
                process_id=process.process_id,
                message="Coordinación completada",
                event_type=EventType.FINALIZED,
                associated_state=process_state.current_state.value,
            )
            self.finalize_event(completion_event.event_id)

            self._transition(CoordinatorState.FINALIZADO, "Coordinación completada", process.process_id)
            process.state = CoordinatorState.FINALIZADO

            return CoordinationResult(
                process_id=process.process_id,
                success=True,
                state=CoordinatorState.FINALIZADO,
                message="Ciclo de coordinación completado sin lógica de negocio",
                phases_completed=phases,
                metadata={
                    "module_count": self._admin.count(),
                    "modules": [status.to_dict() for status in self._admin.all_statuses()],
                    "pipeline": module_pipeline_snapshot,
                    "internal_pipeline": internal_pipeline_result.to_dict(),
                    "process_state": process_state.to_dict(),
                    "process_events": [
                        event.to_dict()
                        for event in self.get_process_events(process.process_id)
                    ],
                    "event_management": self.get_event_snapshot(),
                    "discovery": self.discover_modules().to_dict(),
                },
            )

        except Exception as exc:
            self._transition(CoordinatorState.ERROR_INTERNO, str(exc), process.process_id)
            process.state = CoordinatorState.ERROR_INTERNO
            return CoordinationResult(
                process_id=process.process_id,
                success=False,
                state=CoordinatorState.ERROR_INTERNO,
                message=str(exc),
            )

    def get_process(self, process_id: UUID) -> CoordinationProcess | None:
        return self._processes.get(process_id)

    def snapshot(self) -> dict[str, Any]:
        discovery = self.discover_modules()
        return {
            "coordinator_state": self._state.value,
            "is_ready": self.is_ready(),
            "active_processes": self.active_process_count,
            "registered_modules": self.list_modules(),
            "planned_modules": list(self._admin.registry.planned_modules()),
            "base_modules_valid": self.validate_base_modules(),
            "discovery": discovery.to_dict(),
            "pipeline": self.get_pipeline_snapshot(),
            "internal_pipeline": self.get_internal_pipeline_snapshot(),
            "state_management": self.get_state_snapshot(),
            "event_management": self.get_event_snapshot(),
            "events_recorded": self._events.count(),
            "ems_total_events": self._event_manager.count(),
            "service_version": self._config.service_version(),
            "environment": self._config.environment().value,
            "configuration": self._config.snapshot(),
        }

    def shutdown(self) -> None:
        self.finalize_modules()
        self._transition(CoordinatorState.FINALIZADO, "Coordinator detenido")
        self._processes.clear()

    def _initialize(self) -> None:
        self._transition(CoordinatorState.INICIALIZADO, "Coordinator creado")
        self._transition(
            CoordinatorState.ESPERANDO_MODULOS,
            "Esperando registro de módulos",
        )
        self._evaluate_readiness()

    def _evaluate_readiness(self) -> None:
        if self.validate_base_modules():
            if self._state != CoordinatorState.PREPARADO:
                self._transition(
                    CoordinatorState.PREPARADO,
                    "Todos los módulos base registrados y disponibles",
                )
        elif self._state == CoordinatorState.PREPARADO:
            self._transition(
                CoordinatorState.ESPERANDO_MODULOS,
                "Módulos base incompletos o no disponibles",
            )

    def _transition(
        self,
        to_state: CoordinatorState,
        reason: str,
        process_id: UUID | None = None,
    ) -> None:
        from_state = self._state
        self._state = to_state
        self._events.emit_state_change(
            from_state=from_state,
            to_state=to_state,
            message=reason,
            process_id=process_id,
        )
        if process_id is not None:
            self.register_coordination_event(
                process_id=process_id,
                message=reason,
                event_type=EventType.STATE_CHANGE,
                associated_state=to_state.value,
                metadata={"from_state": from_state.value, "to_state": to_state.value},
            )

    def _error_result(self, *, message: str) -> CoordinationResult:
        return CoordinationResult(
            process_id=CoordinationProcess().process_id,
            success=False,
            state=self._state,
            message=message,
        )
