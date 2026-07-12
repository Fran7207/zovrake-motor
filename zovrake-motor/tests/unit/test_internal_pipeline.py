"""Pruebas del Pipeline Interno — Implementación 1.7."""

from __future__ import annotations

from uuid import uuid4

import pytest

from zovrake_motor.coordinator import MotorCoordinator
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.communication import CommunicationService
from zovrake_motor.context import ContextService
from zovrake_motor.documents import DocumentService
from zovrake_motor.events import EventManager, EventService
from zovrake_motor.processing import (
    InternalPipeline,
    InvalidStageTransitionError,
    PipelineController,
    PipelineExecutionState,
    PipelineStageDefinition,
    PipelineStageType,
    StageRegistry,
)
from zovrake_motor.reception import ReceptionService
from zovrake_motor.states import StateManager, StateService

BASE_SERVICES = (
    ReceptionService,
    DocumentService,
    ContextService,
    StateService,
    EventService,
    CommunicationService,
)


def _ready_coordinator() -> MotorCoordinator:
    config = ConfigurationProvider.default()
    state_manager = StateManager()
    event_manager = EventManager(max_events_per_process=config.events().max_events_in_memory)
    coordinator = MotorCoordinator(
        config_provider=config,
        state_manager=state_manager,
        event_manager=event_manager,
    )
    for service_cls in BASE_SERVICES:
        kwargs = {"config_provider": config}
        if service_cls is StateService:
            kwargs["state_manager"] = state_manager
        if service_cls is EventService:
            kwargs["event_manager"] = event_manager
        service = service_cls(**kwargs)
        service.initialize()
        coordinator.register_module(service)
    coordinator.prepare_modules()
    return coordinator


class TestInternalPipeline:
    def test_default_stages_registered_in_order(self):
        pipeline = InternalPipeline()
        stages = pipeline.ordered_stage_types()

        assert len(stages) == 7
        assert stages[0] == PipelineStageType.RECEPCION
        assert stages[1] == PipelineStageType.VALIDACION
        assert stages[2] == PipelineStageType.PREPARACION
        assert stages[3] == PipelineStageType.COORDINACION
        assert stages[4] == PipelineStageType.PROCESAMIENTO
        assert stages[5] == PipelineStageType.RESPUESTA
        assert stages[-1] == PipelineStageType.FINALIZACION

    def test_pipeline_initializes_correctly(self):
        controller = PipelineController()
        assert controller.pipeline.stages[0].label == "Recepción"

    def test_sequential_run_completes_all_stages(self):
        controller = PipelineController()
        process_id = uuid4()
        result = controller.run_sequential(process_id)

        assert result.success is True
        assert result.state == PipelineExecutionState.COMPLETADA
        assert len(result.stages_completed) == 7
        assert result.context is not None
        assert len(result.context.stage_records) == 7
        assert len(result.context.transitions) == 6

    def test_advance_does_not_allow_arbitrary_jumps(self):
        controller = PipelineController()
        process_id = uuid4()
        controller.start(process_id)

        context = controller.advance(process_id)
        assert context.current_stage == PipelineStageType.VALIDACION

    def test_stop_and_finalize(self):
        controller = PipelineController()
        process_id = uuid4()
        controller.start(process_id)
        stopped = controller.stop(process_id, reason="detenido para prueba")
        execution = controller.get_execution(process_id)
        assert execution is not None
        assert execution.state == PipelineExecutionState.DETENIDA

        finalized = controller.finalize(process_id)
        assert finalized is not None
        assert execution.state == PipelineExecutionState.FINALIZADA

    def test_cannot_advance_after_completion(self):
        controller = PipelineController()
        process_id = uuid4()
        controller.run_sequential(process_id)

        with pytest.raises(InvalidStageTransitionError):
            controller.advance(process_id)

    def test_custom_pipeline_registry_is_injectable(self):
        subset = InternalPipeline.DEFAULT_STAGES[:3]
        pipeline = InternalPipeline(StageRegistry(subset))
        assert pipeline.ordered_stage_types() == (
            PipelineStageType.RECEPCION,
            PipelineStageType.VALIDACION,
            PipelineStageType.PREPARACION,
        )

    def test_stage_registry_validates_unique_orders(self):
        with pytest.raises(Exception):
            StageRegistry(
                (
                    PipelineStageDefinition(PipelineStageType.RECEPCION, "Recepción", 1),
                    PipelineStageDefinition(PipelineStageType.VALIDACION, "Validación", 1),
                )
            )


class TestCoordinatorPipelineControl:
    def test_coordinator_controls_internal_pipeline(self):
        coordinator = _ready_coordinator()
        process_id = uuid4()

        context = coordinator.start_pipeline(process_id, metadata={"source": "test"})
        assert context.current_stage == PipelineStageType.RECEPCION

        context = coordinator.advance_pipeline(process_id)
        assert context.current_stage == PipelineStageType.VALIDACION

        result = coordinator.run_internal_pipeline(uuid4())
        assert result.success is True
        assert coordinator.get_pipeline_context(result.process_id) is not None

    def test_coordinate_includes_internal_pipeline(self):
        coordinator = _ready_coordinator()
        result = coordinator.coordinate()

        assert result.success is True
        assert "internal_pipeline" in result.metadata
        internal = result.metadata["internal_pipeline"]
        assert len(internal["stages_completed"]) == 7
        assert internal["stages_completed"][0] == "recepcion"
        assert internal["stages_completed"][-1] == "finalizacion"

    def test_snapshot_includes_internal_pipeline_structure(self):
        coordinator = _ready_coordinator()
        snapshot = coordinator.snapshot()

        assert "internal_pipeline" in snapshot
        assert len(snapshot["internal_pipeline"]) == 7

    def test_stages_do_not_depend_on_each_other(self):
        import importlib

        modules = (
            "zovrake_motor.processing.controller",
            "zovrake_motor.processing.stages",
            "zovrake_motor.processing.models",
        )
        for module_name in modules:
            module = importlib.import_module(module_name)
            source_file = module.__file__
            assert source_file is not None
            with open(source_file, encoding="utf-8") as fh:
                content = fh.read()
            assert "zovrake_motor.reception" not in content
            assert "zovrake_motor.documents" not in content
            assert "zovrake_motor.communication" not in content
