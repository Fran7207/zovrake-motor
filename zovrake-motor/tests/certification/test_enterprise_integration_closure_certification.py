"""Pruebas del certificador de cierre — Plataforma de Integracion Empresarial (8.12)."""

from __future__ import annotations

import json
from pathlib import Path

from zovrake_motor import __version__
from zovrake_motor.certification import EnterpriseIntegrationModuleClosureChecker
from zovrake_motor.certification.enums import CertificationArea
from zovrake_motor.enterprise_integration.governance import (
    IMPLEMENTATION,
    INTEGRATION_CONTRACT_NAME,
    INTEGRATION_CONTRACT_VERSION,
    PROMPT_MAESTRO_8_STATUS,
    closure_snapshot,
    frozen_component_names,
)

ENTERPRISE_INTEGRATION_ROOT = (
    Path(__file__).resolve().parents[2] / "zovrake_motor" / "enterprise_integration"
)


class TestEnterpriseIntegrationModuleClosureCertification:
    def test_closure_certification_passes(self):
        checks = EnterpriseIntegrationModuleClosureChecker().run()
        failed = [c for c in checks if not c.passed]
        assert not failed, json.dumps([c.to_dict() for c in failed], indent=2)

    def test_all_checks_use_closure_area(self):
        checks = EnterpriseIntegrationModuleClosureChecker().run()
        assert all(c.area == CertificationArea.ENTERPRISE_INTEGRATION_CLOSURE for c in checks)

    def test_governance_declares_prompt_maestro_8_closed(self):
        snapshot = closure_snapshot()
        assert PROMPT_MAESTRO_8_STATUS == "CLOSED"
        assert IMPLEMENTATION == "8.12"
        assert snapshot["status"] == "CLOSED"
        assert snapshot["next_prompt_maestro"] == "9"
        assert len(snapshot["frozen_components"]) == 17

    def test_frozen_components_match_registry(self):
        from zovrake_motor.enterprise_integration import EnterpriseIntegrationService

        service = EnterpriseIntegrationService()
        service.initialize()
        for name in frozen_component_names():
            component = service.component_registry.get(name)
            assert component is not None
            assert component.is_ready()

    def test_closure_documentation_exists(self):
        for filename in (
            "CLOSURE.md",
            "INTEGRATION_CONTRACT.md",
            "CERTIFICATION.md",
            "ARCHITECTURE.md",
        ):
            assert (ENTERPRISE_INTEGRATION_ROOT / filename).is_file()

    def test_version_reflects_closure_release(self):
        assert __version__ == "9.4.0"

    def test_integration_contract_metadata_complete(self):
        contract = closure_snapshot()["integration_contract"]
        assert contract["name"] == INTEGRATION_CONTRACT_NAME
        assert contract["version"] == INTEGRATION_CONTRACT_VERSION
        assert contract["official_entry_point"] == "Centro de Evidencias — Cotizaciones"
        assert "start_analysis" in contract["required_operations"]

    def test_architecture_freeze_rules_declared(self):
        rules = closure_snapshot()["architecture_freeze_rules"]
        assert len(rules) >= 6
        assert any("contrato" in rule.lower() for rule in rules)
