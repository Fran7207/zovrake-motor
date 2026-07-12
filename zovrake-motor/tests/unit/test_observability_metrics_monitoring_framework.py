"""Pruebas del Observability, Metrics & Monitoring Framework — Implementación 8.8."""

from __future__ import annotations

from uuid import uuid4

from zovrake_motor import EnterpriseIntegrationService
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.enterprise_integration.ecg.contracts.erp_requests import (
    EvidenceCenterAnalysisRequest,
    EvidenceDocumentReference,
    RequirementDetailsReference,
)
from zovrake_motor.enterprise_integration.governance import IMPLEMENTATION
from zovrake_motor.enterprise_integration.ommf.enums import ComponentHealthStatus
from zovrake_motor.events import EventManager
from zovrake_motor.states import StateManager


def _analysis_request(process_id, codigo_req="REQ-OMMF-001") -> EvidenceCenterAnalysisRequest:
    return EvidenceCenterAnalysisRequest(
        process_id=process_id,
        project_id="PRJ-OMMF",
        quotation_id="COT-OMMF",
        requirement=RequirementDetailsReference(codigo_req=codigo_req),
        evidence_documents=(EvidenceDocumentReference(document_id="doc-ommf-1"),),
    )


class TestObservabilityMetricsMonitoringFramework:
    def test_module_has_sixteen_components(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        assert service.component_registry.count() == 17

    def test_ommf_initializes_and_is_ready(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        snapshot = service.get_observability_metrics_monitoring_snapshot()
        assert snapshot is not None
        assert snapshot["framework"]["initialized"] is True
        assert snapshot["framework"]["ready"] is True
        assert snapshot["framework"]["source_bound"] is True

    def test_integrations_bound(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        pio = service.get_pipeline_orchestrator_snapshot()
        apqm = service.get_async_processing_queue_snapshot()
        ftrrf = service.get_fault_tolerance_snapshot()
        svaf = service.get_security_validation_audit_snapshot()
        assert pio["orchestrator"]["observability_bound"] is True
        assert apqm["manager"]["observability_bound"] is True
        assert ftrrf["framework"]["observability_bound"] is True
        assert svaf["framework"]["observability_bound"] is True

    def test_metrics_recorded_on_valid_flow(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        process_id = uuid4()

        service.submit_evidence_center_analysis(_analysis_request(process_id))
        service.process_async_queue_pending()

        ommf = service.observability_metrics_monitoring_framework.framework
        metrics = ommf.observability_snapshot()
        assert metrics["requests_received"] >= 1
        assert metrics["requests_processed"] >= 1
        assert metrics["validations_performed"] >= 1
        assert metrics["traces_total"] >= 1

    def test_trace_continuity_preserved(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        process_id = uuid4()

        service.submit_evidence_center_analysis(_analysis_request(process_id))
        service.process_async_queue_pending()

        ommf = service.observability_metrics_monitoring_framework.framework
        traces = ommf.traces_for_process(process_id)
        assert len(traces) >= 2
        trace_ids = {span["trace_id"] for span in traces}
        assert len(trace_ids) == 1

    def test_validation_failure_records_metrics(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        process_id = uuid4()

        service.submit_evidence_center_analysis(_analysis_request(process_id, codigo_req=""))

        ommf = service.observability_metrics_monitoring_framework.framework
        metrics = ommf.observability_snapshot()
        assert metrics["validations_performed"] >= 1
        assert metrics["processes_failed"] >= 1

    def test_health_monitor_initialized(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        ommf = service.observability_metrics_monitoring_framework.framework
        consolidated = ommf.consolidate()
        health = consolidated["health"]
        assert "PipelineIntegrationOrchestrator" in health
        assert health["PipelineIntegrationOrchestrator"]["status"] == ComponentHealthStatus.AVAILABLE.value

    def test_consolidation_includes_sibling_snapshots(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        process_id = uuid4()
        service.submit_evidence_center_analysis(_analysis_request(process_id))

        ommf = service.observability_metrics_monitoring_framework.framework
        consolidated = ommf.consolidate()
        sources = consolidated["sources"]
        assert sources["queue"] is not None
        assert sources["security"] is not None

    def test_events_registered_for_observability(self):
        event_manager = EventManager()
        service = EnterpriseIntegrationService(event_manager=event_manager)
        service.initialize()
        process_id = uuid4()

        service.submit_evidence_center_analysis(_analysis_request(process_id))
        assert event_manager.count_by_process(process_id) >= 2

    def test_uses_central_configuration(self):
        config = ConfigurationProvider.default()
        settings = config.enterprise_integration().observability_metrics_monitoring_framework
        assert settings.prepared is True
        assert settings.enabled is True
        assert settings.metrics_collector_prepared is True
        assert settings.opentelemetry_prepared is True

    def test_governance_declares_implementation_8_8(self):
        assert IMPLEMENTATION == "8.12"

    def test_no_motor_internal_imports_in_ommf(self):
        import importlib
        import pkgutil
        from pathlib import Path

        package = importlib.import_module("zovrake_motor.enterprise_integration.ommf")
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
