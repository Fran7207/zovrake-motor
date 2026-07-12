"""Pruebas del Sistema de Gestión de Estados — Implementación 1.8."""

from __future__ import annotations

from uuid import uuid4

import pytest

from zovrake_motor.communication import CommunicationService
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.context import ContextService
from zovrake_motor.coordinator import MotorCoordinator
from zovrake_motor.documents import DocumentService
from zovrake_motor.events import EventManager, EventService
from zovrake_motor.reception import ReceptionService
from zovrake_motor.states import (
    MotorState,
    ProcessNotFoundError,
    StateLifecycle,
    StateManagementError,
    StateManager,
    StateService,
)
from zovrake_motor.states.models import StateTransition

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


class TestOfficialStates:
    def test_all_official_states_defined(self):
        states = MotorState.official_states()
        assert len(states) == 11
        assert MotorState.INICIALIZADO in states
        assert MotorState.ESPERANDO_INFORMACION in states
        assert MotorState.VALIDANDO_INFORMACION in states
        assert MotorState.INFORMACION_RECIBIDA in states
        assert MotorState.PREPARANDO_PROCESAMIENTO in states
        assert MotorState.PROCESAMIENTO_PENDIENTE in states
        assert MotorState.PROCESANDO in states
        assert MotorState.PROCESAMIENTO_COMPLETADO in states
        assert MotorState.FINALIZADO in states
        assert MotorState.ERROR_VALIDACION in states
        assert MotorState.ERROR_INTERNO in states

    def test_lifecycle_conceptual_flow(self):
        lifecycle = StateLifecycle()
        assert lifecycle.CONCEPTUAL_FLOW[0] == MotorState.INICIALIZADO
        assert lifecycle.CONCEPTUAL_FLOW[-1] == MotorState.FINALIZADO


class TestStateManager:
    def test_initializes_correctly(self):
        manager = StateManager()
        assert manager.count() == 0

    def test_each_request_maintains_independent_state(self):
        manager = StateManager()
        id_a = uuid4()
        id_b = uuid4()

        manager.create_process(id_a, "REQ-A")
        manager.create_process(id_b, "REQ-B")
        manager.update_state(id_a, MotorState.VALIDANDO_INFORMACION, "validando A")

        record_a = manager.get_process(id_a)
        record_b = manager.get_process(id_b)

        assert record_a is not None
        assert record_b is not None
        assert record_a.current_state == MotorState.VALIDANDO_INFORMACION
        assert record_b.current_state == MotorState.INICIALIZADO

    def test_create_process_starts_inicializado(self):
        manager = StateManager()
        process_id = uuid4()
        record = manager.create_process(process_id, "REQ-001")
        assert record.current_state == MotorState.INICIALIZADO

    def test_update_state_records_transition(self):
        manager = StateManager()
        process_id = uuid4()
        manager.create_process(process_id, "REQ-002")
        updated = manager.update_state(
            process_id,
            MotorState.ESPERANDO_INFORMACION,
            "esperando datos",
        )
        assert updated.current_state == MotorState.ESPERANDO_INFORMACION
        assert len(updated.history) == 1
        assert updated.history[0].from_state == MotorState.INICIALIZADO

    def test_duplicate_process_raises(self):
        manager = StateManager()
        process_id = uuid4()
        manager.create_process(process_id, "REQ-003")
        with pytest.raises(StateManagementError):
            manager.create_process(process_id, "REQ-003")

    def test_missing_process_raises(self):
        manager = StateManager()
        with pytest.raises(ProcessNotFoundError):
            manager.update_state(uuid4(), MotorState.FINALIZADO, "test")

    def test_observer_notification_prepared(self):
        manager = StateManager()
        observed: list[StateTransition] = []

        class _Observer:
            def on_state_change(self, record, transition):
                observed.append(transition)

        manager.register_observer(_Observer())
        process_id = uuid4()
        manager.create_process(process_id, "REQ-004")
        manager.update_state(process_id, MotorState.FINALIZADO, "done")

        assert len(observed) == 1
        assert observed[0].to_state == MotorState.FINALIZADO


class TestStateServiceIntegration:
    def test_service_delegates_to_shared_manager(self):
        manager = StateManager()
        service = StateService(state_manager=manager)
        process_id = uuid4()
        service.create_process(process_id, "REQ-005")
        assert manager.count() == 1


class TestCoordinatorStateControl:
    def test_coordinator_is_only_entry_for_transitions(self):
        coordinator = _ready_coordinator()
        process_id = uuid4()

        record = coordinator.create_process_state(process_id, "REQ-006")
        assert record.current_state == MotorState.INICIALIZADO

        updated = coordinator.transition_process_state(
            process_id,
            MotorState.ESPERANDO_INFORMACION,
            "coordinator transition",
        )
        assert updated.current_state == MotorState.ESPERANDO_INFORMACION
        assert coordinator.get_process_state(process_id) is updated

    def test_coordinate_creates_and_finalizes_process_state(self):
        coordinator = _ready_coordinator()
        result = coordinator.coordinate(metadata={"codigo_req": "REQ-007"})

        assert result.success is True
        assert "process_state" in result.metadata
        assert result.metadata["process_state"]["current_state"] == "finalizado"
        assert result.metadata["process_state"]["codigo_req"] == "REQ-007"

    def test_snapshot_includes_state_management(self):
        coordinator = _ready_coordinator()
        snapshot = coordinator.snapshot()
        assert "state_management" in snapshot
        assert len(snapshot["state_management"]["official_states"]) == 11

    def test_functional_modules_do_not_own_state_storage(self):
        import importlib

        modules = (
            "zovrake_motor.reception.service",
            "zovrake_motor.documents.service",
            "zovrake_motor.context.service",
            "zovrake_motor.events.service",
            "zovrake_motor.communication.service",
        )
        for module_name in modules:
            module = importlib.import_module(module_name)
            source_file = module.__file__
            assert source_file is not None
            with open(source_file, encoding="utf-8") as fh:
                content = fh.read()
            assert "StateManager" not in content
            assert "MotorState" not in content
