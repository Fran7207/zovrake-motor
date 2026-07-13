"""Pipeline E2E ERP (Centro de Evidencias) ↔ API REST ↔ Motor — Implementación 9.4."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from zovrake_motor.api.bootstrap import MotorApiRuntime, build_motor_api_runtime
from zovrake_motor.api.enums import IntegrationApiLifecycleStage


@dataclass
class ErpMotorIntegrationE2EResult:
    """Resultado del flujo End-to-End certificado vía API REST oficial."""

    analysis_id: UUID
    codigo_req: str
    project_id: str
    quotation_id: str
    submit_http_status: int
    submit_success: bool
    submit_async: bool
    queue_processed: int
    pipeline_transitions: int
    status_query_success: bool
    result_query_success: bool
    final_stage: str
    event_count: int
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        processing_evidence = (
            self.queue_processed >= 1
            or self.pipeline_transitions >= 1
            or self.event_count >= 1
        )
        return (
            self.submit_http_status == 202
            and self.submit_success
            and self.submit_async
            and processing_evidence
            and self.status_query_success
            and self.result_query_success
        )


def build_erp_evidence_center_payload(
    analysis_id: UUID | None = None,
    *,
    codigo_req: str = "REQ-E2E-ERP",
    project_id: str = "BT-E2E-COT",
    quotation_id: str = "BT-E2E-COT",
) -> dict[str, Any]:
    """Payload HTTP equivalente al contrato enviado por ZovrakeMotorIntegration."""
    return {
        "analysis_id": str(analysis_id or uuid4()),
        "codigo_req": codigo_req,
        "project_id": project_id,
        "quotation_id": quotation_id,
        "requirement": {
            "codigo_req": codigo_req,
            "description": "Certificación E2E ERP ↔ Motor",
            "metadata": {"obra": "Obra certificación"},
        },
        "documents": [
            {
                "document_id": "doc-e2e-erp-001",
                "document_label": "Cotización proveedor A",
                "content_type": "application/pdf",
                "metadata": {
                    "file_name": "cotizacion-a.pdf",
                    "source": "evidence_center",
                },
            },
        ],
        "metadata": {
            "source": "evidence_center",
            "erp_module": "logistica_cotizaciones",
            "trigger": "analizar_cotizaciones",
        },
        "contract_version": "v1",
    }


def run_erp_motor_integration_e2e_pipeline(
    *,
    runtime: MotorApiRuntime | None = None,
) -> ErpMotorIntegrationE2EResult:
    """
    Ejecuta el flujo completo simulando el ERP vía API REST oficial.

    Centro de Evidencias → API → IntegrationApiService → ECG → Coordinator → Motor → ERP.
    """
    runtime = runtime or build_motor_api_runtime()
    payload = build_erp_evidence_center_payload()
    analysis_id = UUID(payload["analysis_id"])

    from fastapi.testclient import TestClient

    from zovrake_motor.api.http.app import create_app

    client = TestClient(create_app(runtime=runtime))
    create_response = client.post("/api/v1/analyses", json=payload)
    create_body = create_response.json()

    queue_processed = 0
    for _ in range(5):
        processed = runtime.integration_api.process_pending()
        if processed == 0:
            processed = runtime.enterprise_integration.process_async_queue_pending()
        queue_processed += processed
        pending = runtime.enterprise_integration.get_async_processing_queue_snapshot()
        if pending["manager"]["pending_count"] == 0:
            break

    context = runtime.enterprise_integration.get_pipeline_context(analysis_id)
    transitions = len(context.transitions) if context is not None else 0

    status_response = client.get(
        f"/api/v1/analyses/{analysis_id}/status",
        params={"project_id": payload["project_id"], "quotation_id": payload["quotation_id"]},
    )
    status_body = status_response.json()

    result_response = client.get(
        f"/api/v1/analyses/{analysis_id}/result",
        params={"project_id": payload["project_id"], "quotation_id": payload["quotation_id"]},
    )
    result_body = result_response.json()

    return ErpMotorIntegrationE2EResult(
        analysis_id=analysis_id,
        codigo_req=payload["codigo_req"],
        project_id=payload["project_id"],
        quotation_id=payload["quotation_id"],
        submit_http_status=create_response.status_code,
        submit_success=bool(create_body.get("success")),
        submit_async=create_body.get("status") == IntegrationApiLifecycleStage.SENT_TO_MOTOR.value,
        queue_processed=queue_processed,
        pipeline_transitions=transitions,
        status_query_success=bool(status_body.get("success")),
        result_query_success=bool(result_body.get("success")),
        final_stage=str(status_body.get("status", "")),
        event_count=runtime.event_manager.count_by_process(analysis_id),
        metadata={
            "create_message": create_body.get("message"),
            "status_message": status_body.get("message"),
            "result_message": result_body.get("message"),
            "contract_version": create_body.get("contract_version"),
        },
    )
