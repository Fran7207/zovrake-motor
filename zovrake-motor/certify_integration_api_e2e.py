"""
Punto de entrada de certificación E2E ERP ↔ Motor — Prompt Maestro 9.

Implementación 9.4 — Validación integral zovrake-web ↔ zovrake-motor.
"""

from __future__ import annotations

import json
import sys

from zovrake_motor import __version__
from zovrake_motor.api.governance import governance_snapshot
from zovrake_motor.certification.integration_api_e2e_checker import (
    IntegrationApiE2ECertificationChecker,
)


def main() -> int:
    checks = IntegrationApiE2ECertificationChecker().run()
    passed = sum(1 for check in checks if check.passed)
    total = len(checks)
    approved = passed == total
    governance = governance_snapshot()

    print("=" * 60)
    print("CERTIFICACIÓN E2E — PROMPT MAESTRO 9")
    print("Integracion ERP <-> API <-> Motor — Implementacion 9.4")
    print("=" * 60)
    print(f"Versión del Motor: {__version__}")
    print(f"Implementación PM9: {governance['implementation']}")
    print(f"Verificaciones: {passed}/{total} aprobadas")
    print(f"Integracion End-to-End ERP <-> Motor: {'APROBADA' if approved else 'RECHAZADA'}")
    print(f"Punto de entrada ERP: {governance['public_contract']['official_erp_entry_point']}")
    print("-" * 60)

    if not approved:
        for check in checks:
            if not check.passed:
                print(f"[FALLO] {check.area.value}/{check.name}: {check.message}")

    print(
        json.dumps(
            {
                "motor_version": __version__,
                "implementation": "9.4",
                "prompt_maestro": "9",
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
