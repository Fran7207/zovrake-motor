"""Pruebas de la API Interna del Motor Inteligente — Implementación 8.2."""

from __future__ import annotations

from uuid import uuid4

from zovrake_motor import EnterpriseIntegrationService
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.enterprise_integration.internal_api import (
    AnalysisResultQueryRequest,
    AnalysisStatusQueryRequest,
    CancelAnalysisRequest,
    ContractVersionRegistry,
    InternalApiErrorResponse,
    StartAnalysisRequest,
    ValidateAnalysisRequest,
)
from zovrake_motor.enterprise_integration.internal_api.enums import InternalApiErrorCode
from zovrake_motor.enterprise_integration.internal_api.validation import StructuralValidator
from zovrake_motor.events import EventManager
from zovrake_motor.states import StateManager


class TestInternalIntegrationApiContracts:
    def test_contract_version_registry_supports_v1(self):
        assert ContractVersionRegistry.is_supported("v1") is True
        assert ContractVersionRegistry.is_supported("v2") is False
        assert ContractVersionRegistry.is_future("v2") is True
        assert ContractVersionRegistry.ACTIVE_VERSION == "v1"

    def test_start_analysis_request_serializes(self):
        process_id = uuid4()
        request = StartAnalysisRequest(
            process_id=process_id,
            codigo_req="REQ-100",
            document_ids=("doc-1", "doc-2"),
        )
        payload = request.to_dict()
        assert payload["operation"] == "start_analysis"
        assert payload["contract_version"] == "v1"
        assert payload["codigo_req"] == "REQ-100"
        assert payload["document_ids"] == ["doc-1", "doc-2"]

    def test_structural_validator_rejects_empty_codigo_req(self):
        validator = StructuralValidator()
        request = StartAnalysisRequest(process_id=uuid4(), codigo_req="")
        result = validator.validate_start_analysis(request)
        assert result.valid is False
        assert any("codigo_req" in error for error in result.errors)

    def test_structural_validator_rejects_unsupported_version(self):
        validator = StructuralValidator()
        request = StartAnalysisRequest(
            process_id=uuid4(),
            codigo_req="REQ-101",
            contract_version="v99",
        )
        result = validator.validate_start_analysis(request)
        assert result.valid is False


class TestInternalIntegrationApiServices:
    def test_internal_api_initializes(self):
        service = EnterpriseIntegrationService()
        service.initialize()

        snapshot = service.get_internal_api_snapshot()
        assert snapshot is not None
        assert snapshot["ready"] is True
        assert snapshot["active_contract_version"] == "v1"

    def test_start_analysis_through_coordinator_without_execution(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        process_id = uuid4()

        response = service.start_analysis(
            StartAnalysisRequest(process_id=process_id, codigo_req="REQ-200"),
        )

        assert response.success is True
        assert response.process_id == process_id
        assert response.executed is False
        assert "sin ejecución" in response.message.lower()

    def test_query_status_integrates_with_state_manager(self):
        state_manager = StateManager()
        event_manager = EventManager()
        config = ConfigurationProvider.default()
        service = EnterpriseIntegrationService(
            config_provider=config,
            state_manager=state_manager,
            event_manager=event_manager,
        )
        service.initialize()
        process_id = uuid4()
        state_manager.create_process(process_id, "REQ-201")

        response = service.query_analysis_status(
            AnalysisStatusQueryRequest(process_id=process_id, codigo_req="REQ-201"),
        )

        assert response.success is True
        assert response.executed is False
        assert response.motor_state is not None

    def test_query_result_returns_structured_placeholder(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        process_id = uuid4()

        response = service.query_analysis_result(
            AnalysisResultQueryRequest(process_id=process_id, codigo_req="REQ-202"),
        )

        assert response.success is True
        assert response.result is not None
        assert response.result.executed is False
        assert response.result.prepared is True

    def test_cancel_analysis_prepared(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        process_id = uuid4()

        response = service.cancel_analysis(
            CancelAnalysisRequest(process_id=process_id, reason="test"),
        )

        assert response.success is True
        assert response.executed is False

    def test_validate_request_structural(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        process_id = uuid4()

        response = service.validate_analysis_request(
            ValidateAnalysisRequest(
                process_id=process_id,
                codigo_req="REQ-203",
                payload={"codigo_req": "REQ-203"},
            ),
        )

        assert response.success is True
        assert response.valid is True

    def test_invalid_request_returns_controlled_error(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        process_id = uuid4()

        response = service.start_analysis(
            StartAnalysisRequest(process_id=process_id, codigo_req=""),
        )

        assert isinstance(response, InternalApiErrorResponse)
        assert response.error_code == InternalApiErrorCode.STRUCTURAL_VALIDATION_FAILED

    def test_events_registered_on_accepted_request(self):
        event_manager = EventManager()
        service = EnterpriseIntegrationService(event_manager=event_manager)
        service.initialize()
        process_id = uuid4()

        service.start_analysis(
            StartAnalysisRequest(process_id=process_id, codigo_req="REQ-204"),
        )

        assert event_manager.count_by_process(process_id) >= 1

    def test_contract_catalog_available(self):
        service = EnterpriseIntegrationService()
        service.initialize()

        catalog = service.get_contract_catalog()
        assert catalog is not None
        assert catalog["versioning"]["active_version"] == "v1"
        assert "v1" in catalog
        assert len(catalog["v1"]["request_contracts"]) == 5

    def test_uses_central_configuration(self):
        config = ConfigurationProvider.default()
        service = EnterpriseIntegrationService(config_provider=config)
        service.initialize()

        settings = config.enterprise_integration().internal_integration_api
        assert settings.prepared is True
        assert settings.structural_validation_enabled is True
        assert settings.active_contract_version == "v1"

    def test_direct_internal_api_requires_coordinator_path(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        coordinator = service.enterprise_integration_coordinator
        assert coordinator is not None
        assert coordinator.is_ready() is True

        gateway = coordinator.internal_api_gateway
        assert gateway is not None
        assert gateway.internal_api is not None

    def test_uninitialized_service_returns_coordinator_error(self):
        service = EnterpriseIntegrationService()
        process_id = uuid4()

        response = service.start_analysis(
            StartAnalysisRequest(process_id=process_id, codigo_req="REQ-205"),
        )

        assert isinstance(response, InternalApiErrorResponse)
        assert response.error_code == InternalApiErrorCode.COORDINATOR_REQUIRED

    def test_no_direct_imports_from_intelligent_analysis_in_internal_api(self):
        import importlib
        import pkgutil
        from pathlib import Path

        package = importlib.import_module("zovrake_motor.enterprise_integration.internal_api")
        for _finder, modname, _ispkg in pkgutil.walk_packages(
            package.__path__,
            prefix=package.__name__ + ".",
        ):
            module = importlib.import_module(modname)
            source = getattr(module, "__file__", "") or ""
            if not source.endswith(".py"):
                continue
            content = Path(source).read_text(encoding="utf-8")
            assert "zovrake_motor.intelligent_analysis" not in content
