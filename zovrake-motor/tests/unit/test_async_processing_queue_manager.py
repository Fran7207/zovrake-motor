"""Pruebas del Asynchronous Processing & Queue Manager — Implementación 8.5."""

from __future__ import annotations

from uuid import uuid4

from zovrake_motor import EnterpriseIntegrationService
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.enterprise_integration.apqm.enums import ApqmProcessingStage
from zovrake_motor.enterprise_integration.ecg.contracts.erp_requests import (
    EvidenceCenterAnalysisRequest,
    EvidenceDocumentReference,
    RequirementDetailsReference,
)
from zovrake_motor.enterprise_integration.governance import IMPLEMENTATION
from zovrake_motor.events import EventManager
from zovrake_motor.states import StateManager
from zovrake_motor.states.enums import MotorState


def _analysis_request(process_id, codigo_req: str = "REQ-APQM-001") -> EvidenceCenterAnalysisRequest:
    return EvidenceCenterAnalysisRequest(
        process_id=process_id,
        project_id="PRJ-APQM",
        quotation_id="COT-APQM",
        requirement=RequirementDetailsReference(codigo_req=codigo_req),
        evidence_documents=(
            EvidenceDocumentReference(document_id="doc-apqm-1"),
        ),
    )


class TestAsyncProcessingQueueManager:
    def test_module_has_fourteen_components(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        assert service.component_registry.count() == 17

    def test_apqm_initializes_and_is_ready(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        snapshot = service.get_async_processing_queue_snapshot()
        assert snapshot is not None
        assert snapshot["manager"]["initialized"] is True
        assert snapshot["manager"]["ready"] is True
        assert snapshot["manager"]["execution_bound"] is True

    def test_ecg_enqueues_without_blocking_erp(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        process_id = uuid4()

        delivery = service.submit_evidence_center_analysis(_analysis_request(process_id))

        assert delivery.success is True
        assert delivery.analysis_status == "procesamiento_pendiente"
        assert delivery.metadata.get("async") is True

        item = service.async_processing_queue_manager.manager.get_item_by_process(process_id)
        assert item is not None
        assert item.stage == ApqmProcessingStage.QUEUED

    def test_queue_processes_via_pio(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        process_id = uuid4()

        service.submit_evidence_center_analysis(_analysis_request(process_id))
        processed = service.process_async_queue_pending()

        assert processed == 1
        item = service.async_processing_queue_manager.manager.get_item_by_process(process_id)
        assert item is not None
        assert item.stage == ApqmProcessingStage.PROCESSING_COMPLETED
        assert item.started_at is not None
        assert item.completed_at is not None

        context = service.get_pipeline_context(process_id)
        assert context is not None
        assert context.motor_executed is False

    def test_multiple_processes_isolated(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        process_a = uuid4()
        process_b = uuid4()

        service.submit_evidence_center_analysis(_analysis_request(process_a, "REQ-A"))
        service.submit_evidence_center_analysis(_analysis_request(process_b, "REQ-B"))
        service.process_async_queue_pending()

        item_a = service.async_processing_queue_manager.manager.get_item_by_process(process_a)
        item_b = service.async_processing_queue_manager.manager.get_item_by_process(process_b)

        assert item_a is not None and item_b is not None
        assert item_a.context.codigo_req == "REQ-A"
        assert item_b.context.codigo_req == "REQ-B"
        assert item_a.item_id != item_b.item_id

    def test_state_manager_updated_on_enqueue_and_execution(self):
        state_manager = StateManager()
        service = EnterpriseIntegrationService(state_manager=state_manager)
        service.initialize()
        process_id = uuid4()

        service.submit_evidence_center_analysis(_analysis_request(process_id))
        pending = state_manager.get_process(process_id)
        assert pending is not None
        assert pending.current_state == MotorState.PROCESAMIENTO_PENDIENTE

        service.process_async_queue_pending()
        final = state_manager.get_process(process_id)
        assert final is not None
        assert final.current_state.value == "finalizado"

    def test_events_registered_for_queue_lifecycle(self):
        event_manager = EventManager()
        service = EnterpriseIntegrationService(event_manager=event_manager)
        service.initialize()
        process_id = uuid4()

        service.submit_evidence_center_analysis(_analysis_request(process_id))
        service.process_async_queue_pending()

        assert event_manager.count_by_process(process_id) >= 3

    def test_rejects_non_ecg_source(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        manager = service.async_processing_queue_manager.manager

        from zovrake_motor.enterprise_integration.apqm.models import QueueItemContext
        from zovrake_motor.enterprise_integration.internal_api import StartAnalysisRequest

        process_id = uuid4()
        result = manager.enqueue_start_analysis(
            StartAnalysisRequest(process_id=process_id, codigo_req="REQ-X"),
            source_context=QueueItemContext(
                process_id=process_id,
                project_id="P",
                quotation_id="Q",
                codigo_req="REQ-X",
                source="invalid",
            ),
        )

        assert result.success is False

    def test_uses_central_configuration(self):
        config = ConfigurationProvider.default()
        settings = config.enterprise_integration().async_processing_queue_manager
        assert settings.prepared is True
        assert settings.enabled is True
        assert settings.max_concurrent_workers == 10

    def test_governance_declares_current_implementation(self):
        assert IMPLEMENTATION == "8.12"

    def test_no_motor_internal_imports_in_apqm(self):
        import importlib
        import pkgutil
        from pathlib import Path

        package = importlib.import_module("zovrake_motor.enterprise_integration.apqm")
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
