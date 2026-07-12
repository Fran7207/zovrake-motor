"""Pruebas del certificador integral de plataforma — Implementación 8.11."""

from __future__ import annotations

import json
from pathlib import Path

from zovrake_motor import __version__
from zovrake_motor.certification import EnterpriseIntegrationPlatformCertificationChecker
from zovrake_motor.certification.enums import CertificationArea
from zovrake_motor.enterprise_integration.governance import (
    E2E_CERTIFICATION_STATUS,
    IMPLEMENTATION,
    PLATFORM_CERTIFICATION_STATUS,
    PROMPT_MAESTRO_8_STATUS,
    governance_snapshot,
)

ENTERPRISE_INTEGRATION_ROOT = (
    Path(__file__).resolve().parents[2] / "zovrake_motor" / "enterprise_integration"
)


class TestEnterpriseIntegrationPlatformCertification:
    def test_platform_certification_passes(self):
        checks = EnterpriseIntegrationPlatformCertificationChecker().run()
        failed = [c for c in checks if not c.passed]
        assert not failed, json.dumps([c.to_dict() for c in failed], indent=2)

    def test_all_checks_use_platform_area(self):
        checks = EnterpriseIntegrationPlatformCertificationChecker().run()
        assert all(c.area == CertificationArea.ENTERPRISE_INTEGRATION_PLATFORM for c in checks)

    def test_governance_declares_platform_certified(self):
        snapshot = governance_snapshot()
        assert PROMPT_MAESTRO_8_STATUS == "CLOSED"
        assert IMPLEMENTATION == "8.12"
        assert snapshot["next_implementation"] is None
        assert snapshot["e2e_certification"]["status"] == E2E_CERTIFICATION_STATUS
        assert snapshot["platform_certification"]["status"] == PLATFORM_CERTIFICATION_STATUS
        assert snapshot["platform_certification"]["production_ready"] is True

    def test_documentation_exists_for_8_11(self):
        for filename in ("ARCHITECTURE.md", "CERTIFICATION.md"):
            path = ENTERPRISE_INTEGRATION_ROOT / filename
            assert path.is_file()
            assert "8.12" in path.read_text(encoding="utf-8")

    def test_version_reflects_platform_release(self):
        assert __version__ == "8.12.0"

    def test_minimum_platform_check_count(self):
        checks = EnterpriseIntegrationPlatformCertificationChecker().run()
        assert len(checks) >= 18
