"""Pruebas del Módulo de Clasificación Inteligente — Implementación 3.1."""

from __future__ import annotations

from uuid import uuid4

from zovrake_motor import ClassificationService, MotorCoordinator
from zovrake_motor.classification import ClassificationRequest
from zovrake_motor.classification.enums import ClassificationComponentType
from zovrake_motor.classification.input_models import (
    DocumentIndexReference,
    IntegratedContextReference,
    InternalDocumentModelReference,
)
from zovrake_motor.config import ConfigurationProvider, ConfigCategory
from zovrake_motor.coordinator.pipeline import CoordinationPipeline
from zovrake_motor.events import EventManager
from zovrake_motor.states import StateManager


class TestClassificationArchitecture:
    def test_module_initializes_with_thirteen_components(self):
        service = ClassificationService()
        service.initialize()

        assert service.is_available()
        assert service.module_name == "classification"
        assert service.component_registry.count() == 13
        assert service.classification_coordinator is not None
        assert service.classification_coordinator.is_ready() is True

    def test_prepare_returns_structural_result_without_processing(self):
        service = ClassificationService()
        service.initialize()
        process_id = uuid4()

        result = service.prepare(
            ClassificationRequest(process_id=process_id, codigo_req="REQ-001"),
        )

        assert result.prepared is True
        assert result.process_id == process_id
        assert result.components_ready == 10
        assert "sin procesamiento" in result.message.lower()

    def test_prepare_consumes_comprehension_outputs_without_original_documents(self):
        service = ClassificationService()
        service.initialize()
        process_id = uuid4()

        result = service.prepare(
            ClassificationRequest(
                process_id=process_id,
                codigo_req="REQ-002",
                internal_model=InternalDocumentModelReference(
                    model_id="model-001",
                    document_id="doc-001",
                    schema_version="1.0",
                ),
                index_reference=DocumentIndexReference(
                    index_entry_id="dki-001",
                    model_id="model-001",
                    process_id=str(process_id),
                ),
                context_reference=IntegratedContextReference(
                    association_id="ctx-001",
                    process_id=str(process_id),
                    codigo_req="REQ-002",
                ),
            ),
        )

        consumption = result.metadata["comprehension_consumption"]
        assert consumption["executed"] is False
        assert consumption["accesses_original_documents"] is False
        assert consumption["internal_model_present"] is True
        assert consumption["index_reference_present"] is True
        assert consumption["context_reference_present"] is True

    def test_uses_central_configuration(self):
        config = ConfigurationProvider.default()
        service = ClassificationService(config_provider=config)
        service.initialize()

        settings = service.integration.classification_settings()
        assert settings.enabled is False
        assert settings.max_concepts_per_process == 10_000
        assert settings.comprehension_integration_prepared is True

    def test_prepared_for_state_and_event_managers(self):
        state_manager = StateManager()
        event_manager = EventManager()
        service = ClassificationService(
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
        expected = {item.value for item in ClassificationComponentType}
        service = ClassificationService()
        service.initialize()
        registered = {
            component.component_name for component in service.component_registry.all_components()
        }
        assert expected == registered

    def test_no_direct_imports_from_other_base_modules(self):
        import importlib
        import pkgutil
        from pathlib import Path

        package = importlib.import_module("zovrake_motor.classification")
        forbidden = ("reception", "documents", "context", "communication", "comprehension")
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


class TestClassificationCoordinatorIntegration:
    def test_registers_in_coordinator_and_pipeline(self):
        config = ConfigurationProvider.default()
        state_manager = StateManager()
        event_manager = EventManager()
        coordinator = MotorCoordinator(
            config_provider=config,
            state_manager=state_manager,
            event_manager=event_manager,
        )

        service = ClassificationService(
            config_provider=config,
            state_manager=state_manager,
            event_manager=event_manager,
        )
        coordinator.register_module(service)
        coordinator.initialize_modules()
        coordinator.prepare_modules()

        assert coordinator.is_module_available("classification")
        snapshot = coordinator.get_pipeline_snapshot()
        classification = next(item for item in snapshot if item["module_name"] == "classification")
        assert classification["registered"] is True
        assert classification["available"] is True
        assert classification["order"] == 5

    def test_configuration_category_available(self):
        config = ConfigurationProvider.default()
        assert ConfigCategory.CLASSIFICATION.value == "classification"
        assert config.classification().enabled is False

    def test_pipeline_includes_classification_stage(self):
        names = CoordinationPipeline.ordered_module_names()
        assert names.index("classification") == 4
