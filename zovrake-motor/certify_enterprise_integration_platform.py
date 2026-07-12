"""
Punto de entrada de certificación integral del Prompt Maestro 8.

Implementación 8.11 — Certificación integral de la Plataforma de Integración Empresarial.
"""

from __future__ import annotations

import json
import sys

from zovrake_motor import __version__
from zovrake_motor.certification.enterprise_integration_platform_checker import (
    EnterpriseIntegrationPlatformCertificationChecker,
)
from zovrake_motor.enterprise_integration.governance import governance_snapshot


def main() -> int:
    checks = EnterpriseIntegrationPlatformCertificationChecker().run()
    passed = sum(1 for check in checks if check.passed)
    total = len(checks)
    approved = passed == total
    governance = governance_snapshot()

    print("=" * 60)
    print("CERTIFICACION INTEGRAL — PROMPT MAESTRO 8")
    print("Plataforma de Integracion Empresarial — Implementacion 8.11")
    print("=" * 60)
    print(f"Version del Motor: {__version__}")
    print(f"Estado PM8: {governance['status']}")
    print(f"Certificacion de plataforma: {governance['platform_certification']['status']}")
    print(f"Verificaciones: {passed}/{total} aprobadas")
    print(f"Certificacion integral: {'APROBADA' if approved else 'RECHAZADA'}")
    print(f"Punto de entrada ERP: {governance['e2e_certification']['official_entry_point']}")
    print(f"Preparado para produccion: {'SI' if approved else 'NO'}")
    print("-" * 60)

    if not approved:
        for check in checks:
            if not check.passed:
                print(f"[FALLO] {check.area.value}/{check.name}: {check.message}")

    print(
        json.dumps(
            {
                "motor_version": __version__,
                "implementation": "8.11",
                "prompt_maestro": "8",
                "prompt_maestro_8_status": governance["status"],
                "platform_certification": governance["platform_certification"],
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
