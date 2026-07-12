"""
Punto de entrada de certificación End-to-End del Prompt Maestro 8.

Implementación 8.10 — Integración, validación y certificación del Módulo de Integración Empresarial.
"""

from __future__ import annotations

import json
import sys

from zovrake_motor import __version__
from zovrake_motor.certification.enterprise_integration_e2e_checker import (
    EnterpriseIntegrationE2ECertificationChecker,
)
from zovrake_motor.enterprise_integration.governance import governance_snapshot


def main() -> int:
    checks = EnterpriseIntegrationE2ECertificationChecker().run()
    passed = sum(1 for check in checks if check.passed)
    total = len(checks)
    approved = passed == total
    governance = governance_snapshot()

    print("=" * 60)
    print("CERTIFICACIÓN E2E — PROMPT MAESTRO 8")
    print("Módulo de Integración Empresarial — Implementación 8.10")
    print("=" * 60)
    print(f"Versión del Motor: {__version__}")
    print(f"Estado PM8: {governance['status']}")
    print(f"Certificación E2E: {governance['e2e_certification']['status']}")
    print(f"Verificaciones: {passed}/{total} aprobadas")
    print(f"Integración End-to-End: {'APROBADA' if approved else 'RECHAZADA'}")
    print(f"Punto de entrada ERP: {governance['e2e_certification']['official_entry_point']}")
    print("-" * 60)

    if not approved:
        for check in checks:
            if not check.passed:
                print(f"[FALLO] {check.area.value}/{check.name}: {check.message}")

    print(
        json.dumps(
            {
                "motor_version": __version__,
                "implementation": "8.10",
                "prompt_maestro": "8",
                "prompt_maestro_8_status": governance["status"],
                "e2e_certification": governance["e2e_certification"],
                "passed": approved,
                "total_checks": total,
                "passed_checks": passed,
                "governance": governance,
                "checks": [check.to_dict() for check in checks],
            },
            indent=2,
            ensure_ascii=True,
        ),
    )
    return 0 if approved else 1


if __name__ == "__main__":
    sys.exit(main())
