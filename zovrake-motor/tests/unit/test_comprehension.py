"""Pruebas del Módulo de Comprensión Documental — Implementación 2.1."""

from __future__ import annotations

from uuid import uuid4

from zovrake_motor import ComprehensionService, MotorCoordinator
from zovrake_motor.comprehension import ComprehensionRequest
from zovrake_motor.comprehension.enums import ComprehensionComponentType
from zovrake_motor.config import ConfigurationProvider, ConfigCategory
from zovrake_motor.coordinator.pipeline import CoordinationPipeline
from zovrake_motor.events import EventManager
from zovrake_motor.states import StateManager


class TestComprehensionArchitecture:
    def test_module_initializes_with_eleven_components(self):
        service = ComprehensionService()
        service.initialize()

        assert service.is_available()
        assert service.module_name == "comprehension"
        assert service.component_registry.count() == 11
        assert service.document_coordinator is not None
        assert service.document_coordinator.is_ready() is True

    def test_prepare_returns_structural_result_without_processing(self):
        service = ComprehensionService()
        service.initialize()
        process_id = uuid4()

        result = service.prepare(
            ComprehensionRequest(process_id=process_id, codigo_req="REQ-001"),
        )

        assert result.prepared is True
        assert result.process_id == process_id
        assert result.components_ready == 9
        assert "sin procesamiento" in result.message.lower()

    def test_uses_central_configuration(self):
        config = ConfigurationProvider.default()
        service = ComprehensionService(config_provider=config)
        service.initialize()

        settings = service.integration.comprehension_settings()
        assert settings.enabled is False
        assert settings.max_documents_per_process == 100
        assert "pdf" in settings.supported_formats

    def test_prepared_for_state_and_event_managers(self):
        state_manager = StateManager()
        event_manager = EventManager()
        service = ComprehensionService(
            state_manager=state_manager,
            event_manager=event_manager,
        )
        service.initialize()

        assert service.state_manager is state_manager
        assert service.event_manager is event_manager
        snapshot = service.integration.snapshot()
        assert snapshot["state_management_ready"] is True
        assert snapshot["event_management_ready"] is True

    def test_component_types_cover_architecture(self):
        expected = {item.value for item in ComprehensionComponentType}
        service = ComprehensionService()
        service.initialize()
        registered = {
            component.component_name for component in service.component_registry.all_components()
        }
        assert expected == registered

    def test_no_direct_imports_from_other_base_modules(self):
        import importlib
        import pkgutil
        from pathlib import Path

        package = importlib.import_module("zovrake_motor.comprehension")
        forbidden = ("reception", "documents", "context", "communication")
        for _finder, modname, _ispkg in pkgutil.walk_packages(
            package.__path__,
            prefix=package.__name__ + ".",
        ):
            module = importlib.import_module(modname)
            source = getattr(module, "__file__", "") or ""
            if not source.endswith(".py"):
                continue
            content = Path(source).read_text(encoding="utf-8")
            for other in forbidden:
                assert f"zovrake_motor.{other}" not in content


class TestComprehensionCoordinatorIntegration:
    def test_registers_in_coordinator_and_pipeline(self):
        config = ConfigurationProvider.default()
        state_manager = StateManager()
        event_manager = EventManager()
        coordinator = MotorCoordinator(
            config_provider=config,
            state_manager=state_manager,
            event_manager=event_manager,
        )

        service = ComprehensionService(
            config_provider=config,
            state_manager=state_manager,
            event_manager=event_manager,
        )
        coordinator.register_module(service)
        coordinator.initialize_modules()
        coordinator.prepare_modules()

        assert coordinator.is_module_available("comprehension")
        snapshot = coordinator.get_pipeline_snapshot()
        comprehension = next(item for item in snapshot if item["module_name"] == "comprehension")
        assert comprehension["registered"] is True
        assert comprehension["available"] is True
        assert comprehension["order"] == 4

    def test_configuration_category_available(self):
        config = ConfigurationProvider.default()
        assert ConfigCategory.COMPREHENSION.value == "comprehension"
        assert config.comprehension().enabled is False

    def test_pipeline_includes_comprehension_stage(self):
        names = CoordinationPipeline.ordered_module_names()
        assert names.index("comprehension") == 3
