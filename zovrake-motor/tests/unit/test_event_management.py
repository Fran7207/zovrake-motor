"""Pruebas del Sistema de Gestión de Eventos — Implementación 1.9."""

from __future__ import annotations

from uuid import uuid4

import pytest

from zovrake_motor.communication import CommunicationService
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.context import ContextService
from zovrake_motor.coordinator import MotorCoordinator
from zovrake_motor.documents import DocumentService
from zovrake_motor.events import (
    EventCategory,
    EventFactory,
    EventLifecycleState,
    EventManagementError,
    EventManager,
    EventService,
    EventType,
    MotorEvent,
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
    event_manager = EventManager(
        max_events_per_process=config.events().max_events_in_memory,
    )
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


class TestMotorEventModel:
    def test_uniform_event_structure(self):
        process_id = uuid4()
        event = MotorEvent.create(
            process_id=process_id,
            module="reception",
            event_type=EventType.MODULE,
            message="Evento de prueba",
            associated_state="inicializado",
            metadata={"key": "value"},
            category=EventCategory.RECEPTION,
        )

        data = event.to_dict()
        assert data["event_id"]
        assert data["process_id"] == str(process_id)
        assert data["module"] == "reception"
        assert data["event_type"] == "module"
        assert data["associated_state"] == "inicializado"
        assert data["metadata"] == {"key": "value"}
        assert data["lifecycle_state"] == "created"


class TestEventManager:
    def test_initializes_correctly(self):
        manager = EventManager()
        assert manager.count() == 0

    def test_register_and_query_by_process(self):
        manager = EventManager()
        process_a = uuid4()
        process_b = uuid4()

        manager.create_and_register(
            process_id=process_a,
            module="coordinator",
            event_type=EventType.COORDINATION,
            message="Proceso A",
        )
        manager.create_and_register(
            process_id=process_b,
            module="coordinator",
            event_type=EventType.COORDINATION,
            message="Proceso B",
        )

        history_a = manager.get_process_history(process_a)
        history_b = manager.get_process_history(process_b)

        assert len(history_a) == 1
        assert len(history_b) == 1
        assert history_a[0].message == "Proceso A"
        assert history_b[0].message == "Proceso B"

    def test_create_register_finalize_lifecycle(self):
        manager = EventManager()
        process_id = uuid4()
        event = manager.create_and_register(
            process_id=process_id,
            module="test",
            event_type=EventType.SYSTEM,
            message="registrado",
        )
        assert event.lifecycle_state == EventLifecycleState.REGISTERED

        finalized = manager.finalize_event(event.event_id)
        assert finalized.lifecycle_state == EventLifecycleState.FINALIZED

    def test_cannot_register_finalized_event(self):
        manager = EventManager()
        process_id = uuid4()
        event = manager.create_and_register(
            process_id=process_id,
            module="test",
            event_type=EventType.SYSTEM,
            message="test",
        )
        manager.finalize_event(event.event_id)

        with pytest.raises(EventManagementError):
            manager.register_event(event)

    def test_event_factory_generates_without_registering(self):
        manager = EventManager()
        process_id = uuid4()
        event = EventFactory.create(
            process_id=process_id,
            module="reception",
            event_type=EventType.MODULE,
            message="generado",
        )
        assert manager.count() == 0
        manager.register_event(event)
        assert manager.count() == 1


class TestEventServiceIntegration:
    def test_service_delegates_to_shared_manager(self):
        manager = EventManager()
        service = EventService(event_manager=manager)
        process_id = uuid4()
        service.emit(
            category=EventCategory.SYSTEM,
            message="test",
            module="test",
            process_id=process_id,
        )
        assert manager.count() == 1


class TestCoordinatorEventControl:
    def test_coordinator_registers_process_events(self):
        coordinator = _ready_coordinator()
        process_id = uuid4()

        event = coordinator.register_coordination_event(
            process_id=process_id,
            message="evento de coordinación",
        )
        assert event.module == "MotorCoordinator"
        assert coordinator.get_process_events(process_id)[0].event_id == event.event_id

    def test_coordinate_includes_process_events(self):
        coordinator = _ready_coordinator()
        result = coordinator.coordinate(metadata={"codigo_req": "REQ-EMS"})

        assert result.success is True
        assert "process_events" in result.metadata
        assert len(result.metadata["process_events"]) >= 2
        assert "event_management" in result.metadata

    def test_snapshot_includes_event_management(self):
        coordinator = _ready_coordinator()
        snapshot = coordinator.snapshot()
        assert "event_management" in snapshot
        assert "ems_total_events" in snapshot

    def test_functional_modules_do_not_own_event_storage(self):
        import importlib

        modules = (
            "zovrake_motor.reception.service",
            "zovrake_motor.documents.service",
            "zovrake_motor.context.service",
            "zovrake_motor.communication.service",
            "zovrake_motor.states.service",
        )
        for module_name in modules:
            module = importlib.import_module(module_name)
            source_file = module.__file__
            assert source_file is not None
            with open(source_file, encoding="utf-8") as fh:
                content = fh.read()
            assert "EventStore" not in content
            assert "EventManager" not in content
