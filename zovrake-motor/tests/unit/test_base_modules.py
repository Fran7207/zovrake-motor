"""Pruebas de los módulos base — Implementación 1.4."""

from __future__ import annotations

import importlib
import pkgutil
from uuid import uuid4

import pytest

from zovrake_motor.communication import CommunicationService
from zovrake_motor.context import ContextService
from zovrake_motor.coordinator import BASE_MODULES, ModuleRegistry, MotorCoordinator
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.events import EventManager, EventService
from zovrake_motor.states import StateManager, StateService
from zovrake_motor.documents import DocumentService
from zovrake_motor.events import EventService
from zovrake_motor.models.common import MotorRequest, MotorResponse
from zovrake_motor.models.ports import ModulePort
from zovrake_motor.reception import ReceptionService
from zovrake_motor.states import StateService

BASE_SERVICES = (
    ReceptionService,
    DocumentService,
    ContextService,
    StateService,
    EventService,
    CommunicationService,
)


class TestBaseModules:
    @pytest.mark.parametrize("service_cls", BASE_SERVICES)
    def test_module_initializes(self, service_cls):
        service = service_cls()
        assert service.is_available() is False
        service.initialize()
        assert service.is_available() is True

    @pytest.mark.parametrize("service_cls", BASE_SERVICES)
    def test_implements_module_port(self, service_cls):
        service = service_cls()
        assert isinstance(service, ModulePort)

    def test_all_base_modules_in_coordinator_constants(self):
        assert len(BASE_MODULES) == 6
        assert "reception" in BASE_MODULES
        assert "communication" in BASE_MODULES

    def test_modules_are_independent(self):
        """Ningún módulo base importa a otro módulo base."""
        base_packages = set(BASE_MODULES)
        for name in base_packages:
            package = importlib.import_module(f"zovrake_motor.{name}")
            for _finder, modname, _ispkg in pkgutil.walk_packages(
                package.__path__, prefix=package.__name__ + "."
            ):
                module = importlib.import_module(modname)
                source_file = getattr(module, "__file__", "") or ""
                if not source_file.endswith(".py"):
                    continue
                with open(source_file, encoding="utf-8") as fh:
                    content = fh.read()
                for other in base_packages:
                    if other == name:
                        continue
                    assert f"zovrake_motor.{other}" not in content, (
                        f"{modname} no debe depender de zovrake_motor.{other}"
                    )

    def test_registry_accepts_all_base_modules(self):
        registry = ModuleRegistry()
        for service_cls in BASE_SERVICES:
            service = service_cls()
            service.initialize()
            registry.register(service)
        assert registry.count() == 6
        for name in BASE_MODULES:
            assert registry.is_registered(name)

    def test_coordinator_can_register_modules_without_modification(self):
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
        assert coordinator.is_ready()
        result = coordinator.coordinate()
        assert result.success is True
        assert result.metadata["module_count"] == 6

    def test_reception_contract(self):
        service = ReceptionService()
        service.initialize()
        request = MotorRequest(codigo_req="REQ-001")
        result = service.receive(request)
        assert result.accepted is True
        assert result.codigo_req == "REQ-001"

    def test_context_contract(self):
        service = ContextService()
        service.initialize()
        request = MotorRequest(codigo_req="REQ-002", detalles_requerimiento="Cemento")
        ctx = service.prepare(request)
        assert ctx.detalles_requerimiento == "Cemento"

    def test_states_contract(self):
        service = StateService()
        service.initialize()
        pid = uuid4()
        record = service.create_process(pid, "REQ-003")
        assert record.current_state.value == "inicializado"

    def test_events_contract(self):
        service = EventService()
        service.initialize()
        from zovrake_motor.events import EventCategory, EventType
        process_id = uuid4()
        event = service.emit(
            category=EventCategory.SYSTEM,
            message="test",
            module="test",
            process_id=process_id,
            event_type=EventType.SYSTEM,
        )
        assert event is not None
        assert event.process_id == process_id
        assert service.count() == 1

    def test_communication_contract(self):
        service = CommunicationService()
        service.initialize()
        response = MotorResponse(process_id=uuid4(), codigo_req="REQ-004")
        service.send(response)
        assert service.outbound_count == 1
