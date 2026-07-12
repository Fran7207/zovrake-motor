"""Pruebas de integración integral — Plataforma de Integración Empresarial (8.11)."""

from __future__ import annotations

from zovrake_motor.certification import (
    EnterpriseIntegrationE2ECertificationChecker,
    EnterpriseIntegrationPlatformCertificationChecker,
)
from zovrake_motor.certification.enterprise_integration_e2e_pipeline import (
    run_full_enterprise_integration_e2e_pipeline,
)
from zovrake_motor.enterprise_integration.governance import governance_snapshot


class TestEnterpriseIntegrationPlatformIntegration:
    def test_e2e_prerequisite_remains_valid(self):
        checks = EnterpriseIntegrationE2ECertificationChecker().run()
        assert all(check.passed for check in checks)

    def test_platform_certification_covers_full_stack(self):
        checks = EnterpriseIntegrationPlatformCertificationChecker().run()
        names = {check.name for check in checks}
        expected = {
            "prior_e2e_certification_valid",
            "complete_flow_integrity",
            "platform_components_unified",
            "official_contract_exclusive",
            "resilience_isolation_and_retry",
            "security_validation_and_audit",
            "observability_metrics_and_traces",
            "performance_consistency",
            "no_circular_dependencies",
            "logical_flow_acyclic",
            "production_readiness_prepared",
        }
        assert expected.issubset(names)

    def test_pipeline_stable_under_platform_certification(self):
        result = run_full_enterprise_integration_e2e_pipeline()
        assert result.passed

    def test_governance_declares_production_ready(self):
        snapshot = governance_snapshot()
        assert snapshot["platform_certification"]["production_ready"] is True
        assert snapshot["status"] == "CLOSED"
        assert snapshot["implementation"] == "8.12"
