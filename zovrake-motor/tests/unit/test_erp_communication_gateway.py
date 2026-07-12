"""Pruebas del ERP Communication Gateway — Implementación 8.4/8.5."""

from __future__ import annotations

from uuid import uuid4

from zovrake_motor import EnterpriseIntegrationService
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.enterprise_integration.ecg.contracts.erp_requests import (
    EvidenceCenterAnalysisRequest,
    EvidenceCenterResultQuery,
    EvidenceCenterStatusQuery,
    EvidenceDocumentReference,
    RequirementDetailsReference,
)
from zovrake_motor.enterprise_integration.governance import IMPLEMENTATION
from zovrake_motor.events import EventManager
from zovrake_motor.states import StateManager


def _analysis_request(process_id, codigo_req: str = "REQ-ECG-001") -> EvidenceCenterAnalysisRequest:
    return EvidenceCenterAnalysisRequest(
        process_id=process_id,
        project_id="PRJ-ECG",
        quotation_id="COT-001",
        requirement=RequirementDetailsReference(
            codigo_req=codigo_req,
            description="Requerimiento de prueba",
        ),
        evidence_documents=(
            EvidenceDocumentReference(document_id="doc-001", document_label="Plano"),
        ),
        analysis_metadata={"priority": "normal"},
    )


class TestErpCommunicationGateway:
    def test_module_has_fourteen_components(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        assert service.component_registry.count() == 17

    def test_ecg_initializes_and_is_ready(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        snapshot = service.get_erp_communication_gateway_snapshot()
        assert snapshot is not None
        gateway = snapshot["gateway"]
        assert gateway["initialized"] is True
        assert gateway["ready"] is True
        assert gateway["dispatch_bound"] is True
        assert gateway["enqueue_bound"] is True
        assert gateway["async_queue_enabled"] is True

    def test_submit_enqueues_and_routes_through_pio(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        process_id = uuid4()

        delivery = service.submit_evidence_center_analysis(_analysis_request(process_id))

        assert delivery.success is True
        assert delivery.analysis_status == "procesamiento_pendiente"
        assert delivery.metadata.get("async") is True

        service.process_async_queue_pending()

        context = service.get_pipeline_context(process_id)
        assert context is not None
        assert len(context.transitions) >= 1

    def test_status_and_result_queries_return_erp_delivery(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        process_id = uuid4()

        service.submit_evidence_center_analysis(_analysis_request(process_id))
        service.process_async_queue_pending()

        status_delivery = service.query_evidence_center_status(
            EvidenceCenterStatusQuery(
                process_id=process_id,
                project_id="PRJ-ECG",
                quotation_id="COT-001",
            ),
        )
        result_delivery = service.query_evidence_center_result(
            EvidenceCenterResultQuery(
                process_id=process_id,
                project_id="PRJ-ECG",
                quotation_id="COT-001",
            ),
        )

        assert status_delivery.success is True
        assert result_delivery.success is True
        assert status_delivery.immutable is True
        assert result_delivery.immutable is True

    def test_invalid_request_rejected_before_queue(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        process_id = uuid4()

        delivery = service.submit_evidence_center_analysis(
            _analysis_request(process_id, codigo_req=""),
        )

        assert delivery.success is False
        assert delivery.analysis_status == "error_validacion"
        assert delivery.metadata.get("svaf_validated") is True

        item = service.async_processing_queue_manager.manager.get_item_by_process(process_id)
        assert item is None

    def test_messages_recorded_in_store(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        process_id = uuid4()

        service.submit_evidence_center_analysis(_analysis_request(process_id))

        ecg = service.erp_communication_gateway
        assert ecg is not None
        assert ecg.gateway.message_store.count() >= 2

    def test_state_manager_updated_on_submission(self):
        state_manager = StateManager()
        service = EnterpriseIntegrationService(state_manager=state_manager)
        service.initialize()
        process_id = uuid4()

        service.submit_evidence_center_analysis(_analysis_request(process_id))

        record = state_manager.get_process(process_id)
        assert record is not None
        assert record.metadata.get("source") == "evidence_center"

    def test_events_registered_for_communication(self):
        event_manager = EventManager()
        service = EnterpriseIntegrationService(event_manager=event_manager)
        service.initialize()
        process_id = uuid4()

        service.submit_evidence_center_analysis(_analysis_request(process_id))

        assert event_manager.count_by_process(process_id) >= 2

    def test_uses_central_configuration(self):
        config = ConfigurationProvider.default()
        settings = config.enterprise_integration().erp_communication_gateway
        assert settings.prepared is True
        assert settings.immutability_enforced is True
        assert settings.evidence_center_integration_prepared is True

    def test_prepare_reports_ecg_ready(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        process_id = uuid4()

        from zovrake_motor.enterprise_integration import EnterpriseIntegrationRequest

        result = service.prepare(
            EnterpriseIntegrationRequest(process_id=process_id, codigo_req="REQ-ECG-PREP"),
        )

        assert result.metadata["erp_communication_gateway_ready"] is True
        assert result.metadata["async_processing_queue_manager_ready"] is True
        assert result.components_ready == 17

    def test_governance_declares_implementation_8_7(self):
        assert IMPLEMENTATION == "8.12"

    def test_no_motor_internal_imports_in_ecg(self):
        import importlib
        import pkgutil
        from pathlib import Path

        package = importlib.import_module("zovrake_motor.enterprise_integration.ecg")
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
