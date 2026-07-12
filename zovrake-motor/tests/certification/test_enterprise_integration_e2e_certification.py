"""Pruebas del certificador E2E — Módulo de Integración Empresarial (8.10/8.11)."""

from __future__ import annotations

import json
from pathlib import Path

from zovrake_motor import __version__
from zovrake_motor.certification import EnterpriseIntegrationE2ECertificationChecker
from zovrake_motor.certification.enums import CertificationArea
from zovrake_motor.enterprise_integration.governance import (
    E2E_CERTIFICATION_STATUS,
    E2E_IMPLEMENTATION,
    IMPLEMENTATION,
    PROMPT_MAESTRO_8_STATUS,
    governance_snapshot,
)

ENTERPRISE_INTEGRATION_ROOT = (
    Path(__file__).resolve().parents[2] / "zovrake_motor" / "enterprise_integration"
)


class TestEnterpriseIntegrationE2ECertification:
    def test_e2e_certification_passes(self):
        checks = EnterpriseIntegrationE2ECertificationChecker().run()
        failed = [c for c in checks if not c.passed]
        assert not failed, json.dumps([c.to_dict() for c in failed], indent=2)

    def test_all_checks_use_e2e_area(self):
        checks = EnterpriseIntegrationE2ECertificationChecker().run()
        assert all(c.area == CertificationArea.ENTERPRISE_INTEGRATION_E2E for c in checks)

    def test_governance_declares_e2e_integration(self):
        snapshot = governance_snapshot()
        assert PROMPT_MAESTRO_8_STATUS == "CLOSED"
        assert IMPLEMENTATION == "8.12"
        assert E2E_IMPLEMENTATION == "8.10"
        assert snapshot["next_implementation"] is None
        assert snapshot["e2e_certification"]["status"] == E2E_CERTIFICATION_STATUS
        assert snapshot["prepared_functional_components_count"] == 17

    def test_documentation_exists(self):
        for filename in ("ARCHITECTURE.md", "CERTIFICATION.md"):
            assert (ENTERPRISE_INTEGRATION_ROOT / filename).is_file()

    def test_version_reflects_e2e_release(self):
        assert __version__ == "8.12.0"

    def test_architectural_boundaries_include_full_flow(self):
        boundaries = governance_snapshot()["architectural_boundaries"]
        integration = next(item for item in boundaries if item.get("module") == "enterprise_integration")
        assert "Coordinator" in integration["flow"]
        assert "ECG" in integration["flow"]
