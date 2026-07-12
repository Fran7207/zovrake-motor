"""Pruebas de cierre formal del Prompt Maestro 8 — Implementacion 8.12."""

from __future__ import annotations

import json

from zovrake_motor import __version__
from zovrake_motor.certification import CoreCertificationChecker, EnterpriseIntegrationModuleClosureChecker
from zovrake_motor.certification.enums import CertificationArea
from zovrake_motor.enterprise_integration.governance import (
    PROMPT_MAESTRO_8_STATUS,
    closure_snapshot,
    frozen_component_names,
)


class TestEnterpriseIntegrationModuleClosure:
    def test_closure_certification_passes(self):
        checks = EnterpriseIntegrationModuleClosureChecker().run()
        failed = [c for c in checks if not c.passed]
        assert not failed, json.dumps([c.to_dict() for c in failed], indent=2)

    def test_core_certification_declares_pm8_closed(self):
        report = CoreCertificationChecker().run()
        assert CertificationArea.ENTERPRISE_INTEGRATION_CLOSURE in {c.area for c in report.checks}
        assert report.prompt_maestro_8_closed

    def test_governance_declares_prompt_maestro_8_closed(self):
        snapshot = closure_snapshot()
        assert snapshot["status"] == PROMPT_MAESTRO_8_STATUS
        assert snapshot["prompt_maestro"] == "8"
        assert snapshot["next_prompt_maestro"] == "9"
        assert len(snapshot["frozen_components"]) == 17

    def test_frozen_components_count(self):
        assert len(frozen_component_names()) == 17

    def test_version_reflects_closure_release(self):
        assert __version__ == "8.12.0"

    def test_official_flow_declared(self):
        flow = closure_snapshot()["official_integration_flow"]
        assert flow[0] == "Usuario"
        assert "Centro de Evidencias" in flow
        assert "Motor Inteligente" in flow
