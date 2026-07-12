"""Pruebas del Coordinator Central — Implementación 1.3 y 1.5."""

from __future__ import annotations

from uuid import uuid4

import pytest

from zovrake_motor.coordinator import (
    BASE_MODULES,
    CoordinationPhase,
    CoordinatorState,
    ModulePort,
    ModuleRegistry,
    MotorCoordinator,
)


class _StubModule(ModulePort):
    def __init__(self, name: str) -> None:
        self._name = name
        self._initialized = False

    @property
    def module_name(self) -> str:
        return self._name

    def is_available(self) -> bool:
        return self._initialized

    def initialize(self) -> None:
        self._initialized = True


def _register_all_base_stubs(coordinator: MotorCoordinator) -> None:
    for name in BASE_MODULES:
        stub = _StubModule(name)
        coordinator.register_module(stub)
    coordinator.initialize_modules()
    coordinator.prepare_modules()


class TestMotorCoordinator:
    def test_initializes_waiting_for_modules_without_registry(self):
        coordinator = MotorCoordinator()
        assert coordinator.is_ready() is False
        assert coordinator.state == CoordinatorState.ESPERANDO_MODULOS

    def test_becomes_ready_with_all_base_modules(self):
        coordinator = MotorCoordinator()
        _register_all_base_stubs(coordinator)
        assert coordinator.is_ready() is True
        assert coordinator.state == CoordinatorState.PREPARADO

    def test_snapshot(self):
        coordinator = MotorCoordinator()
        _register_all_base_stubs(coordinator)
        snap = coordinator.snapshot()
        assert snap["is_ready"] is True
        assert snap["coordinator_state"] == "preparado"
        assert snap["base_modules_valid"] is True
        assert len(snap["registered_modules"]) == 6

    def test_coordinate_completes_lifecycle(self):
        coordinator = MotorCoordinator()
        _register_all_base_stubs(coordinator)
        result = coordinator.coordinate()

        assert result.success is True
        assert result.state == CoordinatorState.FINALIZADO
        assert len(result.phases_completed) == 5
        assert result.phases_completed[0] == CoordinationPhase.SOLICITUD
        assert result.phases_completed[-1] == CoordinationPhase.FINALIZACION

    def test_coordinate_includes_pipeline_structure(self):
        coordinator = MotorCoordinator()
        _register_all_base_stubs(coordinator)
        result = coordinator.coordinate()

        assert "pipeline" in result.metadata
        assert len(result.metadata["pipeline"]) >= 7
        assert result.metadata["pipeline"][0]["module_name"] == "reception"

    def test_coordinate_fails_without_base_modules(self):
        coordinator = MotorCoordinator()
        result = coordinator.coordinate()
        assert result.success is False

    def test_coordinate_creates_process(self):
        coordinator = MotorCoordinator()
        _register_all_base_stubs(coordinator)
        process_id = uuid4()
        result = coordinator.coordinate(process_id=process_id)

        process = coordinator.get_process(process_id)
        assert process is not None
        assert len(process.phases) == 5
        assert result.process_id == process_id

    def test_events_recorded(self):
        coordinator = MotorCoordinator()
        _register_all_base_stubs(coordinator)
        coordinator.coordinate()
        assert coordinator.event_collector.count() > 0

    def test_module_registry_accepts_ports(self):
        registry = ModuleRegistry()
        stub = _StubModule("reception")
        stub.initialize()
        registry.register(stub)
        assert registry.is_registered("reception")
        assert registry.count() == 1

    def test_dependency_injection_via_registry(self):
        registry = ModuleRegistry()
        for name in BASE_MODULES:
            stub = _StubModule(name)
            stub.initialize()
            registry.register(stub)
        coordinator = MotorCoordinator(module_registry=registry)
        coordinator.prepare_modules()

        assert coordinator.module_registry.count() == 6
        assert coordinator.is_ready() is True
        result = coordinator.coordinate()
        assert result.metadata["module_count"] == 6

    def test_register_module_api(self):
        coordinator = MotorCoordinator()
        stub = _StubModule("reception")
        coordinator.register_module(stub)
        coordinator.initialize_modules()

        assert coordinator.is_module_available("reception") is True
        assert coordinator.get_module("reception") is stub

    def test_shutdown(self):
        coordinator = MotorCoordinator()
        _register_all_base_stubs(coordinator)
        coordinator.coordinate()
        coordinator.shutdown()
        assert coordinator.active_process_count == 0

    def test_no_circular_imports(self):
        import zovrake_motor.coordinator.coordinator
        import zovrake_motor.coordinator.registry
        import zovrake_motor.coordinator.lifecycle
        import zovrake_motor.coordinator.module_administrator
        import zovrake_motor.coordinator.pipeline
