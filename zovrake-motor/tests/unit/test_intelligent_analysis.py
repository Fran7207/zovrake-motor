"""Pruebas del Módulo de Razonamiento y Resultado del Análisis Inteligente — Implementación 7.1."""

from __future__ import annotations

from uuid import uuid4

from zovrake_motor import IntelligentAnalysisService, MotorCoordinator
from zovrake_motor.config import ConfigurationProvider, ConfigCategory
from zovrake_motor.coordinator.pipeline import CoordinationPipeline
from zovrake_motor.events import EventManager
from zovrake_motor.intelligent_analysis import IntelligentAnalysisRequest
from zovrake_motor.intelligent_analysis.enums import IntelligentAnalysisComponentType
from zovrake_motor.intelligent_analysis.input_models import DefinitiveComparativeModelReference
from zovrake_motor.states import StateManager


class TestIntelligentAnalysisArchitecture:
    def test_module_initializes_with_eleven_components(self):
        service = IntelligentAnalysisService()
        service.initialize()

        assert service.is_available()
        assert service.module_name == "intelligent_analysis"
        assert service.component_registry.count() == 11
        assert service.intelligent_analysis_coordinator is not None
        assert service.intelligent_analysis_coordinator.is_ready() is True

    def test_all_prepared_components_are_ready(self):
        service = IntelligentAnalysisService()
        service.initialize()

        assert service.component_registry.ready_count() == 11

    def test_prepare_returns_structural_result_without_processing(self):
        service = IntelligentAnalysisService()
        service.initialize()
        process_id = uuid4()

        result = service.prepare(
            IntelligentAnalysisRequest(process_id=process_id, codigo_req="REQ-001"),
        )

        assert result.prepared is True
        assert result.process_id == process_id
        assert result.components_ready == 11
        assert "sin procesamiento" in result.message.lower()

    def test_prepare_consumes_definitive_model_without_original_documents(self):
        service = IntelligentAnalysisService()
        service.initialize()
        process_id = uuid4()

        result = service.prepare(
            IntelligentAnalysisRequest(
                process_id=process_id,
                codigo_req="REQ-002",
                definitive_model=DefinitiveComparativeModelReference(
                    catalog_id="catalog-001",
                    model_id="cmd-000001",
                    document_id="doc-001",
                    process_id=str(process_id),
                ),
            ),
        )

        consumption = result.metadata["comparative_tables_consumption"]
        assert consumption["executed"] is False
        assert consumption["accesses_source_files"] is False
        assert consumption["accesses_intermediate_models"] is False
        assert consumption["accesses_comparable_groups"] is False
        assert consumption["definitive_model_present"] is True
        assert consumption["pm7_input_contract_valid"] is True

    def test_uses_central_configuration(self):
        config = ConfigurationProvider.default()
        service = IntelligentAnalysisService(config_provider=config)
        service.initialize()

        settings = service.integration.intelligent_analysis_settings()
        assert settings.enabled is False
        assert settings.max_models_per_process == 5_000
        assert settings.pm7_input_contract_required is True
        assert settings.comparative_tables_integration_prepared is True

    def test_prepared_for_state_and_event_managers(self):
        state_manager = StateManager()
        event_manager = EventManager()
        service = IntelligentAnalysisService(
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
        expected = {item.value for item in IntelligentAnalysisComponentType}
        service = IntelligentAnalysisService()
        service.initialize()
        registered = {
            component.component_name for component in service.component_registry.all_components()
        }
        assert expected == registered

    def test_pipeline_has_thirteen_stages(self):
        service = IntelligentAnalysisService()
        service.initialize()

        pipeline = service.get_intelligent_analysis_pipeline_snapshot()
        assert len(pipeline) == 13
        assert pipeline[1]["phase"] == "consumo_modelo_comparativo_definitivo"
        assert pipeline[2]["component_name"] == "evidence_analysis_engine"
        assert pipeline[9]["component_name"] == "reasoning_result_builder"

    def test_no_direct_imports_from_other_base_modules(self):
        import importlib
        import pkgutil
        from pathlib import Path

        package = importlib.import_module("zovrake_motor.intelligent_analysis")
        forbidden = (
            "reception",
            "documents",
            "context",
            "communication",
            "comprehension",
            "classification",
            "comparative_tables",
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


class TestIntelligentAnalysisCoordinatorIntegration:
    def test_registers_in_coordinator_and_pipeline(self):
        config = ConfigurationProvider.default()
        state_manager = StateManager()
        event_manager = EventManager()
        coordinator = MotorCoordinator(
            config_provider=config,
            state_manager=state_manager,
            event_manager=event_manager,
        )

        service = IntelligentAnalysisService(
            config_provider=config,
            state_manager=state_manager,
            event_manager=event_manager,
        )
        coordinator.register_module(service)
        coordinator.initialize_modules()
        coordinator.prepare_modules()

        assert coordinator.is_module_available("intelligent_analysis")
        snapshot = coordinator.get_pipeline_snapshot()
        intelligent_analysis = next(
            item for item in snapshot if item["module_name"] == "intelligent_analysis"
        )
        assert intelligent_analysis["registered"] is True
        assert intelligent_analysis["available"] is True
        assert intelligent_analysis["order"] == 7

    def test_configuration_category_available(self):
        config = ConfigurationProvider.default()
        assert ConfigCategory.INTELLIGENT_ANALYSIS.value == "intelligent_analysis"
        assert config.intelligent_analysis().enabled is False
        assert config.intelligent_analysis().pm7_input_contract_required is True

    def test_pipeline_includes_intelligent_analysis_stage(self):
        names = CoordinationPipeline.ordered_module_names()
        assert names.index("intelligent_analysis") == 6
        assert names.index("comparative_tables") == 5
