"""Pruebas de integración End-to-End — Módulo de Integración Empresarial (8.10)."""

from __future__ import annotations

from uuid import uuid4

from zovrake_motor.certification.enterprise_integration_e2e_pipeline import (
    build_evidence_center_request,
    run_full_enterprise_integration_e2e_pipeline,
)
from zovrake_motor.enterprise_integration import EnterpriseIntegrationService
from zovrake_motor.events import EventManager
from zovrake_motor.states import StateManager


class TestEnterpriseIntegrationE2EPipeline:
    def test_full_pipeline_passes(self):
        result = run_full_enterprise_integration_e2e_pipeline()
        assert result.passed
        assert result.submit_success is True
        assert result.submit_async is True
        assert result.queue_processed >= 1
        assert result.pipeline_transitions >= 1
        assert result.status_query_success is True
        assert result.result_query_success is True
        assert result.event_count >= 1

    def test_pipeline_preserves_process_context(self):
        service = EnterpriseIntegrationService()
        result = run_full_enterprise_integration_e2e_pipeline(service=service)
        context = service.get_pipeline_context(result.process_id)
        assert context is not None
        assert context.process_id == result.process_id
        assert len(context.transitions) >= 1

    def test_evidence_center_request_builder(self):
        process_id = uuid4()
        request = build_evidence_center_request(process_id, codigo_req="REQ-TEST")
        assert request.process_id == process_id
        assert request.requirement.codigo_req == "REQ-TEST"
        assert len(request.evidence_documents) >= 1

    def test_async_processing_does_not_block_erp(self):
        state_manager = StateManager()
        event_manager = EventManager()
        service = EnterpriseIntegrationService(
            state_manager=state_manager,
            event_manager=event_manager,
        )
        result = run_full_enterprise_integration_e2e_pipeline(
            service=service,
            state_manager=state_manager,
            event_manager=event_manager,
        )
        assert result.submit_async is True
        assert state_manager.get_process(result.process_id) is not None

    def test_traceability_and_audit_recorded(self):
        service = EnterpriseIntegrationService()
        result = run_full_enterprise_integration_e2e_pipeline(service=service)
        ommf = service.observability_metrics_monitoring_framework
        svaf = service.security_validation_audit_framework
        assert ommf is not None
        assert svaf is not None
        assert len(ommf.framework.traces_for_process(result.process_id)) >= 1
        assert len(svaf.framework.audit_store.by_process(result.process_id)) >= 1
