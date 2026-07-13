"""Pruebas de la API REST oficial — Implementación 9.2."""

from __future__ import annotations

from uuid import uuid4

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from zovrake_motor import __version__
from zovrake_motor.api.bootstrap import build_motor_api_runtime
from zovrake_motor.api.governance import IMPLEMENTATION, NEXT_IMPLEMENTATION
from zovrake_motor.api.http.app import create_app


@pytest.fixture
def client() -> TestClient:
    runtime = build_motor_api_runtime()
    app = create_app(runtime=runtime)
    return TestClient(app)


class TestIntegrationApiRest:
    def test_api_root_returns_uniform_envelope(self, client: TestClient):
        response = client.get("/api/v1")
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["status"] == "ok"
        assert body["contract_version"] == "v1"
        assert body["result"]["motor_version"] == __version__
        assert body["result"]["implementation"] == "9.4"

    def test_create_and_query_analysis(self, client: TestClient):
        payload = {
            "codigo_req": "REQ-REST-001",
            "project_id": "PRJ-REST",
            "quotation_id": "COT-REST",
            "documents": [{"document_id": "doc-rest-001", "document_label": "Cotizacion"}],
            "requirement": {
                "codigo_req": "REQ-REST-001",
                "description": "Prueba REST API",
            },
            "metadata": {"source": "evidence_center"},
        }
        create_response = client.post("/api/v1/analyses", json=payload)
        assert create_response.status_code == 202
        created = create_response.json()
        assert created["success"] is True
        assert created["analysis_id"] is not None
        assert created["status"] == "sent_to_motor"
        analysis_id = created["analysis_id"]

        status_response = client.get(
            f"/api/v1/analyses/{analysis_id}/status",
            params={"project_id": "PRJ-REST"},
        )
        assert status_response.status_code == 200
        status_body = status_response.json()
        assert status_body["analysis_id"] == analysis_id
        assert status_body["contract_version"] == "v1"

        result_response = client.get(
            f"/api/v1/analyses/{analysis_id}/result",
            params={"project_id": "PRJ-REST"},
        )
        assert result_response.status_code == 200
        assert result_response.json()["analysis_id"] == analysis_id

        full_response = client.get(
            f"/api/v1/analyses/{analysis_id}",
            params={"project_id": "PRJ-REST"},
        )
        assert full_response.status_code == 200
        assert full_response.json()["analysis_id"] == analysis_id

    def test_invalid_request_returns_controlled_error(self, client: TestClient):
        response = client.post(
            "/api/v1/analyses",
            json={
                "codigo_req": "",
                "project_id": "PRJ-001",
                "documents": [{"document_id": "doc-001"}],
            },
        )
        assert response.status_code == 422
        body = response.json()
        assert body["success"] is False
        assert body["status"] == "invalid_request"
        assert body["error"]["code"] == "invalid_request"

    def test_health_endpoints(self, client: TestClient):
        motor = client.get("/api/v1/health/motor")
        assert motor.status_code == 200
        assert motor.json()["success"] is True
        assert motor.json()["result"]["motor_ready"] is True

        coordinator = client.get("/api/v1/health/coordinator")
        assert coordinator.status_code == 200
        assert coordinator.json()["success"] is True
        assert coordinator.json()["result"]["coordinator_ready"] is True

    def test_info_endpoints(self, client: TestClient):
        version = client.get("/api/v1/info/version")
        assert version.status_code == 200
        assert version.json()["result"]["motor_version"] == __version__

        service = client.get("/api/v1/info/service")
        assert service.status_code == 200
        assert service.json()["result"]["http_enabled"] is True

        modules = client.get("/api/v1/info/modules")
        assert modules.status_code == 200
        module_list = modules.json()["result"]["modules"]
        assert len(module_list) >= 1
        assert all("module_name" in item for item in module_list)
        assert all("registered" in item for item in module_list)

    def test_governance_declares_rest_implementation(self):
        assert IMPLEMENTATION == "9.4"
        assert NEXT_IMPLEMENTATION is None

    def test_version_reflects_rest_api(self):
        assert __version__ == "9.4.0"
