"""Pruebas del certificador E2E ERP ↔ Motor — Implementación 9.4."""

from __future__ import annotations

import json

from zovrake_motor import __version__
from zovrake_motor.api.governance import IMPLEMENTATION, governance_snapshot
from zovrake_motor.certification.integration_api_e2e_checker import (
    IntegrationApiE2ECertificationChecker,
)
from zovrake_motor.certification.enums import CertificationArea
from zovrake_motor.certification.integration_api_e2e_pipeline import (
    run_erp_motor_integration_e2e_pipeline,
)


class TestIntegrationApiE2ECertification:
    def test_e2e_certification_passes(self):
        checks = IntegrationApiE2ECertificationChecker().run()
        failed = [c for c in checks if not c.passed]
        assert not failed, json.dumps([c.to_dict() for c in failed], indent=2)

    def test_all_checks_use_integration_api_e2e_area(self):
        checks = IntegrationApiE2ECertificationChecker().run()
        assert all(c.area == CertificationArea.INTEGRATION_API_E2E for c in checks)

    def test_pipeline_passes(self):
        result = run_erp_motor_integration_e2e_pipeline()
        assert result.passed, (
            f"submit={result.submit_success}, status={result.status_query_success}, "
            f"result={result.result_query_success}, events={result.event_count}"
        )

    def test_governance_declares_e2e_integration(self):
        snapshot = governance_snapshot()
        assert IMPLEMENTATION == "9.4"
        assert snapshot["pm8_unchanged"] is True
        assert "erp_integration_flow" in snapshot

    def test_version_reflects_e2e_release(self):
        assert __version__ == "9.4.0"
