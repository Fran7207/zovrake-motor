"""Pruebas de la arquitectura de la API de Integración Pública — Implementación 9.1."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from zovrake_motor import IntegrationApiService, __version__
from zovrake_motor.api.enums import IntegrationApiLifecycleStage, PublicContractVersion
from zovrake_motor.api.governance import (
    IMPLEMENTATION,
    NEXT_IMPLEMENTATION,
    PROMPT_MAESTRO_9_STATUS,
    governance_snapshot,
)
from zovrake_motor.api.models import (
    AnalysisDocumentReference,
    PublicAnalysisRequest,
    PublicResultQuery,
    PublicStatusQuery,
    RequirementContext,
)
from zovrake_motor.config import ConfigCategory, ConfigurationProvider

API_ROOT = Path(__file__).resolve().parents[2] / "zovrake_motor" / "api"


class TestIntegrationApiArchitecture:
    def test_service_initializes(self):
        service = IntegrationApiService()
        service.initialize()
        assert service.is_available()
        snapshot = service.snapshot()
        assert snapshot["http_transport_prepared"] is True
        assert snapshot["public_contract_version"] == "v1"

    def test_public_contract_start_analysis_flow(self):
        service = IntegrationApiService()
        analysis_id = uuid4()
        request = PublicAnalysisRequest(
            analysis_id=analysis_id,
            codigo_req="REQ-API-001",
            project_id="PRJ-001",
            quotation_id="COT-001",
            requirement=RequirementContext(
                codigo_req="REQ-API-001",
                description="Requerimiento de arquitectura API",
            ),
            documents=(
                AnalysisDocumentReference(
                    document_id="doc-001",
                    document_label="Cotizacion proveedor",
                ),
            ),
            metadata={"source": "evidence_center"},
        )

        response = service.start_analysis(request)
        assert response.success is True
        assert response.analysis_id == analysis_id
        assert response.contract_version == PublicContractVersion.V1.value
        assert response.status.stage == IntegrationApiLifecycleStage.SENT_TO_MOTOR

        service.process_pending()
        status = service.query_status(PublicStatusQuery(analysis_id=analysis_id, project_id="PRJ-001"))
        assert status.analysis_id == analysis_id

        result = service.query_result(PublicResultQuery(analysis_id=analysis_id, project_id="PRJ-001"))
        assert result.analysis_id == analysis_id
        assert len(service.events_for_analysis(analysis_id)) >= 1

    def test_incomplete_request_returns_controlled_error(self):
        service = IntegrationApiService()
        response = service.start_analysis(
            PublicAnalysisRequest(
                analysis_id=uuid4(),
                codigo_req="",
                project_id="PRJ-001",
                documents=(AnalysisDocumentReference(document_id="doc-001"),),
            ),
        )
        assert response.success is False
        assert response.error is not None
        assert response.error.error_code.value == "incomplete_request"

    def test_governance_declares_pm9_open(self):
        snapshot = governance_snapshot()
        assert PROMPT_MAESTRO_9_STATUS == "OPEN"
        assert IMPLEMENTATION == "9.4"
        assert NEXT_IMPLEMENTATION is None
        assert snapshot["public_contract"]["version"] == "v1"
        assert snapshot["pm8_unchanged"] is True
        assert "API de Integracion" in snapshot["official_integration_flow"]

    def test_documentation_exists(self):
        for filename in ("ARCHITECTURE.md", "CONTRACT.md", "LIFECYCLE.md", "CERTIFICATION.md"):
            assert (API_ROOT / filename).is_file()

    def test_configuration_category_available(self):
        provider = ConfigurationProvider.default()
        assert ConfigCategory.INTEGRATION_API.value == "integration_api"
        settings = provider.integration_api()
        assert settings.prepared is True
        assert settings.http_enabled is True
        assert settings.http_transport_prepared is True

    def test_version_reflects_pm9_architecture(self):
        assert __version__ == "9.4.0"

    def test_api_does_not_import_motor_internals(self):
        forbidden = (
            "zovrake_motor.intelligent_analysis",
            "zovrake_motor.comprehension",
            "zovrake_motor.classification",
            "zovrake_motor.comparative_tables",
        )
        for path in API_ROOT.rglob("*.py"):
            content = path.read_text(encoding="utf-8")
            for name in forbidden:
                assert name not in content, f"{name} en {path.name}"
