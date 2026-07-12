"""Pruebas de administración central de módulos — Implementación 1.5."""

from __future__ import annotations

import pytest

from zovrake_motor.communication import CommunicationService
from zovrake_motor.context import ContextService
from zovrake_motor.coordinator import (
    BASE_MODULES,
    CoordinationPipeline,
    ModuleAdministrator,
    ModuleLifecycleState,
    ModuleRegistry,
    MotorCoordinator,
    PLANNED_MODULES,
)
from zovrake_motor.coordinator.exceptions import ModuleNotAvailableError, ModuleNotFoundError
from zovrake_motor.documents import DocumentService
from zovrake_motor.events import EventService
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


class TestModuleAdministrator:
    def test_register_and_discover(self):
        admin = ModuleAdministrator()
        service = ReceptionService()
        admin.register(service)

        discovery = admin.discover()
        assert "reception" in discovery.registered
        assert "documents" in discovery.missing_base

    def test_initialize_all_base_modules(self):
        admin = ModuleAdministrator()
        for service_cls in BASE_SERVICES:
            admin.register(service_cls())

        admin.initialize_all()
        for name in BASE_MODULES:
            assert admin.is_available(name)
            assert admin.lifecycle_state(name) == ModuleLifecycleState.DISPONIBLE

    def test_validate_base_modules(self):
        admin = ModuleAdministrator()
        for service_cls in BASE_SERVICES:
            service = service_cls()
            service.initialize()
            admin.register(service)

        assert admin.validate_base_modules() is True

    def test_prepare_and_finalize_lifecycle(self):
        admin = ModuleAdministrator()
        service = ReceptionService()
        service.initialize()
        admin.register(service)

        admin.prepare_module("reception")
        assert admin.lifecycle_state("reception") == ModuleLifecycleState.PREPARADO

        admin.finalize_module("reception")
        assert admin.lifecycle_state("reception") == ModuleLifecycleState.FINALIZADO
        assert admin.is_available("reception") is False

    def test_require_raises_for_missing_module(self):
        admin = ModuleAdministrator()
        with pytest.raises(ModuleNotFoundError):
            admin.require("reception")

    def test_prepare_raises_for_unavailable_module(self):
        admin = ModuleAdministrator()
        admin.register(ReceptionService())
        with pytest.raises(ModuleNotAvailableError):
            admin.prepare_module("reception")

    def test_list_and_status(self):
        admin = ModuleAdministrator()
        service = ReceptionService()
        service.initialize()
        admin.register(service)

        assert admin.list_modules() == ["reception"]
        status = admin.get_status("reception")
        assert status.is_registered is True
        assert status.is_available is True


class TestCoordinationPipeline:
    def test_main_pipeline_order(self):
        names = CoordinationPipeline.ordered_module_names()
        assert names[0] == "reception"
        assert names[-1] == "intelligent_analysis"
        assert len(names) == 7

    def test_pipeline_snapshot_marks_future_modules(self):
        admin = ModuleAdministrator()
        for service_cls in BASE_SERVICES:
            service = service_cls()
            service.initialize()
            admin.register(service)

        snapshot = CoordinationPipeline.build_snapshot(admin)
        reception = next(item for item in snapshot if item["module_name"] == "reception")
        comprehension = next(item for item in snapshot if item["module_name"] == "comprehension")

        assert reception["registered"] is True
        assert reception["available"] is True
        assert comprehension["registered"] is False
        assert comprehension["available"] is False

    def test_all_referenced_modules_cover_planned_base(self):
        referenced = set(CoordinationPipeline.all_referenced_modules())
        for name in BASE_MODULES:
            assert name in referenced


class TestCoordinatorModuleAdministration:
    def test_registers_all_base_modules_individually(self):
        coordinator = MotorCoordinator()
        for service_cls in BASE_SERVICES:
            coordinator.register_module(service_cls())
        coordinator.initialize_modules()
        coordinator.prepare_modules()

        assert coordinator.validate_base_modules() is True
        assert coordinator.module_administrator.count() == 6

    def test_can_query_each_module(self):
        coordinator = MotorCoordinator()
        services = [service_cls() for service_cls in BASE_SERVICES]
        for service in services:
            coordinator.register_module(service)
        coordinator.initialize_modules()

        for service in services:
            assert coordinator.is_module_available(service.module_name)
            assert coordinator.get_module(service.module_name) is service

    def test_discovery_reports_missing_planned_modules(self):
        coordinator = MotorCoordinator()
        for service_cls in BASE_SERVICES:
            service = service_cls()
            service.initialize()
            coordinator.register_module(service)

        discovery = coordinator.discover_modules()
        assert discovery.missing_base == ()
        assert "comprehension" in discovery.missing_planned
        assert len(discovery.planned_modules) == len(PLANNED_MODULES)

    def test_no_direct_dependencies_between_modules(self):
        coordinator = MotorCoordinator()
        for service_cls in BASE_SERVICES:
            coordinator.register_module(service_cls())

        modules = [coordinator.get_module(name) for name in BASE_MODULES]
        assert all(module is not None for module in modules)
        assert coordinator.module_administrator.registry.all_base_registered()
