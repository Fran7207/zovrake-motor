"""Pruebas del Módulo de Generación de Cuadros Comparativos — Implementación 4.1."""

from __future__ import annotations

from uuid import uuid4

from zovrake_motor import ComparativeTablesService, MotorCoordinator
from zovrake_motor.comparative_tables import ComparativeTablesRequest
from zovrake_motor.comparative_tables.enums import ComparativeTablesComponentType
from zovrake_motor.comparative_tables.input_models import ComparativeDomainModelReference
from zovrake_motor.config import ConfigurationProvider, ConfigCategory
from zovrake_motor.coordinator.pipeline import CoordinationPipeline
from zovrake_motor.events import EventManager
from zovrake_motor.states import StateManager


class TestComparativeTablesArchitecture:
    def test_module_initializes_with_ten_components(self):
        service = ComparativeTablesService()
        service.initialize()

        assert service.is_available()
        assert service.module_name == "comparative_tables"
        assert service.component_registry.count() == 10
        assert service.comparative_tables_coordinator is not None
        assert service.comparative_tables_coordinator.is_ready() is True

    def test_coordinator_cse_and_dcb_are_ready(self):
        service = ComparativeTablesService()
        service.initialize()

        assert service.component_registry.ready_count() == 10

    def test_prepare_returns_structural_result_without_processing(self):
        service = ComparativeTablesService()
        service.initialize()
        process_id = uuid4()

        result = service.prepare(
            ComparativeTablesRequest(process_id=process_id, codigo_req="REQ-001"),
        )

        assert result.prepared is True
        assert result.process_id == process_id
        assert result.components_ready == 10
        assert "sin procesamiento" in result.message.lower()

    def test_prepare_consumes_domain_model_without_original_documents(self):
        service = ComparativeTablesService()
        service.initialize()
        process_id = uuid4()

        result = service.prepare(
            ComparativeTablesRequest(
                process_id=process_id,
                codigo_req="REQ-002",
                domain_model=ComparativeDomainModelReference(
                    catalog_id="catalog-001",
                    model_id="cdm-000001",
                    document_id="doc-001",
                    process_id=str(process_id),
                ),
            ),
        )

        consumption = result.metadata["classification_consumption"]
        assert consumption["executed"] is False
        assert consumption["accesses_source_files"] is False
        assert consumption["accesses_intermediate_models"] is False
        assert consumption["domain_model_present"] is True
        assert consumption["pm6_output_contract_valid"] is True

    def test_uses_central_configuration(self):
        config = ConfigurationProvider.default()
        service = ComparativeTablesService(config_provider=config)
        service.initialize()

        settings = service.integration.comparative_tables_settings()
        assert settings.enabled is False
        assert settings.max_tables_per_process == 5_000
        assert settings.pm6_output_contract_required is True
        assert settings.classification_integration_prepared is True

    def test_prepared_for_state_and_event_managers(self):
        state_manager = StateManager()
        event_manager = EventManager()
        service = ComparativeTablesService(
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
        expected = {item.value for item in ComparativeTablesComponentType}
        service = ComparativeTablesService()
        service.initialize()
        registered = {
            component.component_name for component in service.component_registry.all_components()
        }
        assert expected == registered

    def test_pipeline_has_twelve_stages(self):
        service = ComparativeTablesService()
        service.initialize()

        pipeline = service.get_comparative_tables_pipeline_snapshot()
        assert len(pipeline) == 12
        assert pipeline[1]["phase"] == "consumo_modelo_dominio"
        assert pipeline[2]["component_name"] == "comparative_structure_engine"

    def test_no_direct_imports_from_other_base_modules(self):
        import importlib
        import pkgutil
        from pathlib import Path

        package = importlib.import_module("zovrake_motor.comparative_tables")
        forbidden = (
            "reception",
            "documents",
            "context",
            "communication",
            "comprehension",
            "classification",
        )
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


class TestComparativeTablesCoordinatorIntegration:
    def test_registers_in_coordinator_and_pipeline(self):
        config = ConfigurationProvider.default()
        state_manager = StateManager()
        event_manager = EventManager()
        coordinator = MotorCoordinator(
            config_provider=config,
            state_manager=state_manager,
            event_manager=event_manager,
        )

        service = ComparativeTablesService(
            config_provider=config,
            state_manager=state_manager,
            event_manager=event_manager,
        )
        coordinator.register_module(service)
        coordinator.initialize_modules()
        coordinator.prepare_modules()

        assert coordinator.is_module_available("comparative_tables")
        snapshot = coordinator.get_pipeline_snapshot()
        comparative_tables = next(
            item for item in snapshot if item["module_name"] == "comparative_tables"
        )
        assert comparative_tables["registered"] is True
        assert comparative_tables["available"] is True
        assert comparative_tables["order"] == 6

    def test_configuration_category_available(self):
        config = ConfigurationProvider.default()
        assert ConfigCategory.COMPARATIVE_TABLES.value == "comparative_tables"
        assert config.comparative_tables().enabled is False
        assert config.comparative_tables().pm6_output_contract_required is True

    def test_pipeline_includes_comparative_tables_stage(self):
        names = CoordinationPipeline.ordered_module_names()
        assert names.index("comparative_tables") == 5
        assert names.index("classification") == 4
