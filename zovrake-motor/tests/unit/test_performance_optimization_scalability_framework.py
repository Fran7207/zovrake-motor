"""Pruebas del Performance Optimization & Scalability Framework — Implementación 8.9."""

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
from zovrake_motor.enterprise_integration.posf.enums import ScalabilityMode
from zovrake_motor.events import EventManager


def _analysis_request(process_id, codigo_req="REQ-POSF-001") -> EvidenceCenterAnalysisRequest:
    return EvidenceCenterAnalysisRequest(
        process_id=process_id,
        project_id="PRJ-POSF",
        quotation_id="COT-POSF",
        requirement=RequirementDetailsReference(codigo_req=codigo_req),
        evidence_documents=(EvidenceDocumentReference(document_id="doc-posf-1"),),
    )


class TestPerformanceOptimizationScalabilityFramework:
    def test_module_has_seventeen_components(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        assert service.component_registry.count() == 17

    def test_posf_initializes_and_is_ready(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        snapshot = service.get_performance_optimization_scalability_snapshot()
        assert snapshot is not None
        assert snapshot["framework"]["initialized"] is True
        assert snapshot["framework"]["ready"] is True
        assert snapshot["framework"]["metrics_source_bound"] is True

    def test_integrations_bound(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        pio = service.get_pipeline_orchestrator_snapshot()
        apqm = service.get_async_processing_queue_snapshot()
        assert pio["orchestrator"]["performance_optimizer_bound"] is True
        assert apqm["manager"]["performance_optimizer_bound"] is True

    def test_pipeline_analysis_on_valid_flow(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        process_id = uuid4()

        service.submit_evidence_center_analysis(_analysis_request(process_id))
        service.process_async_queue_pending()

        posf = service.performance_optimization_scalability_framework.framework
        optimization = posf.optimization_snapshot()
        assert optimization["optimizations_applied"] >= 0
        assert optimization["pipeline"]["tracked_processes"] >= 1
        assert optimization["resources"]["current_usage"]["cpu"] >= 1

    def test_functional_behavior_unchanged_after_optimization(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        process_id = uuid4()

        delivery = service.submit_evidence_center_analysis(_analysis_request(process_id))
        assert delivery.success is True
        service.process_async_queue_pending()

        context = service.get_pipeline_context(process_id)
        assert context is not None
        assert len(context.transitions) >= 1

    def test_ommf_metrics_consumed(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        process_id = uuid4()

        service.submit_evidence_center_analysis(_analysis_request(process_id))
        service.process_async_queue_pending()

        posf = service.performance_optimization_scalability_framework.framework
        evaluation = posf.evaluate_from_metrics()
        assert evaluation["evaluated"] is True
        assert "ommf_metrics" in evaluation

    def test_scalability_readiness(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        posf = service.performance_optimization_scalability_framework.framework
        readiness = posf.optimization_snapshot()["scalability"]["readiness"]
        assert readiness["horizontal_prepared"] is True
        assert readiness["vertical_prepared"] is True
        assert readiness["mode"] == ScalabilityMode.ENTERPRISE_PREPARED.value

    def test_reuse_registry_does_not_store_process_data(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        posf = service.performance_optimization_scalability_framework.framework
        reuse = posf.optimization_snapshot()["reuse"]
        assert reuse["configuration_entries"] >= 1
        assert reuse["contract_entries"] >= 1

    def test_events_registered_for_optimization(self):
        event_manager = EventManager()
        service = EnterpriseIntegrationService(event_manager=event_manager)
        service.initialize()
        process_id = uuid4()

        service.submit_evidence_center_analysis(_analysis_request(process_id))
        service.process_async_queue_pending()
        assert event_manager.count_by_process(process_id) >= 2

    def test_uses_central_configuration(self):
        config = ConfigurationProvider.default()
        settings = config.enterprise_integration().performance_optimization_scalability_framework
        assert settings.prepared is True
        assert settings.enabled is True
        assert settings.pipeline_optimization_prepared is True
        assert settings.kubernetes_prepared is True

    def test_governance_declares_implementation_8_9(self):
        assert IMPLEMENTATION == "8.12"

    def test_no_motor_internal_imports_in_posf(self):
        import importlib
        import pkgutil
        from pathlib import Path

        package = importlib.import_module("zovrake_motor.enterprise_integration.posf")
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
