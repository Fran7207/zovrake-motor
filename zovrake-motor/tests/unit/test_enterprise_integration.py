"""Pruebas del Módulo de Integración Empresarial — Implementación 8.1."""

from __future__ import annotations

from uuid import uuid4

from zovrake_motor import EnterpriseIntegrationService, MotorCoordinator
from zovrake_motor.config import ConfigurationProvider, ConfigCategory
from zovrake_motor.coordinator.pipeline import CoordinationPipeline
from zovrake_motor.enterprise_integration import EnterpriseIntegrationRequest
from zovrake_motor.enterprise_integration.enums import EnterpriseIntegrationComponentType
from zovrake_motor.enterprise_integration.governance import (
    IMPLEMENTATION,
    PROMPT_MAESTRO_8_STATUS,
    governance_snapshot,
)
from zovrake_motor.enterprise_integration.input_models import IntelligentAnalysisResultReference
from zovrake_motor.events import EventManager
from zovrake_motor.states import StateManager


class TestEnterpriseIntegrationArchitecture:
    def test_module_initializes_with_ten_components(self):
        service = EnterpriseIntegrationService()
        service.initialize()

        assert service.is_available()
        assert service.module_name == "enterprise_integration"
        assert service.component_registry.count() == 17
        assert service.enterprise_integration_coordinator is not None
        assert service.enterprise_integration_coordinator.is_ready() is True

    def test_all_prepared_components_are_ready(self):
        service = EnterpriseIntegrationService()
        service.initialize()

        assert service.component_registry.ready_count() == 17

    def test_prepare_returns_structural_result_without_processing(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        process_id = uuid4()

        result = service.prepare(
            EnterpriseIntegrationRequest(process_id=process_id, codigo_req="REQ-001"),
        )

        assert result.prepared is True
        assert result.process_id == process_id
        assert result.components_ready == 17
        assert "sin procesamiento" in result.message.lower()

    def test_prepare_consumes_analysis_result_without_intelligent_analysis_internals(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        process_id = uuid4()

        result = service.prepare(
            EnterpriseIntegrationRequest(
                process_id=process_id,
                codigo_req="REQ-002",
                analysis_result=IntelligentAnalysisResultReference(
                    catalog_id="catalog-001",
                    model_id="iar-000001",
                    document_id="doc-001",
                    process_id=str(process_id),
                ),
            ),
        )

        consumption = result.metadata["intelligent_analysis_consumption"]
        assert consumption["executed"] is False
        assert consumption["accesses_intelligent_analysis_internals"] is False
        assert consumption["accesses_erp_frontend"] is False
        assert consumption["accesses_intermediate_catalogs"] is False
        assert consumption["analysis_result_present"] is True
        assert consumption["pm8_input_contract_valid"] is True

    def test_uses_central_configuration(self):
        config = ConfigurationProvider.default()
        service = EnterpriseIntegrationService(config_provider=config)
        service.initialize()

        settings = service.integration.enterprise_integration_settings()
        assert settings.enabled is False
        assert settings.max_requests_per_process == 5_000
        assert settings.pm8_input_contract_required is True
        assert settings.intelligent_analysis_integration_prepared is True

    def test_prepared_for_state_and_event_managers(self):
        state_manager = StateManager()
        event_manager = EventManager()
        service = EnterpriseIntegrationService(
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
        expected = {item.value for item in EnterpriseIntegrationComponentType}
        service = EnterpriseIntegrationService()
        service.initialize()
        registered = {
            component.component_name for component in service.component_registry.all_components()
        }
        assert expected == registered

    def test_component_types_include_pio(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        names = {
            component.component_name for component in service.component_registry.all_components()
        }
        assert "pipeline_integration_orchestrator" in names

    def test_pipeline_has_twelve_stages(self):
        service = EnterpriseIntegrationService()
        service.initialize()

        pipeline = service.get_enterprise_integration_pipeline_snapshot()
        assert len(pipeline) == 12
        assert pipeline[1]["phase"] == "consumo_resultado_analisis_inteligente"
        assert pipeline[2]["component_name"] == "api_gateway_internal"
        assert pipeline[11]["component_name"] == "enterprise_integration_coordinator"

    def test_no_direct_imports_from_other_base_modules(self):
        import importlib
        import pkgutil
        from pathlib import Path

        package = importlib.import_module("zovrake_motor.enterprise_integration")
        forbidden = (
            "reception",
            "documents",
            "context",
            "communication",
            "comprehension",
            "classification",
            "comparative_tables",
            "intelligent_analysis",
        )
        for _finder, modname, _ispkg in pkgutil.walk_packages(
            package.__path__,
            prefix=package.__name__ + ".",
        ):
            module = importlib.import_module(modname)
            source = getattr(module, "__file__", "") or ""
            if not source.endswith(".py"):
                continue
            if source.endswith("governance.py"):
                continue
            content = Path(source).read_text(encoding="utf-8")
            for other in forbidden:
                assert f"zovrake_motor.{other}" not in content

    def test_governance_snapshot_declares_pm8_open(self):
        snapshot = governance_snapshot()
        assert PROMPT_MAESTRO_8_STATUS == "CLOSED"
        assert IMPLEMENTATION == "8.12"
        assert snapshot["prepared_functional_components_count"] == 17


class TestEnterpriseIntegrationCoordinatorIntegration:
    def test_registers_in_coordinator_and_pipeline(self):
        config = ConfigurationProvider.default()
        state_manager = StateManager()
        event_manager = EventManager()
        coordinator = MotorCoordinator(
            config_provider=config,
            state_manager=state_manager,
            event_manager=event_manager,
        )

        service = EnterpriseIntegrationService(
            config_provider=config,
            state_manager=state_manager,
            event_manager=event_manager,
        )
        coordinator.register_module(service)
        coordinator.initialize_modules()
        coordinator.prepare_modules()

        assert coordinator.is_module_available("enterprise_integration")
        snapshot = coordinator.get_pipeline_snapshot()
        enterprise_integration = next(
            item for item in snapshot if item["module_name"] == "enterprise_integration"
        )
        assert enterprise_integration["registered"] is True
        assert enterprise_integration["available"] is True
        assert enterprise_integration["role"] == "integration"
        assert enterprise_integration["order"] is None

    def test_configuration_category_available(self):
        config = ConfigurationProvider.default()
        assert ConfigCategory.ENTERPRISE_INTEGRATION.value == "enterprise_integration"
        assert config.enterprise_integration().enabled is False
        assert config.enterprise_integration().pm8_input_contract_required is True

    def test_pipeline_includes_enterprise_integration_module(self):
        assert "enterprise_integration" in CoordinationPipeline.INTEGRATION_MODULES
        assert "enterprise_integration" not in CoordinationPipeline.ordered_module_names()
