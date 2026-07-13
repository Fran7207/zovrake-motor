"""
Certificador End-to-End ERP ↔ API REST ↔ Motor Inteligente.

Implementación 9.4 — Validación integral de integración zovrake-web ↔ zovrake-motor.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from uuid import uuid4

from zovrake_motor import __version__
from zovrake_motor.api.governance import ERP_INTEGRATION_FLOW, governance_snapshot
from zovrake_motor.api.bootstrap import build_motor_api_runtime
from zovrake_motor.api.http.app import create_app
from zovrake_motor.certification.enums import CertificationArea, CertificationStatus
from zovrake_motor.certification.integration_api_e2e_pipeline import (
    build_erp_evidence_center_payload,
    run_erp_motor_integration_e2e_pipeline,
)
from zovrake_motor.certification.models import CertificationCheck

API_ROOT = Path(__file__).resolve().parent.parent / "api"
ERP_SCRIPT = Path(__file__).resolve().parents[2].parent / "zovrake-web" / "script.js"

FORBIDDEN_API_HTTP_IMPORTS = (
    "zovrake_motor.intelligent_analysis",
    "zovrake_motor.comprehension",
    "zovrake_motor.classification",
    "zovrake_motor.comparative_tables",
)


class IntegrationApiE2ECertificationChecker:
    """Certifica la integración operativa ERP ↔ API ↔ Motor."""

    IMPLEMENTATION = "9.4"

    def run(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        checks.extend(self._check_documentation())
        checks.extend(self._check_governance())
        checks.extend(self._check_erp_client_prepared())
        checks.extend(self._check_full_e2e_flow())
        checks.extend(self._check_api_health_and_coordinator())
        checks.extend(self._check_uniform_contract())
        checks.extend(self._check_robustness())
        checks.extend(self._check_consistency_and_concurrency())
        checks.extend(self._check_architectural_isolation())
        return checks

    def _check_documentation(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.INTEGRATION_API_E2E
        for filename in ("ARCHITECTURE.md", "CONTRACT.md", "LIFECYCLE.md", "CERTIFICATION.md"):
            path = API_ROOT / filename
            if path.is_file():
                checks.append(self._passed(area, f"doc_{filename.lower()}", f"Documentación {filename} presente"))
            else:
                checks.append(self._failed(area, f"doc_{filename.lower()}", f"Falta {filename}"))
        return checks

    def _check_governance(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.INTEGRATION_API_E2E
        try:
            snapshot = governance_snapshot()
            assert snapshot["implementation"] == "9.4"
            assert snapshot["pm8_unchanged"] is True
            assert snapshot["motor_internals_unchanged"] is True
            assert "ZovrakeMotorIntegration" in " ".join(ERP_INTEGRATION_FLOW)
            checks.append(self._passed(area, "governance_pm9_e2e", "Gobierno PM9.4 declarado"))
        except Exception as exc:
            checks.append(self._failed(area, "governance_pm9_e2e", str(exc)))
        return checks

    def _check_erp_client_prepared(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.INTEGRATION_API_E2E
        try:
            assert ERP_SCRIPT.is_file(), "script.js no encontrado"
            content = ERP_SCRIPT.read_text(encoding="utf-8")
            required = (
                "ZovrakeMotorIntegration",
                "construirSolicitudAnalisis",
                "pollUntilComplete",
                "source: \"evidence_center\"",
                "analizarCotizaciones",
                "cuadroComparativoHTML",
            )
            for token in required:
                assert token in content, f"Falta {token} en script.js"
            checks.append(
                self._passed(
                    area,
                    "erp_client_integration",
                    "Cliente ERP ZovrakeMotorIntegration preparado en script.js",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "erp_client_integration", str(exc)))
        return checks

    def _check_full_e2e_flow(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.INTEGRATION_API_E2E
        try:
            result = run_erp_motor_integration_e2e_pipeline()
            assert result.passed, (
                f"Flujo E2E incompleto: submit={result.submit_success}, "
                f"queue={result.queue_processed}, transitions={result.pipeline_transitions}, "
                f"status={result.status_query_success}, result={result.result_query_success}"
            )
            checks.append(
                self._passed(
                    area,
                    "full_e2e_flow",
                    "Flujo Centro de Evidencias → API → Coordinator → Motor → ERP certificado",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "full_e2e_flow", str(exc)))
        return checks

    def _check_api_health_and_coordinator(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.INTEGRATION_API_E2E
        try:
            from fastapi.testclient import TestClient

            runtime = build_motor_api_runtime()
            client = TestClient(create_app(runtime=runtime))
            motor = client.get("/api/v1/health/motor").json()
            coordinator = client.get("/api/v1/health/coordinator").json()
            assert motor["success"] is True
            assert coordinator["success"] is True
            assert coordinator["result"]["coordinator_ready"] is True
            checks.append(self._passed(area, "api_and_coordinator_health", "API y Coordinator operativos"))
        except Exception as exc:
            checks.append(self._failed(area, "api_and_coordinator_health", str(exc)))
        return checks

    def _check_uniform_contract(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.INTEGRATION_API_E2E
        try:
            from fastapi.testclient import TestClient

            runtime = build_motor_api_runtime()
            client = TestClient(create_app(runtime=runtime))
            payload = build_erp_evidence_center_payload()
            response = client.post("/api/v1/analyses", json=payload)
            body = response.json()
            for field in ("analysis_id", "status", "timestamp", "message", "success", "contract_version"):
                assert field in body, f"Campo ausente: {field}"
            assert body["contract_version"] == "v1"
            checks.append(self._passed(area, "uniform_response_contract", "Sobre uniforme ApiResponseEnvelope respetado"))
        except Exception as exc:
            checks.append(self._failed(area, "uniform_response_contract", str(exc)))
        return checks

    def _check_robustness(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.INTEGRATION_API_E2E
        try:
            from fastapi.testclient import TestClient

            runtime = build_motor_api_runtime()
            client = TestClient(create_app(runtime=runtime))

            incomplete = client.post(
                "/api/v1/analyses",
                json={
                    "codigo_req": "",
                    "project_id": "PRJ-001",
                    "documents": [{"document_id": "doc-001"}],
                },
            )
            assert incomplete.status_code == 422
            assert incomplete.json()["success"] is False

            no_docs = client.post(
                "/api/v1/analyses",
                json={
                    "codigo_req": "REQ-001",
                    "project_id": "PRJ-001",
                    "documents": [],
                },
            )
            assert no_docs.status_code == 422

            invalid_doc = client.post(
                "/api/v1/analyses",
                json={
                    "codigo_req": "REQ-001",
                    "project_id": "PRJ-001",
                    "documents": [{"document_id": ""}],
                },
            )
            assert invalid_doc.status_code == 422

            checks.append(
                self._passed(
                    area,
                    "controlled_error_handling",
                    "Solicitudes inválidas devuelven errores controlados sin afectar el servicio",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "controlled_error_handling", str(exc)))
        return checks

    def _check_consistency_and_concurrency(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.INTEGRATION_API_E2E
        try:
            from fastapi.testclient import TestClient

            runtime = build_motor_api_runtime()
            client = TestClient(create_app(runtime=runtime))

            ids: set[str] = set()

            def submit_one(index: int) -> str:
                payload = build_erp_evidence_center_payload(
                    analysis_id=uuid4(),
                    codigo_req=f"REQ-CONC-{index}",
                    project_id=f"PRJ-CONC-{index}",
                )
                response = client.post("/api/v1/analyses", json=payload)
                body = response.json()
                assert response.status_code == 202
                assert body["success"] is True
                return str(body["analysis_id"])

            with ThreadPoolExecutor(max_workers=4) as pool:
                futures = [pool.submit(submit_one, i) for i in range(4)]
                for future in as_completed(futures):
                    ids.add(future.result())

            assert len(ids) == 4
            runtime.integration_api.process_pending()
            checks.append(
                self._passed(
                    area,
                    "unique_concurrent_analyses",
                    "Análisis concurrentes con identificadores únicos aceptados",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "unique_concurrent_analyses", str(exc)))
        return checks

    def _check_architectural_isolation(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        area = CertificationArea.INTEGRATION_API_E2E
        try:
            http_root = API_ROOT / "http"
            for path in http_root.rglob("*.py"):
                content = path.read_text(encoding="utf-8")
                for forbidden in FORBIDDEN_API_HTTP_IMPORTS:
                    assert forbidden not in content, f"{forbidden} importado en {path.name}"
            checks.append(
                self._passed(
                    area,
                    "api_http_isolation",
                    "Capa HTTP no importa módulos inteligentes internos",
                ),
            )
        except Exception as exc:
            checks.append(self._failed(area, "api_http_isolation", str(exc)))
        return checks

    @staticmethod
    def _passed(area: CertificationArea, name: str, message: str) -> CertificationCheck:
        return CertificationCheck(
            area=area,
            name=name,
            status=CertificationStatus.PASSED,
            message=message,
        )

    @staticmethod
    def _failed(area: CertificationArea, name: str, message: str) -> CertificationCheck:
        return CertificationCheck(
            area=area,
            name=name,
            status=CertificationStatus.FAILED,
            message=message,
        )
