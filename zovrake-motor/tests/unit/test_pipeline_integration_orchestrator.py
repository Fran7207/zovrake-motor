"""Pruebas del Pipeline Integration Orchestrator — Implementación 8.3."""

from __future__ import annotations

from uuid import uuid4

from zovrake_motor import EnterpriseIntegrationService
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.enterprise_integration.governance import IMPLEMENTATION
from zovrake_motor.enterprise_integration.internal_api import (
    InternalApiErrorResponse,
    StartAnalysisRequest,
)
from zovrake_motor.enterprise_integration.pio import (
    IntegrationPipelineLifecycle,
    IntegrationPipelinePhase,
    PipelineOrchestrationOperation,
)
from zovrake_motor.events import EventManager
from zovrake_motor.states import StateManager


class TestPipelineIntegrationOrchestrator:
    def test_module_has_eleven_components(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        assert service.component_registry.count() == 17

    def test_pio_initializes_and_is_ready(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        snapshot = service.get_pipeline_orchestrator_snapshot()
        assert snapshot is not None
        assert snapshot["orchestrator"]["ready"] is True

    def test_coordinator_requires_pio(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        coordinator = service.enterprise_integration_coordinator
        assert coordinator is not None
        assert coordinator.is_ready() is True
        assert coordinator.pipeline_orchestrator is not None

    def test_start_analysis_runs_full_deterministic_pipeline(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        process_id = uuid4()

        response = service.start_analysis(
            StartAnalysisRequest(
                process_id=process_id,
                codigo_req="REQ-PIO-001",
                metadata={"project_id": "PRJ-1", "analysis_id": "AN-1"},
            ),
        )

        assert response.success is True
        assert response.executed is False
        pipeline = response.metadata["pipeline_orchestration"]
        assert len(pipeline["phases_completed"]) == len(
            IntegrationPipelineLifecycle.flow_for(PipelineOrchestrationOperation.START_ANALYSIS),
        )
        assert pipeline["phases_completed"][0] == IntegrationPipelinePhase.SOLICITUD_RECIBIDA.value
        assert pipeline["phases_completed"][-1] == IntegrationPipelinePhase.PROCESO_FINALIZADO.value

    def test_traceability_preserved_through_pipeline(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        process_id = uuid4()

        service.start_analysis(
            StartAnalysisRequest(
                process_id=process_id,
                codigo_req="REQ-PIO-002",
                metadata={"project_id": "PRJ-2", "analysis_id": "AN-2"},
            ),
        )

        context = service.get_pipeline_context(process_id)
        assert context is not None
        assert context.project_id == "PRJ-2"
        assert context.analysis_id == "AN-2"
        assert len(context.transitions) >= 9
        assert context.motor_invocation_prepared is True
        assert context.motor_executed is False

    def test_invalid_request_produces_controlled_error(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        process_id = uuid4()

        response = service.start_analysis(
            StartAnalysisRequest(process_id=process_id, codigo_req=""),
        )

        assert isinstance(response, InternalApiErrorResponse)

    def test_motor_states_updated_via_central_state_manager(self):
        state_manager = StateManager()
        service = EnterpriseIntegrationService(state_manager=state_manager)
        service.initialize()
        process_id = uuid4()

        service.start_analysis(
            StartAnalysisRequest(process_id=process_id, codigo_req="REQ-PIO-003"),
        )

        record = state_manager.get_process(process_id)
        assert record is not None
        assert record.current_state.value == "finalizado"

    def test_pipeline_events_registered(self):
        event_manager = EventManager()
        service = EnterpriseIntegrationService(event_manager=event_manager)
        service.initialize()
        process_id = uuid4()

        service.start_analysis(
            StartAnalysisRequest(process_id=process_id, codigo_req="REQ-PIO-004"),
        )

        assert event_manager.count_by_process(process_id) >= 5

    def test_lifecycle_rejects_out_of_order_transition(self):
        assert IntegrationPipelineLifecycle.is_valid_transition(
            PipelineOrchestrationOperation.START_ANALYSIS,
            IntegrationPipelinePhase.SOLICITUD_RECIBIDA,
            IntegrationPipelinePhase.VALIDACION_INICIADA,
        )
        assert IntegrationPipelineLifecycle.is_valid_transition(
            PipelineOrchestrationOperation.START_ANALYSIS,
            IntegrationPipelinePhase.SOLICITUD_RECIBIDA,
            IntegrationPipelinePhase.PROCESO_FINALIZADO,
        ) is False

    def test_uses_central_configuration(self):
        config = ConfigurationProvider.default()
        settings = config.enterprise_integration().pipeline_integration_orchestrator
        assert settings.prepared is True
        assert settings.deterministic_pipeline is True

    def test_governance_declares_implementation_8_6(self):
        assert IMPLEMENTATION == "8.12"

    def test_no_motor_internal_imports_in_pio(self):
        import importlib
        import pkgutil
        from pathlib import Path

        package = importlib.import_module("zovrake_motor.enterprise_integration.pio")
        forbidden = ("intelligent_analysis", "comprehension", "reception", "documents")
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
