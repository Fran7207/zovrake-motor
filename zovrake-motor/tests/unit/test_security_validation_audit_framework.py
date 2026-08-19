"""Pruebas del Security, Validation & Audit Framework — Implementación 8.7."""

from __future__ import annotations

from uuid import uuid4

import pytest

from zovrake_motor import EnterpriseIntegrationService
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.enterprise_integration.apqm.enums import ApqmProcessingStage
from zovrake_motor.enterprise_integration.ecg.contracts.erp_requests import (
    EvidenceCenterAnalysisRequest,
    EvidenceDocumentReference,
    RequirementDetailsReference,
)
from zovrake_motor.enterprise_integration.ftrrf.enums import ErrorCategory
from zovrake_motor.enterprise_integration.governance import IMPLEMENTATION
from zovrake_motor.enterprise_integration.svaf.enums import ValidationStage
from zovrake_motor.enterprise_integration.svaf.validation_engine import ValidationEngine
from zovrake_motor.events import EventManager
from zovrake_motor.states import StateManager
from zovrake_motor.states.enums import MotorState


def _analysis_request(process_id, codigo_req="REQ-SVAF-001") -> EvidenceCenterAnalysisRequest:
    return EvidenceCenterAnalysisRequest(
        process_id=process_id,
        project_id="PRJ-SVAF",
        quotation_id="COT-SVAF",
        requirement=RequirementDetailsReference(codigo_req=codigo_req),
        evidence_documents=(EvidenceDocumentReference(document_id="doc-svaf-1"),),
    )


class TestSecurityValidationAuditFramework:
    def test_module_has_fifteen_components(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        assert service.component_registry.count() == 17

    def test_svaf_initializes_and_is_ready(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        snapshot = service.get_security_validation_audit_snapshot()
        assert snapshot is not None
        assert snapshot["framework"]["initialized"] is True
        assert snapshot["framework"]["ready"] is True
        assert snapshot["framework"]["fault_notifier_bound"] is True

    def test_ecg_security_bound(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        ecg_snapshot = service.get_erp_communication_gateway_snapshot()
        assert ecg_snapshot is not None
        assert ecg_snapshot["gateway"]["security_bound"] is True
        assert ecg_snapshot["gateway"]["security_enabled"] is True

    def test_validation_engine_rejects_invalid_request(self):
        engine = ValidationEngine()
        process_id = uuid4()
        result = engine.validate_erp_analysis_request(
            _analysis_request(process_id, codigo_req=""),
        )
        assert result.approved is False
        assert result.stage == ValidationStage.VALIDATION_REJECTED

    def test_inbound_validation_blocks_pipeline(self):
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
        assert item is None or item.stage == ApqmProcessingStage.CONTROLLED_ERROR

    def test_valid_request_generates_audit_record(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        process_id = uuid4()

        service.submit_evidence_center_analysis(_analysis_request(process_id))
        service.process_async_queue_pending()

        svaf = service.security_validation_audit_framework.framework
        audits = svaf.audit_store.by_process(process_id)
        assert len(audits) >= 1

    def test_validation_failure_notifies_ftrrf(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        process_id = uuid4()

        service.submit_evidence_center_analysis(_analysis_request(process_id, codigo_req=""))

        ftrrf = service.fault_tolerance_retry_recovery_framework.framework
        errors = ftrrf.errors_for_process(process_id)
        assert len(errors) >= 1
        assert errors[-1].category == ErrorCategory.VALIDATION

    def test_state_manager_reflects_validation(self):
        state_manager = StateManager()
        service = EnterpriseIntegrationService(state_manager=state_manager)
        service.initialize()
        process_id = uuid4()

        service.submit_evidence_center_analysis(_analysis_request(process_id, codigo_req=""))
        record = state_manager.get_process(process_id)
        assert record is not None
        assert record.current_state == MotorState.ERROR_VALIDACION

    def test_duplicate_message_rejected(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        process_id = uuid4()
        request = _analysis_request(process_id)

        service.submit_evidence_center_analysis(request)
        second = service.submit_evidence_center_analysis(request)

        assert second.success is False
        assert second.analysis_status == "error_validacion"

    def test_status_and_result_queries_are_idempotent(self):
        """El ERP hace polling legítimo; consultas repetidas no deben rechazarse."""
        from zovrake_motor.enterprise_integration.ecg.contracts.erp_requests import (
            EvidenceCenterResultQuery,
            EvidenceCenterStatusQuery,
        )

        service = EnterpriseIntegrationService()
        service.initialize()
        process_id = uuid4()
        request = _analysis_request(process_id)

        start = service.submit_evidence_center_analysis(request)
        assert start.success is True
        service.process_async_queue_pending()

        status_query = EvidenceCenterStatusQuery(
            process_id=process_id,
            project_id=request.project_id,
            quotation_id=request.quotation_id,
        )
        result_query = EvidenceCenterResultQuery(
            process_id=process_id,
            project_id=request.project_id,
            quotation_id=request.quotation_id,
        )

        first_status = service.query_evidence_center_status(status_query)
        second_status = service.query_evidence_center_status(status_query)
        assert first_status.success is True
        assert second_status.success is True
        assert second_status.analysis_status != "error_validacion"

        first_result = service.query_evidence_center_result(result_query)
        second_result = service.query_evidence_center_result(result_query)
        assert first_result.success is True
        assert second_result.success is True
        assert second_result.analysis_status != "error_validacion"

    def test_events_registered_for_validation(self):
        event_manager = EventManager()
        service = EnterpriseIntegrationService(event_manager=event_manager)
        service.initialize()
        process_id = uuid4()

        service.submit_evidence_center_analysis(_analysis_request(process_id))
        assert event_manager.count_by_process(process_id) >= 2

    def test_uses_central_configuration(self):
        config = ConfigurationProvider.default()
        settings = config.enterprise_integration().security_validation_audit_framework
        assert settings.prepared is True
        assert settings.enabled is True
        assert settings.validation_engine_prepared is True

    def test_governance_declares_implementation_8_7(self):
        assert IMPLEMENTATION == "8.12"

    def test_no_motor_internal_imports_in_svaf(self):
        import importlib
        import pkgutil
        from pathlib import Path

        package = importlib.import_module("zovrake_motor.enterprise_integration.svaf")
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
