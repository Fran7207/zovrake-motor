"""Pipeline de certificación End-to-End — Módulo de Integración Empresarial."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from zovrake_motor.enterprise_integration.ecg.contracts.erp_requests import (
    EvidenceCenterAnalysisRequest,
    EvidenceCenterResultQuery,
    EvidenceCenterStatusQuery,
    EvidenceDocumentReference,
    RequirementDetailsReference,
)
from zovrake_motor.enterprise_integration.service import EnterpriseIntegrationService
from zovrake_motor.events import EventManager
from zovrake_motor.states import StateManager


@dataclass
class EnterpriseIntegrationE2EPipelineResult:
    """Resultado del flujo End-to-End certificado."""

    process_id: UUID
    codigo_req: str
    project_id: str
    quotation_id: str
    submit_success: bool
    submit_async: bool
    queue_processed: int
    pipeline_transitions: int
    status_query_success: bool
    result_query_success: bool
    event_count: int
    trace_span_count: int
    audit_count: int
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return (
            self.submit_success
            and self.submit_async
            and self.queue_processed >= 1
            and self.pipeline_transitions >= 1
            and self.status_query_success
            and self.result_query_success
            and self.event_count >= 1
        )


def build_evidence_center_request(
    process_id: UUID | None = None,
    *,
    codigo_req: str = "REQ-E2E-CERT",
    project_id: str = "PRJ-E2E",
    quotation_id: str = "COT-E2E",
) -> EvidenceCenterAnalysisRequest:
    pid = process_id or uuid4()
    return EvidenceCenterAnalysisRequest(
        process_id=pid,
        project_id=project_id,
        quotation_id=quotation_id,
        requirement=RequirementDetailsReference(
            codigo_req=codigo_req,
            description="Requerimiento de certificación End-to-End",
        ),
        evidence_documents=(
            EvidenceDocumentReference(
                document_id="doc-e2e-001",
                document_label="Evidencia certificación",
            ),
        ),
        analysis_metadata={"certification": "8.10", "source": "evidence_center"},
    )


def run_full_enterprise_integration_e2e_pipeline(
    *,
    service: EnterpriseIntegrationService | None = None,
    state_manager: StateManager | None = None,
    event_manager: EventManager | None = None,
) -> EnterpriseIntegrationE2EPipelineResult:
    """
    Ejecuta el flujo completo ERP (Centro de Evidencias) → Motor → ERP.

    Simula el camino oficial sin acceder al ERP frontend ni a lógica interna del Motor.
    """
    state_manager = state_manager or StateManager()
    event_manager = event_manager or EventManager()
    service = service or EnterpriseIntegrationService(
        state_manager=state_manager,
        event_manager=event_manager,
    )
    service.initialize()

    request = build_evidence_center_request()
    process_id = request.process_id

    submit_delivery = service.submit_evidence_center_analysis(request)
    queue_processed = service.process_async_queue_pending()

    context = service.get_pipeline_context(process_id)
    transitions = len(context.transitions) if context is not None else 0

    status_delivery = service.query_evidence_center_status(
        EvidenceCenterStatusQuery(
            process_id=process_id,
            project_id=request.project_id,
            quotation_id=request.quotation_id,
        ),
    )
    result_delivery = service.query_evidence_center_result(
        EvidenceCenterResultQuery(
            process_id=process_id,
            project_id=request.project_id,
            quotation_id=request.quotation_id,
        ),
    )

    ommf = service.observability_metrics_monitoring_framework
    svaf = service.security_validation_audit_framework
    trace_count = 0
    audit_count = 0
    if ommf is not None:
        trace_count = len(ommf.framework.traces_for_process(process_id))
    if svaf is not None:
        audit_count = len(svaf.framework.audit_store.by_process(process_id))

    return EnterpriseIntegrationE2EPipelineResult(
        process_id=process_id,
        codigo_req=request.requirement.codigo_req,
        project_id=request.project_id,
        quotation_id=request.quotation_id,
        submit_success=submit_delivery.success,
        submit_async=submit_delivery.metadata.get("async") is True,
        queue_processed=queue_processed,
        pipeline_transitions=transitions,
        status_query_success=status_delivery.success,
        result_query_success=result_delivery.success,
        event_count=event_manager.count_by_process(process_id),
        trace_span_count=trace_count,
        audit_count=audit_count,
        metadata={
            "submit_analysis_status": submit_delivery.analysis_status,
            "status_analysis_status": status_delivery.analysis_status,
            "result_analysis_status": result_delivery.analysis_status,
        },
    )
