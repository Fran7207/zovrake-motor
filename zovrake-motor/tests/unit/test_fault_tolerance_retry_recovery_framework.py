"""Pruebas del Fault Tolerance, Retry & Recovery Framework — Implementación 8.6."""

from __future__ import annotations

from uuid import uuid4

import pytest

from zovrake_motor import EnterpriseIntegrationService
from zovrake_motor.config import ConfigurationProvider
from zovrake_motor.enterprise_integration.apqm.models import QueueItemContext
from zovrake_motor.enterprise_integration.ecg.contracts.erp_requests import (
    EvidenceCenterAnalysisRequest,
    EvidenceDocumentReference,
    RequirementDetailsReference,
)
from zovrake_motor.enterprise_integration.ftrrf.classifier import ErrorClassifier
from zovrake_motor.enterprise_integration.ftrrf.enums import (
    ErrorCategory,
    RecoveryDecision,
    RecoveryStatus,
)
from zovrake_motor.enterprise_integration.ftrrf.retry_policy import RetryPolicyRegistry
from zovrake_motor.enterprise_integration.governance import IMPLEMENTATION
from zovrake_motor.enterprise_integration.internal_api import StartAnalysisRequest
from zovrake_motor.events import EventManager
from zovrake_motor.states import StateManager
from zovrake_motor.states.enums import MotorState


def _analysis_request(process_id, codigo_req="REQ-FT-001") -> EvidenceCenterAnalysisRequest:
    return EvidenceCenterAnalysisRequest(
        process_id=process_id,
        project_id="PRJ-FT",
        quotation_id="COT-FT",
        requirement=RequirementDetailsReference(codigo_req=codigo_req),
        evidence_documents=(EvidenceDocumentReference(document_id="doc-ft-1"),),
    )


class _FailResponse:
    def __init__(self, error_code: str, message: str = "fallo controlado") -> None:
        self.success = False
        self.message = message

        class _Code:
            value = error_code

        self.error_code = _Code()


class _OkResponse:
    success = True
    message = "ok"


class _FlakyExecution:
    """Ejecución que falla un número de veces y luego tiene éxito."""

    def __init__(self, fail_times: int, error_code: str = "coordinator_required") -> None:
        self.calls = 0
        self._fail_times = fail_times
        self._error_code = error_code

    def execute_start_analysis(self, request):
        self.calls += 1
        if self.calls <= self._fail_times:
            return _FailResponse(self._error_code)
        return _OkResponse()


class TestFaultToleranceRetryRecoveryFramework:
    def test_module_has_fourteen_components(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        assert service.component_registry.count() == 17

    def test_ftrrf_initializes_and_is_ready(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        snapshot = service.get_fault_tolerance_snapshot()
        assert snapshot is not None
        assert snapshot["framework"]["initialized"] is True
        assert snapshot["framework"]["ready"] is True
        assert snapshot["framework"]["continuity_bound"] is True

    def test_classifier_categorizes_errors(self):
        classifier = ErrorClassifier()
        assert classifier.classify(error_code="structural_validation_failed").category == (
            ErrorCategory.VALIDATION
        )
        assert classifier.classify(error_code="coordinator_required").category == (
            ErrorCategory.COMMUNICATION
        )
        assert classifier.classify(error_code="operation_not_executed").category == (
            ErrorCategory.PROCESSING
        )
        assert classifier.classify(description="documento faltante").category == (
            ErrorCategory.DOCUMENTAL
        )

    def test_retry_policy_only_recoverable(self):
        registry = RetryPolicyRegistry(default_max_retries=3)
        communication = registry.policy_for(ErrorCategory.COMMUNICATION)
        validation = registry.policy_for(ErrorCategory.VALIDATION)

        assert communication.recoverable is True
        assert communication.allows_retry(1) is True
        assert validation.recoverable is False
        assert validation.allows_retry(1) is False

    def test_validation_error_is_terminal_and_isolated(self):
        state_manager = StateManager()
        service = EnterpriseIntegrationService(state_manager=state_manager)
        service.initialize()
        process_id = uuid4()

        service.submit_evidence_center_analysis(_analysis_request(process_id, codigo_req=""))
        service.process_async_queue_pending()

        ftrrf = service.fault_tolerance_retry_recovery_framework.framework
        errors = ftrrf.errors_for_process(process_id)
        assert len(errors) >= 1
        assert errors[-1].category == ErrorCategory.VALIDATION
        assert errors[-1].recovery_status == RecoveryStatus.FAILED

        record = state_manager.get_process(process_id)
        assert record is not None
        assert record.current_state == MotorState.ERROR_VALIDACION

    def test_recoverable_error_retries_and_recovers(self):
        state_manager = StateManager()
        service = EnterpriseIntegrationService(state_manager=state_manager)
        service.initialize()
        process_id = uuid4()

        state_manager.create_process(process_id, "REQ-FT-RECOVER")

        manager = service.async_processing_queue_manager.manager
        flaky = _FlakyExecution(fail_times=1, error_code="coordinator_required")
        manager.bind_execution(flaky)

        manager.enqueue_start_analysis(
            StartAnalysisRequest(process_id=process_id, codigo_req="REQ-FT-RECOVER"),
            source_context=QueueItemContext(
                process_id=process_id,
                project_id="PRJ-FT",
                quotation_id="COT-FT",
                codigo_req="REQ-FT-RECOVER",
                source="ecg",
            ),
        )
        manager.process_all_pending()

        item = manager.get_item_by_process(process_id)
        assert item is not None
        assert item.stage.value == "procesamiento_completado"
        assert item.execution_metadata.get("recovered") is True
        assert flaky.calls == 2

        ftrrf = service.fault_tolerance_retry_recovery_framework.framework
        errors = ftrrf.errors_for_process(process_id)
        assert errors[-1].recovery_status == RecoveryStatus.RECOVERED
        assert errors[-1].category == ErrorCategory.COMMUNICATION

    def test_only_apqm_can_request_recovery(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        ftrrf = service.fault_tolerance_retry_recovery_framework.framework

        with pytest.raises(PermissionError):
            ftrrf.handle_failure(
                process_id=uuid4(),
                item_id="item-x",
                error_message="fallo",
                requested_by="erp",
            )

    def test_fault_isolation_between_processes(self):
        service = EnterpriseIntegrationService()
        service.initialize()
        process_a = uuid4()
        process_b = uuid4()

        service.submit_evidence_center_analysis(_analysis_request(process_a, codigo_req=""))
        service.submit_evidence_center_analysis(_analysis_request(process_b, codigo_req=""))
        service.process_async_queue_pending()

        ftrrf = service.fault_tolerance_retry_recovery_framework.framework
        errors_a = ftrrf.errors_for_process(process_a)
        errors_b = ftrrf.errors_for_process(process_b)

        assert len(errors_a) >= 1
        assert len(errors_b) >= 1
        assert all(e.process_id == process_a for e in errors_a)
        assert all(e.process_id == process_b for e in errors_b)

    def test_events_registered_for_faults(self):
        event_manager = EventManager()
        service = EnterpriseIntegrationService(event_manager=event_manager)
        service.initialize()
        process_id = uuid4()

        service.submit_evidence_center_analysis(_analysis_request(process_id, codigo_req=""))
        service.process_async_queue_pending()

        assert event_manager.count_by_process(process_id) >= 3

    def test_uses_central_configuration(self):
        config = ConfigurationProvider.default()
        settings = config.enterprise_integration().fault_tolerance_retry_recovery_framework
        assert settings.prepared is True
        assert settings.enabled is True
        assert settings.default_max_retries == 3
        assert settings.process_isolation_enforced is True

    def test_governance_declares_implementation_8_7(self):
        assert IMPLEMENTATION == "8.12"

    def test_no_motor_internal_imports_in_ftrrf(self):
        import importlib
        import pkgutil
        from pathlib import Path

        package = importlib.import_module("zovrake_motor.enterprise_integration.ftrrf")
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
