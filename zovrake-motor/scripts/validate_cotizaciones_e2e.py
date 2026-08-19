"""Validación E2E Cotizaciones: ejecución real del Motor con documentos de evidencia."""

from __future__ import annotations

import base64
from uuid import uuid4

from zovrake_motor.api.bootstrap import build_motor_api_runtime
from zovrake_motor.api.models import (
    AnalysisDocumentReference,
    PublicAnalysisRequest,
    PublicResultQuery,
    PublicStatusQuery,
    RequirementContext,
)


def _data_url(text: str) -> str:
    return "data:text/plain;base64," + base64.b64encode(text.encode("utf-8")).decode("ascii")


def main() -> None:
    text_a = """COTIZACION
Proveedor: ACME S.A.C.
Moneda: USD
Total: 1500.00
Condiciones de pago: 30 dias
Acero inoxidable 304    100 kg    12.50
Servicio de instalacion    1 und    250.00
"""
    text_b = """COTIZACION
Proveedor: BETA MATERIALES EIRL
Moneda: USD
Total: 1400.00
Condiciones de pago: Contado
Acero inoxidable 304    100 kg    11.80
Servicio de instalacion    1 und    220.00
"""

    runtime = build_motor_api_runtime()
    analysis_id = uuid4()
    request = PublicAnalysisRequest(
        analysis_id=analysis_id,
        codigo_req="REQ-0022",
        project_id="EL-0002",
        quotation_id="EL-0002",
        requirement=RequirementContext(
            codigo_req="REQ-0022",
            description="Requerimiento de materiales",
            metadata={"obra": "Chinbote"},
        ),
        documents=(
            AnalysisDocumentReference(
                document_id="doc-1",
                document_label="COTIZACION A.pdf",
                content_type="text/plain",
                metadata={
                    "file_name": "a.pdf",
                    "content_data_url": _data_url(text_a),
                    "source": "evidence_center",
                },
            ),
            AnalysisDocumentReference(
                document_id="doc-2",
                document_label="COTIZACION B.pdf",
                content_type="text/plain",
                metadata={
                    "file_name": "b.pdf",
                    "content_data_url": _data_url(text_b),
                    "source": "evidence_center",
                },
            ),
        ),
        metadata={
            "source": "evidence_center",
            "erp_module": "logistica_cotizaciones",
            "trigger": "analizar_cotizaciones",
        },
    )

    start = runtime.integration_api.start_analysis(request)
    print("START", start.success, start.status.stage.value, start.status.message)

    processed_total = 0
    for attempt in range(5):
        processed = runtime.integration_api.process_pending()
        processed_total += processed
        print("PENDING", attempt, processed)
        if processed == 0:
            break

    status = runtime.integration_api.query_status(
        PublicStatusQuery(
            analysis_id=analysis_id,
            project_id="EL-0002",
            quotation_id="EL-0002",
        ),
    )
    print(
        "STATUS",
        status.success,
        status.status.stage.value,
        status.status.message,
        "executed_meta",
        (status.metadata or {}).get("executed"),
    )

    result = runtime.integration_api.query_result(
        PublicResultQuery(
            analysis_id=analysis_id,
            project_id="EL-0002",
            quotation_id="EL-0002",
        ),
    )
    print("RESULT", result.success, result.status.message)
    assert result.success, "query_result debe ser exitoso"
    assert result.result is not None, "debe existir resultado"
    payload = result.result.payload
    print("payload.executed", payload.get("executed"))
    metadata = payload.get("metadata") or {}
    print("meta.executed", metadata.get("executed"))
    print("has_comparative", bool(metadata.get("comparative_tables")))
    print("has_intelligent", bool(metadata.get("intelligent_analysis")))
    print("docs", metadata.get("documents_processed"))
    comparative = metadata.get("comparative_tables") or {}
    print("providers", len(comparative.get("providers") or []))
    print("matrices", len(comparative.get("matrices") or []))
    if comparative.get("providers"):
        first = comparative["providers"][0]
        print(
            "provider0",
            first.get("provider_name"),
            first.get("total_amount"),
            len(first.get("items") or []),
        )

    assert payload.get("executed") is True or metadata.get("executed") is True
    assert metadata.get("comparative_tables"), "debe incluir cuadro comparativo real"
    assert metadata.get("documents_processed"), "debe reportar documentos procesados"
    assert processed_total >= 1, "APQM debe procesar al menos un ítem"
    print("OK processed_total=", processed_total)


if __name__ == "__main__":
    main()
