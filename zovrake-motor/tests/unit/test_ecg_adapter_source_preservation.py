"""Prueba de preservación del origen evidence_center en el adaptador ECG."""

from __future__ import annotations

from uuid import uuid4

from zovrake_motor.api.adapters.ecg_adapter import EcgGatewayAdapter
from zovrake_motor.api.models import (
    AnalysisDocumentReference,
    PublicAnalysisRequest,
    RequirementContext,
)
from zovrake_motor.enterprise_integration.service import EnterpriseIntegrationService


class TestEcgAdapterSourcePreservation:
    def test_preserves_evidence_center_source_for_svaf(self):
        service = EnterpriseIntegrationService()
        adapter = EcgGatewayAdapter(service)
        request = PublicAnalysisRequest(
            analysis_id=uuid4(),
            codigo_req="REQ-ERP-001",
            project_id="BT-001",
            quotation_id="BT-001-COT",
            requirement=RequirementContext(codigo_req="REQ-ERP-001", description="contexto"),
            documents=(AnalysisDocumentReference(document_id="doc-1", document_label="Cot"),),
            metadata={"source": "evidence_center", "erp_module": "logistica_cotizaciones"},
        )

        evidence_request = adapter._to_evidence_request(request)
        assert evidence_request.analysis_metadata["source"] == "evidence_center"
        assert evidence_request.analysis_metadata["public_contract_version"] == "v1"
        assert evidence_request.analysis_metadata["integration_channel"] == "integration_api"

    def test_defaults_source_when_missing(self):
        service = EnterpriseIntegrationService()
        adapter = EcgGatewayAdapter(service)
        request = PublicAnalysisRequest(
            analysis_id=uuid4(),
            codigo_req="REQ-ERP-002",
            project_id="BT-002",
            documents=(AnalysisDocumentReference(document_id="doc-2"),),
        )

        evidence_request = adapter._to_evidence_request(request)
        assert evidence_request.analysis_metadata["source"] == "integration_api"
